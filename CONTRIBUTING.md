# Contributing

## Scope

This project provides curated Azure Functions Python recipes, examples, and supporting documentation.

Contributions should improve one of these areas:

- recipe quality
- example quality
- architecture clarity
- documentation usability
- repository tooling

## Development Setup

```bash
make install
```

## Local Checks

Run these before opening a PR:

```bash
make check-all
make docs
```

## Contribution Guidelines

- Keep changes aligned with the product direction in `PRD.md`.
- Keep changes aligned with the design guardrails in `DESIGN.md`.
- Write all documentation and code comments in English.
- Prefer small, reviewable pull requests.
- Update recipe documentation when examples or recommended structure change.
- Add or update tests for any code that becomes part of the repository package.
- Keep repository test coverage at or above 90 percent.

## Recipe Guidelines

Each recipe should include:

- overview
- when to use
- architecture
- project structure
- local run instructions
- production considerations
- scaffold starter guidance when available

## Code of Conduct

Be respectful and inclusive. See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) for details.
