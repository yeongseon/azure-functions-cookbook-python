# Versions, snapshots, and verification

This cookbook is a collection of runnable examples and documentation, not a library. It is **not published to PyPI**; you do not `pip install` the cookbook. You read it, or clone it, and copy or adapt recipes.

## Am I reading `main` or a release?

- **`main`** is moving development content. It can contain recipes, fixes and docs that no release includes yet.
- **A tagged GitHub Release** is a reproducible snapshot of every recipe, its dependency bounds and its docs at that tag.

Find the latest snapshot on the [GitHub Releases page](https://github.com/yeongseon/azure-functions-cookbook-python/releases). This page deliberately does not repeat a version number; the Releases page and `CHANGELOG.md` are the canonical sources.

To work from a snapshot, check out its tag instead of `main`:

```bash
git clone https://github.com/yeongseon/azure-functions-cookbook-python.git
cd azure-functions-cookbook-python
git fetch --tags
git checkout <tag>   # for example, the tag shown as "Latest" on the Releases page
```

## What a snapshot gives you

For a given tag you get:

- the recipe source and docs exactly as they were at that tag;
- the supported Python range declared in `pyproject.toml` at that tag (currently `>=3.11,<3.15`; CI runs the test suite on 3.11 through 3.14);
- the toolkit and Azure Functions dependency bounds recorded in that tag's `pyproject.toml` and each recipe's own `pyproject.toml`/`requirements.txt`. CI also installs the minimum declared dependency floors (`constraints-min.txt`) on the lowest supported Python.

A snapshot is not a support contract for your deployment, and it does not freeze the packages your recipe resolves later unless you pin them yourself.

## What is verified, and what is not

Verification comes in distinct levels. A higher level is not implied by a lower one.

| Level | What it covers | Where it runs |
|---|---|---|
| Static and generated-artifact checks | Linting, type checking, recipe metadata, generated README/index tables, docs build, security manifest and dependency policy checks | Pull-request CI (`Test and Coverage`, docs, security workflows) and, for dependency policy, tag verification |
| Recipe unit tests and import checks | Each recipe's own `tests/` suite, plus library tests across Python 3.11-3.14 | Pull-request CI (`recipe-tests`, `test`) |
| Local Functions host with Azurite | A small set of recipes is started on a real Functions Core Tools host with Azurite and called over HTTP | Pull-request CI (`host-smoke`); currently the HTTP hello recipe and the validated OpenAPI/logging CRUD recipe |
| Pre-merge toolkit compatibility | Host-backed validation/OpenAPI/logging, DB and LangGraph endpoint scenarios on the pull-request checkout with the exact pins in `constraints-min.txt`; run only for integration-sensitive paths and aggregated by `ci-required` | Pull-request CI (`toolkit-compat`); see [Testing](testing.md#pre-merge-toolkit-compatibility-gate) |
| Toolkit regression matrix | Cookbook smoke and e2e tiers against released toolkit packages and against sibling repositories' `main` | `E2E Toolkit Matrix` workflow (scheduled, manual, and after sibling releases) |
| Real Azure deployment | Behavior that only exists in a deployed app (identity/RBAC, edge limits, host-enforced function keys) | **Not run by this repository's CI.** Treat it as unverified unless a recipe documents otherwise. |

Tag verification (`tag-verification.yml`) additionally builds the repository package, checks it declares the Python range, installs it cleanly on Python 3.11, and requires that Python 3.10 rejects it. That verifies the packaging metadata of the snapshot, not that any recipe works in Azure.

Do **not** read "CI passed" as "Azure-certified" or "production-ready". Passing CI means the checks in the table above passed.

A snapshot tells you what was verified, not what to add before calling a recipe production-like. A
reference path for that question (edge, caller and resource identity, observability, reliability) is tracked in
[issue #352](https://github.com/yeongseon/azure-functions-cookbook-python/issues/352); it is not published yet, so
this page does not link to a guide that does not exist.

## How to judge a recipe

For each recipe, look at:

| Question | Where to look |
|---|---|
| How hard is it? | The difficulty in the recipe table in the [README](https://github.com/yeongseon/azure-functions-cookbook-python#recipes) and `difficulty` in its `recipe.yaml`. Difficulty describes the code, not production readiness. |
| What does it depend on? | The recipe's `pyproject.toml` and `requirements.txt`; see also [Toolkit usage by recipe](toolkit-usage.md). |
| What does it need locally and in the cloud? | The recipe's `README.md` (run steps, settings) and any `local.settings.json.example`, `main.bicep` or `main.tf` it ships. |
| How was it verified? | `verification` in its `recipe.yaml` (`docs`, `unit`, `func-host`, `azure`), listed per recipe in [Toolkit usage by recipe](toolkit-usage.md). |
| Is its HTTP surface safe to expose? | [Anonymous endpoint classification](anonymous-endpoints.md). |

## Commits and releases in this repository

Release Please decides versions from conventional commit titles on `main`, and nothing is released by hand. Only user-facing types appear in release notes and cut a release:

- `feat` adds a minor release, `fix` a patch, and `perf`/`revert` appear in the changelog; a breaking change uses `!`.
- `docs`, `refactor`, `style`, `test`, `ci`, `chore` and `build` are hidden in the changelog (`release-please-config.json`), so a typo-only `docs:` change does not by itself cut a release.
- A new recipe, capability or navigation surface that readers should find in a snapshot should use a user-facing type such as `feat(...)`.
- For a major recipe addition, the GitHub Release notes should name the recipe and link its docs page so readers can find it from the snapshot; check this when reviewing the Release PR. Notes are presentation only, and Release Please still decides the version.

Do not edit version strings, `CHANGELOG.md` or the Release Please manifest; see the [Release Process](release_process.md).
