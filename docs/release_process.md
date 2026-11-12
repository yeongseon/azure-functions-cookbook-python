# Release Process

This repository is a content/examples project. A release produces a **tag**, a **GitHub Release**
and a **changelog entry** for consumers to pin against. Nothing is published to PyPI.

Releases are automated by [Release Please](https://github.com/googleapis/release-please).

## GitHub Release notes for recipe snapshots

The released artifact is the **tagged cookbook source and recipe inventory**, not a PyPI package.
After Release Please publishes a GitHub Release, a non-blocking presentation job formats
the existing Release body with `tools/release_notes.py`. The job does not change the
version, tag, source archive, `CHANGELOG.md`, or any Python distribution. Every formatted
Release prominently states **GitHub recipe snapshot — nothing is published to PyPI**.

Keep notes concise and useful to recipe readers: highlight noteworthy new recipes and
behavior changes, actionable breaking migration steps, and the exact commit comparison.
Omit empty sections and routine maintenance chatter. The owner `@yeongseon` does
not need a repeated `by @yeongseon` byline. Use `by @username` for verified
**external human contributors**, including externally authored squash-merged PRs;
include `New Contributors` only on a verified first external contribution, never for
bots or the owner.

The recipe verification level must not be exaggerated: GitHub tags are reproducible
snapshots but do not by themselves certify a recipe on Azure. See
[snapshot and verification guidance](snapshots-and-verification.md).

Preview an existing Release without changing it:

```bash
GH_TOKEN="$(gh auth token)" python3 -m tools.release_notes apply v0.5.0 --dry-run
```


**Do not hand-edit** `src/azure_functions_python_cookbook/__init__.py` version strings, `CHANGELOG.md`,
or `.release-please-manifest.json`. Release Please maintains all three.

---

## Step 1: Merge Conventional Commits

| Commit | Bump |
|---|---|
| `fix:` | patch |
| `feat:` | minor |
| `feat!:` / `fix!:` / `BREAKING CHANGE:` footer | minor while pre-1.0 |

---

## Step 2: Merge the Release PR

Release Please keeps an open **Release PR** titled like `chore(main): release X.Y.Z` containing the
version bump and the changelog entry. Merging it tags the release commit and publishes the GitHub
Release.

`release-please.yml` runs with `RELEASE_PLEASE_TOKEN` (a fine-grained PAT) rather than the default
`GITHUB_TOKEN`, so the required status checks run on the Release PR. The PAT expires; regenerate it and
update the secret before it does, or no Release PR will appear.

---

## Recipe snapshot cadence

This repository intentionally publishes **GitHub source/recipe snapshots**,
not Python distributions on PyPI. A snapshot signals a coherent, pinned
set of recipe examples, with evidence appropriate to the examples.
Routine PRs can merge without triggering a release.

**Default:** aim for **at most one planned snapshot every two weeks**,
when a meaningful set of recipes is ready and tested. There is no
obligation to publish if no recipe-facing changes are ready. The maintainer
decides when to merge Release Please's open Release PR.

**Out-of-cycle exception:** a verified unsafe example, harmful deployment
guidance, or a widely broken released snapshot can be fixed sooner. Briefly
record the affected examples, impact and reason for early release in the
Release PR. Do not create an automatic minimum wait time or publish a
placeholder release to meet a calendar target.

Before merging, compare the candidate with the last actual GitHub recipe
snapshot, check the recipe index and dependency/runtime constraints, and
verify the available test and Azure evidence without claiming Azure
certification from a tag alone. Preserve existing snapshot/version/tag
history. Release Please remains the only owner of version, tag, release
PR and `CHANGELOG.md`; no PyPI publishing is introduced.

If the dependency ranges changed since the last recording, refresh the
[compatibility evidence](compatibility.md) from a real CI run on the candidate
manifests (`python scripts/gen_compat_table.py --record RUN_ID`); the table
labels older evidence as such rather than hiding it.

---

## Snapshot audit

`python -m tools.audit_snapshots` is a **read-only** audit of the tagged GitHub recipe snapshots. It
never creates, moves or deletes a tag or Release, never edits a version, `CHANGELOG.md` or the
release manifest, and never looks at PyPI: the cookbook is not a PyPI package, and a GitHub Release is
not treated as proof of distribution or of Azure certification. Release Please remains the only owner
of versions, tags, Releases and `CHANGELOG.md`.

For each `vX.Y.Z` tag it prints a deterministic result, with tag/commit/compare links for every failure:

| Check | Meaning |
|---|---|
| `tag-name`, `ancestry` | the tag is plain semver and its commit is reachable from `origin/main` |
| `duplicate-commit`, `tag-order` | tags map to distinct commits that follow version order |
| `release-exists`, `release-draft`, `release-orphan` | each tag has a published GitHub Release, and no Release lacks a tag |
| `source-version`, `changelog-entry` | `__version__`, the Release Please manifest and `CHANGELOG.md` agree with the tag (manifest and changelog only for snapshots cut by Release Please) |
| `head-version` | on the checked-out commit (so on a Release PR, before it is merged) `__version__`, the manifest and the newest `CHANGELOG.md` entry agree |
| `recipe-inventory`, `recipe-index` | `recipes.json` at the tag parses; the current generated recipe index and README tables have not drifted |
| `verification-level` (info) | which CI definitions existed at the tag; this is not a claim that every run passed or that any recipe is Azure-certified |

It also reports, informationally, whether commits since the newest tag include user-facing
Conventional Commit types (a snapshot is expected) or only `docs`/`ci`/`chore`/... changes (no snapshot is
needed). A content-only change never needs a snapshot.

```bash
git fetch --tags origin
python -m tools.audit_snapshots --ref origin/main                 # needs the GitHub CLI for Release data
python -m tools.audit_snapshots --ref origin/main --skip-releases # git-only checks
python -m tools.audit_snapshots --format json                     # machine-readable
```

Exit status is `0` when every finding is either passing or excepted, `1` for an unexcepted failure, and
`2` when the audit itself could not run (for example `gh` could not list Releases).

### Historical exceptions

Verified historical cases live in
[`.github/release-audit-exceptions.json`](https://github.com/yeongseon/azure-functions-cookbook-python/blob/main/.github/release-audit-exceptions.json).
An exception is pinned to the tag's **commit SHA** and to **specific checks**, with a classification,
reason, evidence links and the tracking issue. If a tag moves, or a different kind of defect appears on
the same tag, the finding is reported again; entries that no longer match anything are listed as stale.
Add an entry only for verified history, never to silence a new release.

### Where it runs

The `Snapshot audit` workflow runs the audit on pull requests that touch the audit, the exception registry,
the recipe index or the version sources (so a Release PR is checked before it is merged), **when a GitHub Release is published**, daily, and on demand. A published Release
with a bad version/changelog, a tag that never received a Release (no release event fires for that, so
the daily run catches it) or recipe-index drift fails the run and writes the report to the job summary.
The workflow has `contents: read` only and uses the built-in `github.token` solely to list Releases.
Its result is a signal about repository metadata, not a publication gate.

### Fixing a discrepancy (fix-forward)

Never rewrite history. Correct the cause on `main` with a Conventional Commit so Release Please cuts the next
snapshot: a `fix:` for a user-facing problem, or `docs:`/`ci:` for metadata that needs no snapshot. If a
Release is missing for a *new* tag, create or repair it with the maintainer's GitHub release tooling for that
same tag and verify that it targets the tag's commit; do not create a replacement tag or version. A historical
tag that is deliberately tag-only is recorded in the exception registry instead. Only `Added`, `Fixed`,
breaking and other user-facing items appear in release notes; audit statuses (`excepted`, `stale`, ...)
are for maintainers and never appear there.

---

## What is no longer used

| Retired | Replacement |
|---|---|
| `make release-patch` / `release-minor` / `release-major` / `release` | merge the Release PR |
| `make changelog` / `make commit-changelog` (git-cliff) | Release Please writes `CHANGELOG.md` |
| `make tag-release` | Release Please creates the tag |
| `cliff.toml` | `release-please-config.json` |

---

## Related

- [CHANGELOG.md](https://github.com/yeongseon/azure-functions-cookbook-python/blob/main/CHANGELOG.md)
- [Release Please](https://github.com/googleapis/release-please)
