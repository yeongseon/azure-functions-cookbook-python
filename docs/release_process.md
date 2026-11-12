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
