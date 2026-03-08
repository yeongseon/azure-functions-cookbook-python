# AGENT

## Purpose

This repository maintains practical Azure Functions Python recipes and scaffold-ready examples.

## Working Rules

- Keep all repository content in English.
- Treat recipe quality as the primary product surface.
- Prefer reusable patterns over one-off demos.
- Keep root planning documents in the repository root.
- Keep user-facing documentation in `docs/`.
- Keep recipe source material in `recipes/`.
- Keep runnable sample code in `examples/`.

## Quality Bar

- `make check-all` must pass before merge.
- `make docs` must build successfully before merge.
- New recipe work should include production considerations and local run instructions.
- Example code should stay simple enough to read, but realistic enough to be useful.
