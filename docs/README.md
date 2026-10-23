# Documentation

This folder contains the documentation source files for Cavaleiro Spec Driven, built using [DocFX](https://dotnet.github.io/docfx/).

## Building Locally

To build the documentation locally:

1. Install DocFX:

   ```bash
   dotnet tool install -g docfx
   ```

2. Build the documentation:

   ```bash
   cd docs
   docfx docfx.json --serve
   ```

3. Open your browser to `http://localhost:8080` to view the documentation.

## Structure

- `docfx.json` - DocFX configuration file
- `index.md` - Main documentation homepage
- `toc.yml` - Table of contents configuration
- `installation.md` - Installation guide
- `quickstart.md` - Spec-Driven Development walkthrough
- `guides/agentic-sdlc.md` - How the original project applies agentic and conventional SDLC practices to itself
- `guides/bugfix.md` - Bug-fixing walkthrough
- `guides/assessment.md` - Idea assessment walkthrough
- `guides/customization.md` - Choosing and combining customization building blocks
- `reference/catalogs.md` - Catalog discovery, trust, private sources, and precedence
- `reference/agentic-*.md` - Detailed process command references
- `_site/` - Generated documentation output (ignored by git)

## Deployment

The original project builds and deploys this documentation to GitHub Pages when changes are pushed to `main`. In Cavaleiro Spec Driven, that workflow is disabled: it lives in `.github/workflows-disabled/docs.yml` (see the [README there](../.github/workflows-disabled/README.md)). Re-enable it only after you set up GitHub Pages for your own repository. The Cavaleiro-specific guides are in [`cavaleiro/`](cavaleiro/ENGINEERING.md).
