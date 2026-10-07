# Changelog

All notable changes to the Azure Functions Python Cookbook project will be documented in this file. This project adheres to Semantic Versioning.

## [0.1.1] - 2026-03-14

This release captures the tooling unification, documentation overhaul, and docs deployment infrastructure applied across the ecosystem.

### Added

- Unified tooling: Ruff (lint + format), pre-commit hooks, standardized Makefile
- Comprehensive documentation overhaul (MkDocs site with standardized nav)
- Translated README files (Korean, Japanese, Chinese)
- Standardized documentation quality across ecosystem
- GitHub Pages docs workflow (`.github/workflows/docs.yml`)
- 5 runnable example projects with smoke tests

## [0.1.0] - 2026-03-08

This is the initial release of the Azure Functions Python Cookbook, establishing the foundation for a comprehensive collection of production-ready recipes for Azure Functions development with Python.

### Added
- Initial repository structure for the Azure Functions Python Cookbook.
- Common repository tooling including CI workflows for testing and security.
- Pre-commit hooks for code quality, formatting, and type checking.
- Release automation using GitHub Actions and standardized tagging.
- Core product documentation: README.md, AGENT.md, DESIGN.md, and PRD.md.
- Documentation site built with MkDocs and the Material for MkDocs theme.
- Recipe template (`_template.md`) defining the standard recipe contract and structure.
- Five initial recipe placeholders to guide future development:
    - HTTP API Basic: Simple request/response handling.
    - HTTP API with OpenAPI: Documented APIs with Pydantic and validation.
    - GitHub Webhook: Handling external events with signature verification.
    - Queue Worker: Decoupled processing using Azure Storage Queues.
    - Timer Job: Scheduled tasks and maintenance operations.
- Translated README files for global accessibility:
    - Korean (README.ko.md)
    - Japanese (README.ja.md)
    - Simplified Chinese (README.zh-CN.md)
- Automated badge synchronization across all translated README files.
- Comprehensive development tooling integration:
    - Ruff: Fast linting and code analysis.
    - Black: Deterministic code formatting.
- Mypy: Static type checking for supported Python versions.
    - Pytest: Robust testing framework.
    - Bandit: Security-focused static analysis.
    - Hatch: Modern project management and build system.

## Versioning

This project follows [Semantic Versioning 2.0.0](https://semver.org/).

Given a version number MAJOR.MINOR.PATCH, we increment the:

1. MAJOR version when we make incompatible API changes (e.g., changing the recipe contract).
2. MINOR version when we add functionality in a backwards compatible manner (e.g., adding a new recipe).
3. PATCH version when we make backwards compatible bug fixes or documentation improvements.

For a documentation-first project like this, "breaking changes" often refer to significant restructuring of the repository or changes to the required metadata for recipes that would break existing integrations or automation.

## Release Process

Our release process is designed to be transparent and automated:

1. Changes are proposed via Pull Requests.
2. Automated CI checks must pass, including tests, linting, and security scans.
3. Once merged to the main branch, a new version is prepared.
4. A GitHub release is created with a version tag (e.g., `v0.1.0`).
5. The documentation site is automatically updated to reflect the new release.

Each release includes a summary of changes, categorized as Added, Changed, Fixed, or Removed, to help users understand what is new and what has changed since the previous version.

## Contributing to the Changelog

Contributors are encouraged to update the [Unreleased] section of the changelog when submitting a Pull Request. This makes it easier for maintainers to compile the final release notes. Please follow the format established in this file.

1. Ensure the change is categorized correctly (Added, Changed, Fixed, Removed).
2. Keep descriptions concise but informative.
3. Reference relevant issues or pull requests where applicable.

By maintaining a clear and detailed changelog, we ensure that the project remains accessible and understandable for all users and contributors.
