"""Tests for the ``specify init`` command adapter.

`command_init.py` interpolated the project name, `--integration`/`--script`
values and paths straight into Rich markup f-strings. A name containing a
tag-shaped bracket run was therefore consumed as markup:

* ``specify init "proj [v2]"`` succeeded and created the directory, but the
  Next Steps panel printed ``cd proj`` -- a command that fails when pasted.
* ``specify init "app[/red]x"`` created the directory and then died with
  ``MarkupError``, so the user saw a traceback for a project that had in fact
  been scaffolded.

Every sibling CLI module (extensions, presets, workflows, integrations) already
escapes user-controlled display values; init.py was the outlier.
"""

from __future__ import annotations

import importlib
import os
import re
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from specify_cli import app
from specify_cli.command_init import _shell_quote_arg
from tests.conftest import requires_bash

_ANSI = re.compile(r"\x1b\[[0-9;]*m")


def test_command_init_importable():
    mod = importlib.import_module("specify_cli.command_init")
    assert hasattr(mod, "register")
    assert callable(mod.register)


def test_transitional_commands_package_removed():
    import specify_cli

    package_root = Path(specify_cli.__file__).parent
    assert not (package_root / "commands" / "__init__.py").exists()
    assert not (package_root / "commands" / "init.py").exists()


def test_init_command_registered():
    callback_names = [
        cmd.callback.__name__ for cmd in app.registered_commands if cmd.callback
    ]
    assert callback_names == ["init", "check", "version", "mcp"]


def test_init_has_win32_guard():
    """init.py must assign _transient from platform check and pass it to Live."""
    import specify_cli

    init_src = Path(specify_cli.__file__).parent / "command_init.py"
    content = init_src.read_text(encoding="utf-8")
    guard = (
        r"_transient\s*=\s*sys\.platform\s*!=\s*['\"]win32['\"].*"
        r"Live\(.*transient\s*=\s*_transient"
    )
    assert re.search(guard, content, re.DOTALL)


def _strip(text: str) -> str:
    return _ANSI.sub("", text or "")


def _init(tmp_path: Path, name: str):
    """Run a fully offline, non-interactive `specify init <name>`."""
    previous = os.getcwd()
    os.chdir(tmp_path)
    try:
        return CliRunner().invoke(
            app,
            [
                "init",
                name,
                "--integration",
                "generic",
                "--integration-options",
                "--commands-dir .agent/commands",
                "--ignore-agent-tools",
                "--offline",
            ],
            catch_exceptions=True,
        )
    finally:
        os.chdir(previous)


@pytest.mark.parametrize("name", ["proj [v2]", "my[bold]app"])
def test_next_steps_cd_shows_the_real_project_name(tmp_path: Path, name: str):
    """The `cd` line must name the directory that was actually created."""
    result = _init(tmp_path, name)
    assert result.exit_code == 0, _strip(result.stdout)
    assert (tmp_path / name).is_dir()

    out = _strip(result.stdout)
    cd_lines = [line for line in out.splitlines() if "cd " in line]
    assert cd_lines, out
    assert f"cd {_shell_quote_arg(name)}" in " ".join(cd_lines), cd_lines


def test_closing_tag_in_project_name_does_not_crash(tmp_path: Path):
    """A name forming a closing tag raised MarkupError *after* the project had
    been created, so init reported failure for work it had completed."""
    name = "app[/red]x"
    result = _init(tmp_path, name)

    assert result.exception is None or not isinstance(
        result.exception, Exception
    ) or "MarkupError" not in type(result.exception).__name__, (
        f"unexpected {type(result.exception).__name__}: {result.exception}"
    )
    assert result.exit_code == 0, _strip(result.stdout)
    assert (tmp_path / name).is_dir()
    assert f"cd {_shell_quote_arg(name)}" in _strip(result.stdout)


def test_invalid_integration_value_is_rendered_literally(tmp_path: Path):
    """An invalid `--integration` value is echoed back; it must not be parsed as
    markup (nor raise) when it contains a bracket run."""
    previous = os.getcwd()
    os.chdir(tmp_path)
    try:
        result = CliRunner().invoke(
            app,
            ["init", "proj", "--integration", "nope[/red]", "--ignore-agent-tools"],
            catch_exceptions=True,
        )
    finally:
        os.chdir(previous)

    assert result.exit_code != 0
    assert "nope[/red]" in _strip(result.stdout)


def _cd_argument(stdout: str) -> str:
    """Return the argument of the printed `cd` command, verbatim.

    The line is rendered inside a Rich panel, so the trailing box-drawing
    border and its padding are stripped before the argument is compared.
    """
    marker = "Go to the project folder: cd "
    for line in _strip(stdout).splitlines():
        if marker in line:
            return line.split(marker, 1)[1].rstrip().rstrip("│").rstrip()
    raise AssertionError(f"no cd line in output:\n{stdout}")


@pytest.mark.parametrize("name", ["proj v2", "my project"])
def test_cd_line_quotes_a_name_containing_whitespace(tmp_path: Path, name: str):
    """Rich-escaping alone left `cd proj v2`, which every shell reads as two
    arguments, so the copy-pasted command did not enter the directory."""
    result = _init(tmp_path, name)
    assert result.exit_code == 0, _strip(result.stdout)
    assert (tmp_path / name).is_dir()

    printed = _cd_argument(result.stdout)
    assert printed != name, "a whitespace-bearing name must be quoted"
    assert name in printed, printed
    assert printed == _shell_quote_arg(name)


def test_ordinary_name_is_not_quoted(tmp_path: Path):
    """The common case must stay byte-identical: no gratuitous quoting."""
    result = _init(tmp_path, "my-project")
    assert result.exit_code == 0, _strip(result.stdout)
    assert _cd_argument(result.stdout) == "my-project"


@requires_bash
@pytest.mark.parametrize("name", ["proj v2", "proj [v2]", "my-project"])
def test_printed_cd_command_actually_changes_directory(tmp_path: Path, name: str):
    """Execute the printed command rather than only inspecting it.

    This is the assertion the string comparisons cannot make: the rendered
    `cd <arg>` is fed to a real shell and must land in the created directory.
    """
    result = _init(tmp_path, name)
    assert result.exit_code == 0, _strip(result.stdout)
    target = tmp_path / name
    assert target.is_dir()

    printed = _cd_argument(result.stdout)
    proc = subprocess.run(
        ["bash", "-c", f"cd {printed} && pwd"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, f"cd {printed!r} failed: {proc.stderr}"
    assert Path(proc.stdout.strip()).name == name, proc.stdout


def _init_args(name: str, *extra: str) -> list[str]:
    return [
        "init",
        name,
        "--integration",
        "generic",
        "--ignore-agent-tools",
        "--offline",
        *extra,
    ]


def _invoke_in(tmp_path: Path, args: list[str]):
    previous = os.getcwd()
    os.chdir(tmp_path)
    try:
        return CliRunner().invoke(app, args, catch_exceptions=True)
    finally:
        os.chdir(previous)


def test_rejected_integration_options_leave_no_directory(tmp_path: Path):
    """Options were parsed only after the project root was created, so a typo
    left an empty directory behind and the retry then failed with
    "Directory already exists ... Use --force"."""
    result = _invoke_in(
        tmp_path, _init_args("proj", "--integration-options", "--bogus")
    )
    assert result.exit_code == 1, _strip(result.stdout)
    assert "Unknown integration option" in _strip(result.stdout)
    assert not (tmp_path / "proj").exists()

    retry = _invoke_in(
        tmp_path,
        _init_args("proj", "--integration-options", "--commands-dir .agent/commands"),
    )
    assert retry.exit_code == 0, _strip(retry.stdout)


@pytest.mark.parametrize(
    "error",
    [OSError("disk full"), KeyboardInterrupt()],
    ids=["shared-infra-oserror", "ctrl-c"],
)
def test_aborted_init_removes_the_directory_it_created(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, error: BaseException
):
    """Cleanup ran only for ordinary exceptions; typer.Exit from a failing step
    and Ctrl-C skipped it and left a half-scaffolded project behind."""
    import specify_cli

    def _fail(*_args, **_kwargs):
        raise error

    monkeypatch.setattr(specify_cli, "_install_shared_infra", _fail)
    result = _invoke_in(
        tmp_path,
        _init_args("proj", "--integration-options", "--commands-dir .agent/commands"),
    )

    assert result.exit_code != 0
    assert not (tmp_path / "proj").exists()


def test_aborted_init_keeps_a_directory_that_already_existed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    import specify_cli

    existing = tmp_path / "proj"
    existing.mkdir()
    (existing / "keep.txt").write_text("user data", encoding="utf-8")

    def _fail(*_args, **_kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(specify_cli, "_install_shared_infra", _fail)
    result = _invoke_in(
        tmp_path,
        _init_args(
            "proj",
            "--force",
            "--integration-options",
            "--commands-dir .agent/commands",
        ),
    )

    assert result.exit_code == 1
    assert (existing / "keep.txt").read_text(encoding="utf-8") == "user data"


@pytest.mark.parametrize(
    ("previous", "expected"),
    [
        ({"feature_numbering": "timestamp"}, "timestamp"),
        ({"branch_numbering": "timestamp"}, "timestamp"),
        ({"feature_numbering": "bogus"}, "sequential"),
        ({}, "sequential"),
    ],
)
def test_reinit_preserves_feature_numbering(
    tmp_path: Path, previous: dict, expected: str
):
    """`init --here --force` (the documented fallback upgrade path) reset a
    project's numbering scheme to "sequential". A project on the deprecated
    `branch_numbering: timestamp` key was silently switched too, because the
    new `feature_numbering` value takes precedence over it."""
    import json

    project = tmp_path / "proj"
    first = _invoke_in(
        tmp_path,
        _init_args("proj", "--integration-options", "--commands-dir .agent/commands"),
    )
    assert first.exit_code == 0, _strip(first.stdout)
    options_file = project / ".specify" / "init-options.json"
    options = json.loads(options_file.read_text(encoding="utf-8"))
    options.pop("feature_numbering", None)
    options.update(previous)
    options_file.write_text(json.dumps(options), encoding="utf-8")

    second = _invoke_in(
        project,
        [
            "init",
            "--here",
            "--force",
            "--integration",
            "generic",
            "--integration-options",
            "--commands-dir .agent/commands",
            "--ignore-agent-tools",
            "--offline",
        ],
    )
    assert second.exit_code == 0, _strip(second.stdout)
    saved = json.loads(options_file.read_text(encoding="utf-8"))
    assert saved["feature_numbering"] == expected


def test_failure_panel_renders_error_text_literally(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Exception text was interpolated into Rich markup: a bracket run in a
    path was swallowed and a closing tag replaced the real error with a
    MarkupError message."""
    from specify_cli import command_init

    def _fail(*_args, **_kwargs):
        raise RuntimeError("cannot write C:/work/proj [v2]/x [/red] here")

    monkeypatch.setattr(command_init, "ensure_constitution_from_template", _fail)
    result = _invoke_in(
        tmp_path,
        _init_args("proj", "--integration-options", "--commands-dir .agent/commands"),
    )

    out = " ".join(_strip(result.stdout).split())
    assert result.exit_code == 1, out
    assert "proj [v2]/x [/red] here" in out
    assert not (tmp_path / "proj").exists()


def test_step_tracker_renders_labels_and_details_literally():
    from rich.console import Console

    from specify_cli._console import StepTracker

    tracker = StepTracker("Initialize")
    tracker.add("preset", "Install preset x[/red]")
    tracker.error("preset", "path C:/proj [v2] is [bold]busy[/bold]")
    tracker.complete("tools", "available: a[b]")

    recorder = Console(record=True, width=200)
    recorder.print(tracker.render())
    text = recorder.export_text()

    assert "Install preset x[/red]" in text
    assert "path C:/proj [v2] is [bold]busy[/bold]" in text
    assert "available: a[b]" in text
    assert "\\[" not in text


def test_cli_warning_renders_target_and_error_literally(capsys):
    from specify_cli import _print_cli_warning

    _print_cli_warning(
        "install", "preset", "x[/red]", RuntimeError("bad [bold]value[/bold]")
    )

    out = " ".join(_strip(capsys.readouterr().out).split())
    assert "Failed to install preset 'x[/red]': bad [bold]value[/bold]" in out


def test_shell_quote_arg_is_host_appropriate():
    """The helper follows `_version._render_argv`: list2cmdline on Windows,
    shlex.quote elsewhere. Names needing no quoting round-trip unchanged."""
    assert _shell_quote_arg("my-project") == "my-project"
    quoted = _shell_quote_arg("my project")
    assert quoted != "my project"
    if os.name == "nt":
        assert quoted == '"my project"'
    else:
        assert quoted == "'my project'"
