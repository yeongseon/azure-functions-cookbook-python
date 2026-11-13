# Stability and compatibility

This page defines the words the Cookbook uses for stability and says what this repository's own
CI backs for each documented integration path. It is local to this repository: it describes
what the checks here run, not what any other package promises.

## Terms

| Term | Meaning in this Cookbook |
|---|---|
| **Verified example** | A recipe whose `verification` level in `recipe.yaml` is `unit` or `func-host`, so a **required** CI job runs it (see [Verification levels](https://github.com/yeongseon/azure-functions-cookbook-python/blob/main/DESIGN.md#verification-levels)). Verified means "the checks named by that level passed", not "production-ready" and not "Azure-certified". |
| **Documented-only example** | `verification: docs`. The code and docs are reviewed and import-checked at most, but no recipe-local test suite or host run is required for it. |
| **Experimental integration** | An integration path that is documented but not exercised beyond import or unit level, or one the README Ecosystem table marks **Experimental** or **Planned**. Expect it to change or break when the upstream package changes. |
| **Package compatibility** | The dependency ranges the recipes declare (`pyproject.toml`, recipe `requirements.txt`) and the resolutions CI installs: latest compatible and the lowest declared floors (`constraints-min.txt`). It says which versions CI installed, not that every recipe was run against every version. |
| **Rolling 0.x** | The toolkit packages are declared as `>=X.Y,<1`, and this repository itself is released as `0.x` snapshots. A newer upstream `0.x` release may change behavior without a major version; the Cookbook finds out through the checks below, then raises the floor or fixes the recipe. |

The Cookbook makes **no SemVer promise** for recipe routes, settings, file layout or helper
modules. A snapshot is a pinned record of what was verified at that tag; see
[Versions, snapshots, and verification](snapshots-and-verification.md).

## What backs each integration path

| Integration path | Evidence in this repository | Status |
|---|---|---|
| Plain Azure Functions recipes with `verification: unit` | `recipe-tests` job runs each recipe's own `tests/` suite on Python 3.11 (`scripts/run_recipe_tests.py`); the library suite runs on Python 3.11-3.14 | **Tested** (unit level) |
| Hello HTTP and Full Stack CRUD API (OpenAPI, validation, logging, DB helpers) | `host-smoke` matrix starts a real Functions Core Tools v4 host with Azurite and calls the public route (Python 3.12) | **Tested** (local host) |
| Toolkit packages (`openapi`, `validation`, `logging`, `db`) against newest releases and sibling `main` | `E2E Toolkit Matrix` workflow: weekly schedule, manual dispatch and sibling-release dispatch. It is not a required pull-request check | **Tested**, off the PR path |
| Recipes with `verification: docs` | Repository-level tests under `tests/` may import or inspect them, but no required job runs them | **Unverified** beyond static checks |
| Durable Functions recipes | `tests/e2e/test_durable_examples.py` only imports them, because local Durable host startup is impractical in CI (see that file's docstring) | **Limited** (import only) |
| Queue and Blob Azurite examples | `tests/e2e/` runs a subset against Azurite in the toolkit matrix, not as a required PR check | **Limited** |
| Anything that needs a deployed Azure resource (identity/RBAC, Event Hubs, Cosmos DB, Service Bus, Azure OpenAI, edge limits, host-enforced keys) | No required job exercises a deployed resource and no recipe declares `azure` | **Unverified** |

Use each recipe's `verification` value and [Toolkit usage by recipe](toolkit-usage.md) to see
which row applies to the recipe you plan to copy.

## LangGraph recipes: where the limits apply

Five recipes use `azure-functions-langgraph` (`langgraph_agent`, `langgraph_rag_agent`,
`langgraph_tool_use`, `personal_langgraph_agent`, `servicebus_langgraph_agent`). Only `personal_langgraph_agent` is `func-host`; none is `azure`. The limits
below are the ones these recipes' code and READMEs expose; they are not a statement about
other uses of the package.

- **No checkpointer by default.** `langgraph_tool_use` persists nothing between requests;
  `langgraph_rag_agent` keeps history in a process-local dictionary (per worker, lost on restart or scale-out), not in a LangGraph checkpointer. Add a persistent checkpointer
  before relying on conversation memory.
- **`personal_langgraph_agent` memory modes.** The default `AGENT_MEMORY_MODE=memory` uses a
  process-local `InMemorySaver`. Blob mode (`AzureBlobCheckpointSaver`) is exercised only by the
  opt-in Azurite lane `tests/e2e/test_personal_agent_azurite.py`, which is part of the toolkit
  matrix, not a required PR check, and is not an Azure check. The recipe README states that its
  lock does not promise exactly-once tool effects.
- **`servicebus_langgraph_agent` is unit-level only.** It uses the adapter's Service Bus trigger,
  which that package documents as experimental, and pins `>=0.13.0,<0.14`. Offline tests call the
  generated handler with synthetic messages; no Functions host, Service Bus broker, lock expiry,
  dead-lettering or session behavior has been exercised. Its checkpointer is process-local.
- **No streaming in these recipes.** `personal_langgraph_agent` registers its graph with
  `stream=False`; streaming is not demonstrated or tested by any LangGraph recipe.
- **`langgraph_agent` does not call the compiled graph** from its HTTP handler; it returns a
  deterministic echo so it runs without model credentials. It shows registration, not execution.
- **Thread IDs are not authentication.** They separate checkpoints, not users.

## Breaking changes and deprecations

The process is sized for one maintainer and uses what already exists: Conventional Commit
titles, the Release PR, and the pull request template.

1. **Classify** using [Breaking-change classification](https://github.com/yeongseon/azure-functions-cookbook-python/blob/main/CONTRIBUTING.md#breaking-change-classification).
   A change to a documented route, required setting, authentication default or generated-app
   behavior can be breaking.
2. **Announce a deprecation** in the affected recipe's README and in a commit whose type
   appears in the changelog (`feat`, `fix`, `perf` or a breaking `!`). `docs:`, `chore:` and the other
   hidden types never reach the release notes, so a deprecation carried only by them would be
   invisible to snapshot readers.
3. **Remove or change incompatibly** no earlier than the next snapshot after the deprecation
   was published, with `!` or a `BREAKING CHANGE:` footer and the PR template's
   "Breaking-change impact" section filled in. Release Please then lists it in the Release PR
   notes.
4. **Exception:** a verified insecure example or materially misleading instructions can be
   corrected immediately; record the recipe and reason in the Release PR (see
   [recipe snapshot cadence](release_process.md#recipe-snapshot-cadence)).

Readers pin a snapshot tag (see [snapshots](snapshots-and-verification.md)) and read the GitHub
Release notes for the changes between tags.
