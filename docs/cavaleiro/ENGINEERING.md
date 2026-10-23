# Cavaleiro Spec Driven — engineering report

This report records how Cavaleiro Spec Driven 1.0.0 was derived from the original project. It covers the architecture as studied, the test baseline, every finding, how each fix was verified, and what was left undone. A Portuguese overview is in the [guide](GUIA-PT-BR.md).

| | |
| --- | --- |
| Original project | Branch `main`, commit `c6a4c18f1d01a8bec241c618eb6dfea952508744` (2026-10-16), package `specify-cli` 1.2.2.dev0 |
| License | MIT. The original copyright line is kept verbatim in [LICENSE](../../LICENSE). |
| Release | Cavaleiro Spec Driven 1.0.0 (2026-10-17). See the [changelog](../../CHANGELOG.md). |
| Machine | Windows 10 Pro 19045, Python 3.12.2 (uv venv), Windows PowerShell 5.1, Git for Windows. No `pwsh`. Bare `bash` resolves to the WSL launcher. |

## 1. Architecture map

### Components

| Area | Location | Responsibility |
| --- | --- | --- |
| Entry point | `src/specify_cli/__init__.py` (`specify = specify_cli:main`) | Builds the Typer app (`BannerGroup`), registers the command modules, and forces UTF-8 stdout/stderr on Windows. |
| `init` | `command_init.py`, `_project.py`, `_init_options.py`, `_file_policy.py` | Validates the target (new directory, `--here`, `--force`, `SPECIFY_INIT_DIR`), then installs, in order: the integration, the shared infrastructure, the `speckit` workflow, `init-options.json`, presets, extensions, and the constitution. A Rich `Live` tracker shows progress. |
| Shared infrastructure | `shared_infra.py`, `_assets.py` | Copies `.specify/scripts/{bash,powershell,python}` and `.specify/templates` from the wheel's `core_pack`, which works offline, or from a source checkout. Resolves `__SPECKIT_COMMAND_*__` placeholders and records hashes in `speckit.manifest.json`, so refreshes preserve user edits. |
| Integrations | `integrations/` (42 agents), `integrations/base.py`, `installer.py`, `_lifecycle.py`, `manifest.py` | Each agent package declares where commands or skills go and in which format. `external_lifecycle` wraps `init`/`install`/`switch`/`upgrade` in a transaction with a file journal and rollback, and loads external adapter packages from catalogs on an explicit trust decision. |
| Components | `extensions/`, `presets/`, `workflows/`, `bundles/`, `artifacts/`, `events/` | Install, update, remove, catalog stacks (default, community, and project or env overrides), a priority-based template resolver, the workflow engine (`workflows/engine.py`, `workflows/step/*`, overlays), bundles of components, an artifact inventory, and agent-lifecycle event hooks. |
| Downloads and archives | `_download_security.py` | The HTTPS-or-loopback URL policy and redirect checks, bounded response reads, archive-format detection, and safe ZIP/tar.gz extraction. Extraction rejects traversal, absolute and drive paths, links, special files, Windows-reserved names, case collisions, ZIP64, and oversized members or totals. |
| Authentication | `authentication/` | Token providers (GitHub, Azure DevOps, Bitbucket) applied only to configured hosts. Auth headers are stripped on redirects off-host or to HTTP. |
| Self management | `_version.py`, `selfs/` | `version`, `self check`, and `self upgrade`. Detects the install method (uv tool, pipx, uvx, source checkout) and re-runs the matching installer. |
| MCP | `mcp_server/`, `command_mcp.py` | Experimental stdio MCP server that exposes CLI operations as typed tools. |
| Scripts | `scripts/{bash,powershell,python}`, `extensions/*/scripts/*` | Bash, PowerShell 5.1, and Python twins that agent commands call: `create-new-feature`, `check-prerequisites`, `setup-plan`, `setup-tasks`, `resolve-template`, and the git extension's `create-new-feature-branch`, `auto-commit`, and `initialize-repo`. CONTRIBUTING requires the twins to behave the same. |
| Templates | `templates/commands/*.md`, `templates/*-template.md` | Agent command prompts and the spec, plan, tasks, checklist, and constitution templates. Integrations render them into each agent's format. |

### Data and control flow

```text
specify init --integration X ──► target validation ──► prepare_init_root ──► Live tracker:
   integration.setup(manifest) → shared infra (scripts/templates) → speckit workflow
   → init-options.json → presets → extensions (bundled / path / URL via _download_security)
   → constitution → "Project ready"            (failure ⇒ cleanup of a directory init created)

agent: /speckit-specify ─► before_specify hook (git ext: create-new-feature-branch.{sh,ps1,py})
       ─► core script create-new-feature ─► specs/NNN-name/spec.md + .specify/feature.json
       /speckit-plan ─► setup-plan ─► plan.md   /speckit-tasks ─► setup-tasks ─► tasks.md

specify extension|preset|workflow|bundle add <id|--from URL>
   ─► catalog stack (env/project/default/community) ─► open_url (auth, redirect policy)
   ─► read_response_limited ─► detect_archive_format ─► safe_extract_archive ─► install + register
```

### Extension points, configuration, tests, and release

- **Extension points.** Integrations (built-in packages or catalog-delivered adapters), extensions (commands, hooks, scripts, templates), presets (templates, commands, and scripts with `replace`/`prepend`/`append`/`wrap` strategies), workflows and custom step packages, bundles, and project-local template overrides.
- **Configuration.**
  - Project files: `.specify/init-options.json`, `integration.json`, `*.registry`, `feature.json`, and the catalog files.
  - User file: `~/.specify/auth.json`.
  - Environment: `SPECIFY_INIT_DIR`, `SPECIFY_FEATURE*`, `SPECKIT_*_CATALOG_URL`, `SPECKIT_PYTHON_EXECUTABLE`, `GH_TOKEN`/`GITHUB_TOKEN`, `SPECIFY_UPGRADE_TIMEOUT_SECS`, and `SPECIFY_UPGRADE_REPOSITORY`, which is new.
- **Tests (`tests/`, about 12.7k).**
  - `tests/specify_cli/**` mirrors the source modules.
  - `tests/integrations/**` has per-agent tests.
  - `tests/extensions/**` covers the bundled extensions, including Bash/PS/Python parity.
  - `tests/workflows/**` covers the workflow engine.
  - `tests/contract/**` checks wheel and catalog consistency.
  - Top-level files cover script parity, download security, and the GitHub workflow contracts.
- **Build and release.**
  - `hatchling` builds the wheel and force-includes templates, scripts, extensions, presets, workflows, and bundle catalogs into `specify_cli/core_pack`.
  - The original project releases through `release-trigger.yml` (version bump and tag, using `RELEASE_PAT`), then `release.yml` (GitHub release), then `publish-pypi.yml` (trusted publishing).
  - Docs are built with DocFX and deployed to Pages by `docs.yml`.
  - In this fork those workflows live in `.github/workflows-disabled/`.

## 2. Baseline

Setup: `uv sync --extra test --python 3.12` inside the derivative (identical to the original project at that point).

Command (also used for the final run):

```powershell
.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider -o addopts="" --tb=line
```

| Run | Passed | Failed | Skipped | Duration |
| --- | --- | --- | --- | --- |
| Baseline (original project, `c6a4c18`) | 11,549 | 133 | 1,035 | 1 h 54 min (machine shared with nine other jobs) |

All 133 baseline failures are environmental and come from this Windows host:

- **110 tests** need symlink creation (`OSError: [WinError 1314] the client does not have the required privilege`). They pass on Linux/macOS CI, or on Windows with Developer Mode.
- **21 tests** in `tests/test_github_workflows.py` (`test_community_download_command_treats_url_file_as_data[...]`) run bare `bash`. Windows resolves that to `System32\bash.exe`, the WSL launcher, which has no distribution installed. The original project's own `requires_bash` guard rejects that launcher, but these 21 tests do not use the guard.
- **1 test**, `tests/integrations/test_capture.py::...::test_bounded_capture_reports_timeout_instead_of_raising`, is timing-sensitive under Windows process scheduling and load (`'' == 'partial\n'`).
- **1 test**, `tests/integrations/test_integration_generic.py::test_generic_extension_rejects_modified_artifact_on_disable[False]`, fails because Rich wraps a long Windows temp path in the middle of the asserted phrase.

The skip count includes every `requires_bash` test (the WSL launcher is rejected) and every test that needs `pwsh` 7.

## 3. Findings

Severity reflects reachability and impact. Each "Fixed" row has a regression test that fails on the original project's commit and passes here.

| # | Finding | Severity | Status | Evidence / test |
| --- | --- | --- | --- | --- |
| F1 | tar.gz GNU long-name or pax headers are read into memory whole, before any check. A ~20 KiB archive allocates gigabytes, a 16 MiB name ends up in the error text, and chained headers raise an uncaught `RecursionError`. | High | Fixed | `tests/test_download_security.py::test_safe_extract_archive_bounds_tar_extended_header_memory[L/x]`, `::test_tar_extended_header_chain_is_bounded_not_recursion_error`, `::test_safe_extract_tar_accepts_real_extended_headers[GNU/PAX]` |
| F2 | Responses shorter than `Content-Length` are accepted: `http.client` returns `b""` on an early close. A truncated `workflow.yml` installed with exit 0. | Medium | Fixed | `tests/test_download_security.py::test_read_response_limited_rejects_body_shorter_than_content_length`, `::test_read_response_limited_detects_real_connection_cut_short` (real socket), `tests/specify_cli/workflows/test_command_add.py::...::test_add_from_url_rejects_body_shorter_than_content_length` |
| F3 | `IncompleteRead`, `ConnectionResetError`, and `TimeoutError` raised during the body read escape handlers that catch only `URLError`. Affects `extension add --from`, `preset add --from`, extension and preset catalog downloads, and extension and integration catalog fetches. A non-UTF-8 extension catalog crashes too. | Medium | Fixed | `tests/test_download_transport_errors.py` (19 cases) |
| F4 | A failed `init <new-dir>` leaves the directory behind. Options were parsed after the directory was created, and cleanup ran only for plain exceptions, not for `typer.Exit`, `SystemExit`, or Ctrl-C. The retry then fails with "Directory already exists". | Medium | Fixed | `tests/specify_cli/test_command_init.py::test_rejected_integration_options_leave_no_directory`, `::test_aborted_init_removes_the_directory_it_created[...]`, `::test_aborted_init_keeps_a_directory_that_already_existed` |
| F5 | `self upgrade` does not detect a `uv tool` install on Windows. uv uses `%APPDATA%\uv\tools` and copies the launcher into `~\.local\bin`. | Medium | Fixed | `tests/specify_cli/test_version_detection.py::...::test_copied_launcher_is_detected_from_interpreter_prefix` (+ negative test) |
| F6 | `init --here --force`, the documented fallback upgrade, resets `feature_numbering` to `sequential`. That also silently switches projects on the deprecated `branch_numbering: timestamp`. | Medium | Fixed | `tests/specify_cli/test_command_init.py::test_reinit_preserves_feature_numbering[...]` |
| F7 | Unescaped Rich markup in the init failure panel, the tracker details, preset warnings, and `_print_cli_warning`. A `[/red]` in an error replaces it with `MarkupError` and skips cleanup, and text like `[v2]` disappears. | Low | Fixed | `tests/specify_cli/test_command_init.py::test_failure_panel_renders_error_text_literally`, `::test_step_tracker_renders_labels_and_details_literally`, `::test_cli_warning_renders_target_and_error_literally` |
| F8 | PowerShell scripts pass project paths to wildcard-expanding cmdlets. In `proj [v2]`, which `specify init` creates without complaint, `create-new-feature.ps1` dies at `Set-Location` and existence checks fail. Bash and Python work. | Medium (Windows) | Fixed | `tests/test_ps1_literal_paths.py` (static guard plus 3 behavioral tests on PS 5.1) |
| F9 | The git extension fails the mandatory `before_specify` hook when `GIT_BRANCH_NAME` names the current branch (original issue #5003). | Medium | Fixed | `tests/extensions/git/test_git_extension_python_parity.py::TestGitBranchNameOverrideOfCurrentBranch` (Python in pytest; Bash and PS 5.1 by direct runs) |
| F10 | `self check` and `self upgrade` are hard-wired to the original project, so upgrading a fork install replaces it with the original project's release. | Fork safety | Added opt-in `SPECIFY_UPGRADE_REPOSITORY` | `tests/specify_cli/test_version_upgrade_repository.py` |
| N1 | On Windows, NTFS 8.3 short names (`LONGFI~1.TXT`) in an archive can alias another member, so two names write one file. Nothing escapes the target directory. | Low | Not fixed | See section 5 |
| N2 | `self check` raises on malformed JSON or `BadStatusLine` from the release API. | Low | Not changed | The original project deliberately lets malformed bodies propagate ("research D-006") |
| N3 | `extension update` drops skills registered for non-default integrations (original issue #5002). | Medium | Not fixed | Needs multi-integration re-registration design; original PR #5005 open |
| N4 | Codex skills render hook "To execute" lines with `/` instead of `$` (original issue #4954). | Low | Not fixed | 28 template sites; original PR #4958 open |
| N5 | `extension remove`/`preset remove` trust registry IDs, so `../victim` deletes outside the folder (original issue #4744). | Low (needs a tampered local registry) | Not fixed | Original PR #4745 open |
| N6 | Junie `$ARGUMENTS` handling (original issue #4794) and kiro-cli exec arguments (original issue #4797). | Low | Not fixed | Cannot be validated without those agents |

## 4. Improvements and verification

Each fix has a "before" run and an "after" run.

- **Before:** the new tests run with `PYTHONPATH=<original clone>/src` (and `PYTHONDONTWRITEBYTECODE=1`, so the pristine clone is not touched). Script tests run in a scratch tree assembled from the original project's `scripts/`, `extensions/`, and `templates/`.
- **After:** the same tests run on this tree.

| # | Change | Before | After |
| --- | --- | --- | --- |
| F1 | `_download_security.py`: `_BoundedTarInfo` (passed as `tarinfo=` to every `tarfile.open`) rejects extended headers over 64 KiB or more than 8 in a row, before `tarfile` buffers them. `_TarHeaderLimitError` maps to "Unsafe tar.gz archive: …". | 3 of 5 tests fail: `RecursionError`, a 16 MiB message, a pax header extracted after a 16 MiB allocation | 5/5 pass; real GNU and pax long names still extract |
| F2 | `read_response_limited` and `workflows/_commands._read_response_within_limit` compare the bytes received with `Content-Length` (ignored with `Transfer-Encoding`, malformed values, or mock headers) through the new `declared_content_length()`. | 3 tests fail; the CLI installs a truncated workflow with exit 0 | pass; "response truncated: received N of M bytes" |
| F3 | The new `DOWNLOAD_TRANSPORT_ERRORS` (`URLError`, `HTTPException`, `ConnectionError`, `TimeoutError`, `ssl.SSLError`) is used at the 7 download/catalog sites. The extension catalog also reports non-UTF-8 bodies. | 19/19 fail (tracebacks or a misleading "Failed to save") | 19/19 pass |
| F4 | `command_init.py`: `--integration-options` are parsed before `prepare_init_root`. Cleanup moved to `finally` behind an `init_completed` flag, so it covers `Exit`, `SystemExit`, and `KeyboardInterrupt`. It never removes a directory that existed before, or one owned by an external lifecycle. | 3 fail | pass; the retry succeeds without `--force` |
| F5 | `_version.py`: the `%APPDATA%\uv\tools\specify-cli\` prefix was added, and tier-1 detection also checks `sys.prefix` when argv is the running process. | `UNSUPPORTED` | `UV_TOOL` (tier 1) |
| F6 | `_preserved_feature_numbering()` keeps a valid previous `feature_numbering`, or migrates `branch_numbering`, and otherwise falls back to `sequential`. | 2/4 cases fail | 4/4 pass |
| F7 | `StepTracker.render` escapes labels and details. The failure panel, preset warnings, `_print_cli_warning`, and the shared-infra error escape their text. `command_check` no longer pre-escapes. | 3 fail (`MarkupError`) | pass; no double escaping (`\[` absent) |
| F8 | `-LiteralPath` for `Test-Path`, `Set-Location`, `Get-ChildItem`, `Resolve-Path`, `Get-Content`, and `Remove-Item` across 10 core and extension scripts. `New-Item` and `Join-Path` don't expand wildcards. All 9 changed files parse under PS 5.1 and stay ASCII. | 4/4 fail; manual repro: `create-new-feature.ps1` exit 1 at `Set-Location` | 4/4 pass; manual repro: create, then plan, then git-branch all succeed |
| F9 | All three twins: an override equal to the current branch is a no-op, and a different existing branch still fails. Git extension bumped to 1.0.2 (manifest and catalog) as the extension-version guard requires. | Python test fails; Bash and PS 5.1 exit 1 | Python passes; Bash and PS 5.1 exit 0 (current) and exit 1 (other branch) |
| F10 | `_upgrade_repository()`, `_latest_release_api_url()`, `_git_source_url()`, `_releases_page_url()`; invalid slugs raise `typer.BadParameter` (exit 2). | — | 11 tests pass; defaults byte-identical to the original project |

Related suites re-run after each change (all green apart from the baseline symlink failures):

- download security plus workflow add: 320 passed, 4 baseline symlink failures.
- init, check, and console: 42 passed.
- version and self: 153 passed.
- script and parity suites (14 files): 467 passed, 0 failed.
- git extension parity: 12 passed.

Lint results on changed files:

- `ruff 0.14.0 check` passes on all changed Python files. The same files were clean in the original project.
- `shellcheck --severity=error` passes on the changed Bash script. The warning count is unchanged at 20, all pre-existing.
- The PS 5.1 parser reports 0 errors.
- markdownlint-cli2 results are in section 7.

## 5. What was not done, and why

- **N1, 8.3 aliases.** Opening members with exclusive-create (`"xb"`) would reject aliases. It also changes extraction semantics for every caller, and the issue cannot escape the target directory. Deferred, with a regression idea noted in this report.
- **N2.** The original project documents that malformed release bodies propagate by design. Changing `self check` semantics is out of scope.
- **N3 to N6.** These are issues of the original project with open PRs there that need design decisions, or agents that could not be run here. Fixing them in a fork first would diverge from the original project's direction.
- **Unverified leads.** The interrupted Bash/PowerShell parity research produced patches for three issues: PS 5.1 output encoding of non-ASCII JSON when redirected, `Get-Python3Command` failing under `$ErrorActionPreference='Stop'` with a broken interpreter, and culture-sensitive `ToLower()` under `tr-TR`. The existing parity tests (including the PS 5.1 Unicode tests) pass on this machine, and there was no budget to build independent repros. They are not included, and are listed as next steps.
- **No renames of identifiers.** The package, command, environment variables, catalog URLs, and the `speckit` command names are unchanged on purpose (see [Compatibility](../../README.md#compatibility)). The package version stays `1.2.2.dev0`, so release comparisons and extension `requires` checks keep working.
- **Inherited docs** under `docs/` keep their content, with the product name changed to Cavaleiro Spec Driven. Self-links now point here. History (PR, issue, and commit links), runtime catalog URLs, and the original project's release-install commands stay as they are, and a note on the install pages explains this.

## 6. Known limitations

- Linux and macOS were not exercised locally. CI (`test.yml`, kept enabled) runs the full matrix once the repository is pushed.
- On Windows, symlink tests need Developer Mode. `requires_bash` tests need Git Bash to be the first `bash` that `CreateProcess` finds. `pwsh`-only tests need PowerShell 7.
- `specify self upgrade` still targets the original project unless `SPECIFY_UPGRADE_REPOSITORY` is set. A fork that wants to use it must publish tags that parse as versions newer than the installed package version.
- The community catalogs and the agentic catalog-submission automation stay the original project's. The workflows for them are disabled here.

## 7. Final verification

| Run | Passed | Failed | Skipped | Duration |
| --- | --- | --- | --- | --- |
| Final (this tree) | 11,612 | 132 | 1,037 | 40 min |

The final run used the same command as the baseline, and compared with it:

- **No new failures.** The 132 failures are a strict subset of the 133 baseline failures: 110 symlink-privilege, 21 WSL-`bash`, and the Rich line-wrap test.
- **One baseline failure passed:** the timing-sensitive capture test. It passed in both final runs, which had less machine load, so it is flaky rather than fixed.
- **The +63 passed are the new regression tests.**
- **The +2 skipped are the new Bash-parity and `pwsh`-only variants of the `GIT_BRANCH_NAME` test.** On this host they were verified by direct Git Bash and PS 5.1 runs instead.

An earlier final run, before the example-bundle pins and two test fixtures were updated for the extension version bumps and the moved workflows, had 6 additional failures. Those 6 caught real inconsistencies and are fixed:

- 4 example bundles still pinned `agent-context` 1.0.2.
- The git manifest test pinned version `1.0.1`.
- One hard-coded `.lock.yml` path still pointed at `.github/workflows/`.

The affected files were then re-run: 631 passed, and only the 21 baseline WSL failures remained.

Checks on changed files:

- `ruff 0.14.0`: clean.
- `shellcheck --severity=error`: clean.
- PowerShell 5.1 parser: 0 errors, ASCII only.
- markdownlint-cli2 0.18.1 over the CI documentation globs plus the new files: 0 errors.
- Relative-link check over all changed Markdown: 392 links, 0 broken. One false positive is a regex inside a moved workflow prompt.
- `git diff --cached --check`: clean.

## 8. Recommended next steps

1. Push the repository and confirm the CI matrix (`test.yml`, `lint.yml`, `security.yml`, `codeql.yml`) on Ubuntu, macOS, and Windows.
2. Offer F1 to F9 to the original project as focused PRs. Each already has a failing-before regression test. F9 overlaps original PR #5006.
3. Turn the unverified Bash/PowerShell parity leads (section 5) into repros, starting with PS 5.1 non-ASCII JSON over a redirected stdout.
4. Harden `extension remove`/`preset remove` ID validation (N5), and design multi-integration re-registration for `extension update` (N3).
5. Decide on a release-tag scheme for the fork before recommending `SPECIFY_UPGRADE_REPOSITORY` to users.
