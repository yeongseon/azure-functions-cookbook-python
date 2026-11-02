# Agent Playbook

## Source Of Truth
- `AGENTS.md` for repository-wide engineering and agent rules.
- `README.md` for installation, quick start, and CLI examples.
- `CONTRIBUTING.md` for branch, commit, and release workflow.
- `pyproject.toml` and `Makefile` for supported commands.

## Repository Map
- `src/azure_functions_python_cookbook/` package code.
- `tests/` recipe and example coverage.
- `examples/` curated Azure Functions recipes.
- `docs/` documentation site content.

## Change Workflow
1. Confirm whether the change affects recipe content, example quality, integration patterns, or docs only.
2. Update examples when they are used as public contract material.
3. Keep tests and docs in lockstep for public behavior changes.
4. Do not broaden supported Python versions or dependency ranges casually.

## Issue Authoring
- Before creating or editing an issue (forms, API, or CLI), follow
  [AGENTS.md "Issue Conventions"](https://github.com/yeongseon/azure-functions-cookbook-python/blob/main/AGENTS.md#issue-conventions) —
  ground it in verified evidence from this repository, search for duplicates, and review every
  project name/link in the title and body for unrelated copied context.
- After saving, fetch the issue again and verify the saved title, body, and labels before
  reporting completion.

## Validation
- `make test`
- `make lint`
- `make typecheck`
- `make security`
- `make build`

## Pull Request Descriptions

Follow `AGENTS.md` for concise, human-readable PR summaries and actual validation results.
Record additional review evidence only for significant findings or changes covered by
[review-evidence-policy.md](review-evidence-policy.md). Do not add an empty "Review Evidence"
section or copy agent review logs into ordinary PRs.

