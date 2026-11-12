# Early snapshot tags (v0.1.x and v0.2.0)

This page records an audit of the earliest tags of this repository. It exists so nobody has to
reverse-engineer why `v0.1.0`, `v0.1.1` and `v0.1.3` have a Git tag but no
[GitHub Release](https://github.com/yeongseon/azure-functions-cookbook-python/releases).

The cookbook is a collection of runnable recipes. It is **not published to PyPI**, so a missing GitHub
Release says nothing about the availability of a package, and a GitHub Release is never evidence of
distribution or of Azure certification. See [Versions, snapshots, and verification](snapshots-and-verification.md)
for what a snapshot is and what CI verifies.

The audit was read-only (`git tag`, `git ls-remote --tags`, `git show`, `gh release list`, `gh run list`).
No tag or GitHub Release was created, moved or deleted, and no version or changelog was edited.

## Summary

| Tag | Commit | Classification | GitHub Release |
|---|---|---|---|
| `v0.1.0` | `def1417d253d` (shared with `v0.1.1`) | **Tag-only milestone**: the tagged source declares `0.1.1`, not `0.1.0` | none |
| `v0.1.1` | `def1417d253d` | **Early snapshot**; a retrospective Release is possible (see below) | none |
| `v0.1.2` | `1b6d12434914` | Snapshot with a Release | yes (2026-03-21) |
| `v0.1.3` | `3c1c37aac9bb` | **Tag-only, out of order**: created on 2026-07-18, after `v0.2.0` was released | none |
| `v0.2.0` | `c82e5bad05a1` | Snapshot with a Release; the tagged source still declares `0.1.2` | yes (2026-04-18) |

Everything from `v0.3.0` onward was cut by Release Please and has a tag, a Release, a `CHANGELOG.md`
entry and a matching `__version__`.

## Evidence

| Tag | Tag object | Tagged / commit date | `__version__` at the commit | Examples (`function_app.py`) | `CHANGELOG.md` at the commit |
|---|---|---|---|---|---|
| `v0.1.0` | annotated, `yeongseon`, 2026-03-14 | 2026-03-14 22:22 +0900 | `0.1.1` | 5 | has `[0.1.1]` and `[0.1.0] - 2026-03-08` |
| `v0.1.1` | annotated, `yeongseon`, 2026-03-14 | 2026-03-14 22:22 +0900 | `0.1.1` | 5 | has `[0.1.1] - 2026-03-14` |
| `v0.1.2` | lightweight | 2026-03-21 23:07 +0900 | `0.1.2` | 28 | has `[0.1.2] - 2026-03-21` |
| `v0.1.3` | annotated, `Sisyphus`, 2026-07-18 | 2026-07-18 20:03 +0900 | `0.1.3` | 77 | git-cliff style, includes "Bump version to 0.1.3" |
| `v0.2.0` | lightweight | 2026-04-18 01:06 UTC | `0.1.2` | 77 | none for `0.2.0` |

Further facts, each checked directly:

- `v0.1.0` and `v0.1.1` point at the same commit, `def1417d253d` ("build: bump version to 0.1.1"). The commit
  before it still declared `0.1.0`, so the `v0.1.0` tag does not describe a source tree that says `0.1.0`.
  The tag objects carry the same tagger time (2026-03-14 22:22:50 +0900).
- `v0.1.3` points at `3c1c37aac9bb` ("docs: update changelog"), a descendant of `v0.2.0`: `git rev-list --count v0.2.0..v0.1.3`
  is 51, and that range contains `d5c6a8a build: bump version to 0.1.3`. The tag was created by a different
  tagger on 2026-07-18, three months after `v0.2.0` shipped. Sorted by version it precedes `v0.2.0`, but by history
  it follows it.
- `v0.2.0` has a Release whose auto-generated notes link `v0.1.2...v0.2.0`, but `__version__` at its commit is
  `0.1.2`: that snapshot predates the Release Please setup that keeps the version sources in sync.
- At `v0.1.0`, `v0.1.1` and `v0.1.2` the repository had a `Publish to PyPI` workflow
  (`.github/workflows/release.yml`) that ran on `v*` tags. Its runs for `v0.1.0`, `v0.1.1` and `v0.1.2` all concluded
  `failure` (run ids 23088805476, 23088805518, 23381375999; the job recorded no steps). The workflow was removed in
  `6e5087a` ("chore: remove unused PyPI publish workflow"), and the `azure-functions-cookbook-python` project does not
  exist on PyPI. That is consistent with the project's contract: tags here are source snapshots, not distributions.
- CI definitions present at the tag: `v0.1.0` and `v0.1.1` only had the docs-deploy and PyPI-publish workflows
  (two test files under `tests/`, no CI workflow ran them at that commit). `v0.1.2` added the test, CodeQL,
  security and SBOM workflows; `v0.1.3` and `v0.2.0` also had `ci-smoke.yml`, whose definition references Azurite and
  `func start` (the run results of that workflow at those tags were not audited). No tag-verification workflow existed, and no workflow
  at these tags logs in to Azure or deploys (no `azure/login` or Functions publish step), so **no early snapshot is claimed to be Azure-certified or
  production-ready**; a CI definition existing at a tag is not proof that it passed.

## Decision for the maintainer

The audit supports the following, and nothing below has been executed:

| Tag | Proposed handling | Why |
|---|---|---|
| `v0.1.0` | Keep as a **tag-only** milestone. Do not create a Release. | Its commit declares `0.1.1`; a Release would describe a version the tagged source does not contain, and it would duplicate `v0.1.1`. |
| `v0.1.1` | **Optional** retrospective Release, text below. Otherwise keep tag-only. | The commit date, the `CHANGELOG.md` entry (`[0.1.1] - 2026-03-14`) and `__version__` agree, so the contents are verifiable. |
| `v0.1.3` | Keep as a **tag-only** milestone. Do not create a Release. | The tag post-dates `v0.2.0`; a Release created now would sort as newer than `v0.2.0` and risk being shown as the latest snapshot. |
| `v0.2.0` | No change. Document only. | A Release exists; the version mismatch is historical and tags are not rewritten. |

These classifications are recorded as verified historical exceptions so that new tag/Release discrepancies
are still visible (see issue #493). Whether to publish the optional `v0.1.1` Release is the maintainer's
decision; creating it is out of scope for this change.

### Proposed `v0.1.1` Release (not executed)

A Release created today gets today's publication date, so the notes state the original date and that the
entry is retrospective. `--verify-tag` makes the command fail instead of creating a tag, and `--latest=false`
keeps it from becoming the latest snapshot.

```bash
cat > /tmp/v0.1.1-notes.md <<'NOTES'
> GitHub recipe snapshot — not a PyPI package; no PyPI distribution exists for this project.
> This Release entry was added retrospectively for the existing tag `v0.1.1` (commit
> `def1417d253dcc4eaeca02cca06a0dbfa74bca54`, 2026-03-14). The tag was not moved.

### Added
- Unified tooling: Ruff (lint + format), pre-commit hooks, standardized Makefile
- MkDocs documentation overhaul with a GitHub Pages deploy workflow
- Translated README files (Korean, Japanese, Chinese)
- 5 runnable example projects with smoke tests

Verification: this tag predates the repository's CI test workflows; it is not certified on Azure.

**Full Changelog:** https://github.com/yeongseon/azure-functions-cookbook-python/compare/a410d14...v0.1.1
NOTES

gh release create v0.1.1 \
  --repo yeongseon/azure-functions-cookbook-python \
  --verify-tag --latest=false \
  --title "v0.1.1" \
  --notes-file /tmp/v0.1.1-notes.md
```

## Reproducing the audit

```bash
git fetch --tags origin
git ls-remote --tags origin                       # remote tag objects and dereferenced commits
git for-each-ref refs/tags --format='%(refname:short) %(objecttype) %(taggername) %(taggerdate:iso8601)'
gh release list --limit 100                        # which tags have a Release
git show v0.1.1:src/azure_functions_python_cookbook/__init__.py   # __version__ at a tag
git rev-list --count v0.2.0..v0.1.3                # history relation between tags
```
