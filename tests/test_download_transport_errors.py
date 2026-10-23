"""Transport failures while a download body streams must become clean errors.

``urlopen`` returning only means the status line and headers arrived. A
connection dropped while the body is read raises ``http.client.IncompleteRead``
(an ``HTTPException``), ``ConnectionResetError`` or ``TimeoutError`` -- none of
them a ``urllib.error.URLError`` -- so handlers that caught only ``URLError``
let them escape as raw tracebacks from ``extension add --from``,
``preset add --from``, catalog downloads, and catalog searches.
"""

from __future__ import annotations

import http.client
from pathlib import Path
from unittest.mock import patch

import pytest
import typer
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.extensions import (
    CatalogEntry,
    ExtensionCatalog,
    ExtensionError,
    ExtensionManager,
)
from specify_cli.integrations import (
    IntegrationCatalog,
    IntegrationCatalogEntry,
    IntegrationCatalogError,
)
from specify_cli.presets import PresetCatalog, PresetError, PresetManager
from tests.conftest import strip_ansi
from tests.specify_cli.extensions._helpers import (
    validate_safe_cache_dir as _validate_safe_cache_dir_test_stand_in,
)

TRANSPORT_FAILURES = [
    pytest.param(
        lambda: http.client.IncompleteRead(b"partial", 100), id="incomplete-read"
    ),
    pytest.param(
        lambda: ConnectionResetError(10054, "connection reset by peer"),
        id="connection-reset",
    ),
    pytest.param(lambda: TimeoutError("timed out"), id="timeout"),
]


class _FailingBodyResponse:
    """A response whose headers arrived but whose body read fails."""

    def __init__(self, error: BaseException, url: str):
        self._error = error
        self._url = url

    def read(self, _size: int = -1) -> bytes:
        raise self._error

    def geturl(self) -> str:
        return self._url

    def getheader(self, _name: str, default=None):
        return default

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        return False


class _UndecodableBodyResponse(_FailingBodyResponse):
    def __init__(self, url: str):
        super().__init__(AssertionError("unused"), url)
        self._data = b'{"schema_version": "1.0", "name": "caf\xe9"}'

    def read(self, size: int = -1) -> bytes:
        data, self._data = self._data, b""
        return data


def _project(tmp_path: Path) -> Path:
    project_dir = tmp_path / "project"
    (project_dir / ".specify").mkdir(parents=True)
    return project_dir


@pytest.mark.parametrize("make_error", TRANSPORT_FAILURES)
def test_extension_add_from_url_reports_body_transport_failure(tmp_path, make_error):
    project_dir = _project(tmp_path)
    url = "https://example.com/ext.zip"

    with patch.object(Path, "cwd", return_value=project_dir), \
         patch("typer.confirm", return_value=True), \
         patch(
             "specify_cli.extensions._commands._validate_safe_cache_dir",
             side_effect=_validate_safe_cache_dir_test_stand_in,
         ), \
         patch(
             "specify_cli.authentication.http.open_url",
             return_value=_FailingBodyResponse(make_error(), url),
         ), \
         patch.object(ExtensionManager, "install_from_zip") as install:
        result = CliRunner().invoke(
            app, ["extension", "add", "my-ext", "--from", url], catch_exceptions=True
        )

    assert result.exit_code == 1, result.output
    assert isinstance(result.exception, SystemExit), result.exception
    assert "Failed to download from" in " ".join(strip_ansi(result.output).split())
    install.assert_not_called()


@pytest.mark.parametrize("make_error", TRANSPORT_FAILURES)
def test_preset_add_from_url_reports_body_transport_failure(
    tmp_path, monkeypatch, capsys, make_error
):
    from specify_cli.presets import _commands as preset_commands

    project_dir = _project(tmp_path)
    url = "https://example.com/preset.zip"
    monkeypatch.setattr("specify_cli._require_specify_project", lambda: project_dir)
    monkeypatch.setattr("specify_cli.get_speckit_version", lambda: "0.6.0")
    monkeypatch.setattr(
        "specify_cli.authentication.http.open_url",
        lambda *_args, **_kwargs: _FailingBodyResponse(make_error(), url),
    )
    monkeypatch.setattr(
        PresetManager,
        "install_from_zip",
        lambda *_args, **_kwargs: pytest.fail("must not install"),
    )

    with pytest.raises(typer.Exit) as exc_info:
        preset_commands.preset_add(
            preset_id=None, from_url=url, dev=None, priority=10
        )

    assert exc_info.value.exit_code == 1
    assert "Failed to download" in " ".join(strip_ansi(capsys.readouterr().out).split())


@pytest.mark.parametrize("make_error", TRANSPORT_FAILURES)
def test_extension_catalog_fetch_reports_body_transport_failure(tmp_path, make_error):
    catalog = ExtensionCatalog(_project(tmp_path))
    url = "https://example.com/catalog.json"
    entry = CatalogEntry(url=url, name="c", priority=1, install_allowed=True)

    with patch.object(
        catalog, "_open_url", return_value=_FailingBodyResponse(make_error(), url)
    ):
        with pytest.raises(ExtensionError, match="Failed to fetch catalog"):
            catalog._fetch_single_catalog(entry, force_refresh=True)


def test_extension_catalog_fetch_reports_non_utf8_body(tmp_path):
    catalog = ExtensionCatalog(_project(tmp_path))
    url = "https://example.com/catalog.json"
    entry = CatalogEntry(url=url, name="c", priority=1, install_allowed=True)

    with patch.object(catalog, "_open_url", return_value=_UndecodableBodyResponse(url)):
        with pytest.raises(ExtensionError, match="not valid UTF-8"):
            catalog._fetch_single_catalog(entry, force_refresh=True)


@pytest.mark.parametrize("make_error", TRANSPORT_FAILURES)
def test_extension_catalog_download_reports_body_transport_failure(
    tmp_path, make_error
):
    catalog = ExtensionCatalog(_project(tmp_path))
    url = "https://example.com/ext.zip"
    ext_info = {"id": "my-ext", "version": "1.0.0", "download_url": url}

    with patch.object(
        catalog, "_open_url", return_value=_FailingBodyResponse(make_error(), url)
    ):
        with pytest.raises(ExtensionError, match="Failed to download extension"):
            catalog.download_extension_info(ext_info, tmp_path / "downloads")


@pytest.mark.parametrize("make_error", TRANSPORT_FAILURES)
def test_preset_catalog_download_reports_body_transport_failure(
    tmp_path, make_error
):
    catalog = PresetCatalog(_project(tmp_path))
    url = "https://example.com/preset.zip"
    pack_info = {"id": "my-preset", "version": "1.0.0", "download_url": url}

    with patch.object(
        catalog, "_open_url", return_value=_FailingBodyResponse(make_error(), url)
    ):
        with pytest.raises(PresetError, match="Failed to download preset"):
            catalog.download_pack_info(pack_info, tmp_path / "downloads")


@pytest.mark.parametrize("make_error", TRANSPORT_FAILURES)
def test_integration_catalog_fetch_reports_body_transport_failure(
    tmp_path, make_error
):
    catalog = IntegrationCatalog(_project(tmp_path))
    url = "https://example.com/integrations.json"
    entry = IntegrationCatalogEntry(url, "c", 1, True)

    with patch(
        "specify_cli.authentication.http.open_url",
        return_value=_FailingBodyResponse(make_error(), url),
    ):
        with pytest.raises(IntegrationCatalogError, match="Failed to fetch catalog"):
            catalog._fetch_single_catalog(entry, force_refresh=True)
