# Security policy

Cavaleiro Spec Driven ships the `specify` CLI and the scripts, templates, and agent commands that it installs into real projects. The CLI downloads and extracts archives, runs shell and PowerShell scripts, and writes files that AI coding agents act on. A flaw here can spread to every project that uses it, so security reports are taken seriously.

## Reporting a vulnerability

**Please do not open a public issue.** Report privately through GitHub:

1. Go to the repository's **Security** tab.
2. Select **Report a vulnerability** (private vulnerability reporting), or open the form directly at <https://github.com/cavaleiro-ai/cavaleiro-spec-driven/security/advisories/new>.

Please include:

- The affected file and line, command, or script.
- Your operating system, shell (Bash, PowerShell 5.1 or 7, Python), Python version, and `specify version` output.
- Steps to reproduce, and the impact you expect.

Redact secrets, tokens, and private data.

## Vulnerabilities that also affect the original project

If the issue also affects the original project, report it to the original project's maintainers through their own security policy as well. They handle their code through their own coordinated-disclosure process. Please tell us too, so we can ship a fix here.

## What is in scope

- **CLI download and archive handling.** This covers bypasses of the HTTPS and redirect policy, ZIP or tar.gz path traversal, symlink or special-file members, size and memory limits, and unsafe temporary files (`src/specify_cli/_download_security.py` and its callers).
- **Project file writes.** This covers writes that escape the project root, follow symlinks, or overwrite user files that `init`, `integration`, `extension`, `preset`, `workflow`, or `bundle` commands were not supposed to touch.
- **Shell, PowerShell, and Python scripts** under `scripts/` and the bundled `extensions/`. This covers command injection, unsafe quoting, wildcard path expansion, and behavior that differs between the Bash, PowerShell, and Python variants in a security-relevant way.
- **Authentication handling.** This covers tokens leaked to the wrong host, logged, or sent over plain HTTP.
- **CI workflows** in `.github/workflows/`. This covers excessive permissions and script injection.

## What is out of scope

- Third-party extensions, presets, bundles, workflows, and integrations listed in community catalogs. Catalog listings are not audits. Report problems to the component's own maintainers.
- The original project's community catalogs that the CLI reads at runtime from `raw.githubusercontent.com/github/spec-kit`. Report those to the original project.
- Workflows in `.github/workflows-disabled/`. They do not run in this repository.
- Code that an AI agent writes in your project while following the generated commands.

## What to expect

This is a community-maintained project, so timelines are best effort:

- Acknowledgement of your report within **7 days**.
- An initial assessment, and a plan or a request for more information, within **14 days**.
- A fix on `main` and a published advisory once the issue is resolved. The advisory credits you unless you prefer to stay anonymous.

## Supported versions

Only the latest Cavaleiro Spec Driven release and the `main` branch receive security fixes.
