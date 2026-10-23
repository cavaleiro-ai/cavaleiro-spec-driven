# Disabled workflows

GitHub Actions only runs workflows stored in `.github/workflows/`. The files in this folder were moved here on purpose when Cavaleiro Spec Driven was derived from [GitHub Spec Kit](https://github.com/github/spec-kit), so that a fork never publishes, deploys, or talks to infrastructure under the original project's identity.

| Workflow | Why it is disabled |
| --- | --- |
| `publish-pypi.yml` | Publishes the `specify-cli` package to PyPI. That name belongs to the upstream project. |
| `release-trigger.yml` | Bumps the version, pushes release branches and tags, and opens pull requests with the `RELEASE_PAT` secret. |
| `release.yml` | Creates GitHub releases with write access on every tag push. |
| `docs.yml` | Builds the DocFX site and deploys it to GitHub Pages. |
| `stale.yml` | A bot that labels and closes issues and pull requests under upstream's triage policy. |
| `catalog-assign.yml` | A bot that comments on and assigns upstream community-catalog submission issues. |
| `add-community-*.md` / `.lock.yml` | GitHub Agentic Workflows (gh-aw) that validate community catalog submissions and open catalog pull requests. They need `COPILOT_GITHUB_TOKEN`, `GH_AW_GITHUB_TOKEN`, `GH_AW_GITHUB_MCP_SERVER_TOKEN`, and `GH_AW_CI_TRIGGER_TOKEN`. |
| `bug-assess`, `bug-fix`, `bug-test`, `feature-assess`, `pr-assess` (`.md` / `.lock.yml`) | Agentic triage workflows with the same Copilot and gh-aw secrets, plus OTLP telemetry headers. |
| `RELEASE-PROCESS.md` | Documentation for the release workflows above. It moved with them. |

The workflows still in `.github/workflows/` need only `GITHUB_TOKEN`:

- `test.yml`, `lint.yml`, `security.yml`, and `extension-version-guard.yml` have read-only permissions.
- `codeql.yml` additionally needs `security-events: write`, and only uploads analysis results to this repository's own code-scanning page.

## Re-enabling a workflow

1. Read the workflow and replace anything that identifies the upstream project. That includes package names, the PyPI environment, the GitHub Pages site, labels, and catalog URLs.
2. Create your own credentials as repository secrets. Never reuse someone else's. PyPI publishing should use [trusted publishing](https://docs.pypi.org/trusted-publishers/) for a package name you own. Do not publish this fork as `specify-cli`.
3. For gh-aw workflows, recompile the `.md` source with the `gh aw compile` version pinned in `.github/aw/actions-lock.json` instead of hand-editing the `.lock.yml` file.
4. Move the files back with `git mv .github/workflows-disabled/<name> .github/workflows/`, then run `pytest tests/test_github_workflows.py`. It validates both folders.
