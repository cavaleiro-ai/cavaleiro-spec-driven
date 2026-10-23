"""``SPECIFY_UPGRADE_REPOSITORY`` selects where self check/upgrade look.

Without it, ``specify self upgrade`` on an install made from a fork resolves
upstream's latest release and reinstalls from upstream, silently replacing the
fork. The override is opt-in: when it is unset every URL stays upstream's.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
import typer

from specify_cli import app
from specify_cli._version import (
    GITHUB_API_LATEST,
    _InstallMethod,
    _UpgradePlan,
    _latest_release_api_url,
    _manual_source_spec,
    _rollback_hint,
    _source_spec,
)
from tests.conftest import strip_ansi
from tests.http_helpers import (
    mock_urlopen_response,
    route_opener_open_through_urlopen,  # noqa: F401 (autouse fixture)
)
from typer.testing import CliRunner

FORK = "cavaleiro-ai/cavaleiro-spec-driven"


def _plan(snapshot: str, method: _InstallMethod) -> _UpgradePlan:
    return _UpgradePlan(
        method=method,
        current_version=snapshot,
        target_tag="v1.1.0",
        installer_argv=[],
        preview_summary="",
        pre_upgrade_snapshot=snapshot,
    )


def test_default_source_is_unchanged(monkeypatch):
    monkeypatch.delenv("SPECIFY_UPGRADE_REPOSITORY", raising=False)

    assert _latest_release_api_url() == GITHUB_API_LATEST
    assert _source_spec("v1.2.3") == "git+https://github.com/github/spec-kit.git@v1.2.3"
    assert _manual_source_spec(None) == "git+https://github.com/github/spec-kit.git@vX.Y.Z"


def test_override_redirects_release_lookup_install_and_rollback(monkeypatch):
    monkeypatch.setenv("SPECIFY_UPGRADE_REPOSITORY", FORK)

    assert _latest_release_api_url() == (
        f"https://api.github.com/repos/{FORK}/releases/latest"
    )
    assert _source_spec("v1.0.0") == f"git+https://github.com/{FORK}.git@v1.0.0"
    assert _source_spec(None) == f"git+https://github.com/{FORK}.git"
    hint = _rollback_hint(_plan("1.0.0", _InstallMethod.UV_TOOL))
    assert f"--from git+https://github.com/{FORK}.git@v1.0.0" in hint
    assert f"https://github.com/{FORK}/releases" in _rollback_hint(
        _plan("unknown", _InstallMethod.PIPX)
    )


@pytest.mark.parametrize(
    "value",
    [
        "../evil",
        "owner",
        "owner/repo/extra",
        "https://github.com/owner/repo",
        "owner/repo.git",
        "owner/..",
        "-owner/repo",
        "owner/re po",
    ],
)
def test_override_must_be_an_owner_repo_slug(monkeypatch, value):
    monkeypatch.setenv("SPECIFY_UPGRADE_REPOSITORY", value)

    with pytest.raises(typer.BadParameter, match="owner/repo"):
        _latest_release_api_url()


def test_self_check_queries_and_recommends_the_override(monkeypatch):
    monkeypatch.setenv("SPECIFY_UPGRADE_REPOSITORY", FORK)
    with patch(
        "specify_cli._version._get_installed_version", return_value="0.9.0"
    ), patch(
        "specify_cli.authentication.http.urllib.request.urlopen",
        return_value=mock_urlopen_response({"tag_name": "v1.0.0"}),
    ) as urlopen:
        result = CliRunner().invoke(app, ["self", "check"])

    output = strip_ansi(result.output)
    assert result.exit_code == 0, output
    request = urlopen.call_args.args[0]
    requested_url = getattr(request, "full_url", request)
    assert requested_url == f"https://api.github.com/repos/{FORK}/releases/latest"
    assert f"git+https://github.com/{FORK}.git@v1.0.0" in output
    assert "github/spec-kit.git" not in output
