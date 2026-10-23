"""PowerShell scripts must treat project paths literally.

``Test-Path``, ``Set-Location``, ``Get-ChildItem -Path``, ``Resolve-Path`` and
``Get-Content`` interpret ``[`` and ``]`` as wildcard characters. In a project
whose path contains them -- ``specify init "proj [v2]"`` creates exactly that
-- ``create-new-feature.ps1`` died on ``Set-Location $repoRoot`` and every
existence check reported present files as missing, while the Bash and Python
twins worked. The scripts now pass user paths through ``-LiteralPath``.
"""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

import pytest

from tests.parity_helpers import (
    HAS_POWERSHELL,
    POWERSHELL_EXE,
    PROJECT_ROOT,
    install_scripts,
    make_repo,
    ps_cmd,
    py_cmd,
    run,
)

requires_powershell = pytest.mark.skipif(
    not HAS_POWERSHELL, reason="PowerShell is not available"
)

BRACKET_NAME = "proj [v2]"

PS_SCRIPT_DIRS = [
    PROJECT_ROOT / "scripts" / "powershell",
    *sorted((PROJECT_ROOT / "extensions").glob("*/scripts/powershell")),
]

# A path cmdlet called with a positional or -Path argument (wildcard-expanded)
# instead of -LiteralPath. New-Item and Join-Path are absent on purpose: they
# never expand wildcards in -Path.
_WILDCARD_PATH_CALL = re.compile(
    r"\b(?:Test-Path|Set-Location|Get-ChildItem|Resolve-Path|Get-Content|Remove-Item)"
    r"\s+(?:-Path\s|-PathType\s+\w+\s+[\$(\"]|[\$(\"])",
    re.IGNORECASE,
)


def test_powershell_scripts_pass_paths_with_literalpath() -> None:
    offenders = []
    for directory in PS_SCRIPT_DIRS:
        for script in sorted(directory.glob("*.ps1")):
            for number, line in enumerate(
                script.read_text(encoding="utf-8").splitlines(), start=1
            ):
                if line.lstrip().startswith("#"):
                    continue
                if _WILDCARD_PATH_CALL.search(line):
                    offenders.append(
                        f"{script.relative_to(PROJECT_ROOT)}:{number}: {line.strip()}"
                    )
    assert offenders == [], "use -LiteralPath for project paths:\n" + "\n".join(
        offenders
    )


def _bracket_repo(tmp_path: Path, *scripts: str) -> Path:
    repo = make_repo(tmp_path, BRACKET_NAME)
    for script in scripts:
        install_scripts(repo, script)
    templates = repo / ".specify" / "templates"
    templates.mkdir(parents=True, exist_ok=True)
    for name in ("spec-template", "plan-template", "tasks-template"):
        shutil.copy(PROJECT_ROOT / "templates" / f"{name}.md", templates / f"{name}.md")
    return repo


@requires_powershell
def test_create_new_feature_ps_works_in_bracketed_project(tmp_path: Path) -> None:
    repo = _bracket_repo(tmp_path, "create-new-feature")

    result = run(ps_cmd(repo, "create-new-feature", "-Json", "Add login page"), repo)

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout.strip().splitlines()[-1])
    assert payload["BRANCH_NAME"] == "001-login-page"
    spec = repo / "specs" / "001-login-page" / "spec.md"
    assert spec.is_file()
    assert spec.read_text(encoding="utf-8").strip()  # template copied, not empty


@requires_powershell
def test_check_prerequisites_ps_matches_python_in_bracketed_project(
    tmp_path: Path,
) -> None:
    repo = _bracket_repo(tmp_path, "check-prerequisites")
    feature = repo / "specs" / "001-login-page"
    (feature / "contracts").mkdir(parents=True)
    for name in ("spec.md", "plan.md", "tasks.md", "research.md", "quickstart.md"):
        (feature / name).write_text(f"# {name}\n", encoding="utf-8")
    (feature / "contracts" / "api.md").write_text("# api\n", encoding="utf-8")
    (repo / ".specify" / "feature.json").write_text(
        json.dumps({"feature_directory": "specs/001-login-page"}), encoding="utf-8"
    )

    ps = run(
        ps_cmd(repo, "check-prerequisites", "-Json", "-RequireTasks", "-IncludeTasks"),
        repo,
    )
    py = run(
        py_cmd(
            repo, "check-prerequisites", "--json", "--require-tasks", "--include-tasks"
        ),
        repo,
    )

    assert py.returncode == 0, py.stderr
    assert ps.returncode == 0, ps.stderr
    ps_payload = json.loads(ps.stdout)
    assert ps_payload["AVAILABLE_DOCS"] == json.loads(py.stdout)["AVAILABLE_DOCS"]
    assert {"research.md", "contracts/", "quickstart.md", "tasks.md"} <= set(
        ps_payload["AVAILABLE_DOCS"]
    )


@requires_powershell
def test_git_extension_branch_script_works_in_bracketed_project(
    tmp_path: Path,
) -> None:
    repo = _bracket_repo(tmp_path, "create-new-feature")
    git_scripts = repo / ".specify" / "extensions" / "git" / "scripts" / "powershell"
    shutil.copytree(PROJECT_ROOT / "extensions" / "git" / "scripts" / "powershell", git_scripts)
    shutil.copy(
        PROJECT_ROOT / "extensions" / "git" / "extension.yml",
        repo / ".specify" / "extensions" / "git" / "extension.yml",
    )
    (repo / "specs" / "001-existing").mkdir(parents=True)

    result = run(
        [
            POWERSHELL_EXE,
            "-NoProfile",
            "-File",
            str(git_scripts / "create-new-feature-branch.ps1"),
            "-Json",
            "-DryRun",
            "Second feature",
        ],
        repo,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout.strip().splitlines()[-1])
    assert payload["BRANCH_NAME"] == "002-second-feature"
