from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import http.client
import json
from pathlib import Path

import pytest

from tools import release_notes as rn

CFG = rn.Config(
    repo="acme/pkg",
    owner_login="maint",
    legacy_repos=["acme/old-pkg"],
    non_human_logins={"agent-bot-user"},
    protected={"v1.0.0": ["Not published to PyPI"]},
)


@dataclass
class FakeGitHub:
    tags: list[tuple[str, str]] = field(
        default_factory=lambda: [
            ("v0.9.0", "2026-01-01T00:00:00Z"),
            ("v1.0.0", "2026-02-01T00:00:00Z"),
            ("v1.0.1", "2026-02-02T00:00:00Z"),
        ]
    )
    commits: dict[tuple[str, str], list[rn.Commit]] = field(default_factory=dict)
    prs: dict[int, tuple[str, bool]] = field(default_factory=dict)
    veterans: set[str] = field(default_factory=lambda: {"maint"})
    bodies: dict[str, str] = field(default_factory=dict)

    def releases(self) -> list[tuple[str, str]]:
        return self.tags

    def release_body(self, tag: str) -> str:
        return self.bodies[tag]

    def compare(self, base: str, head: str) -> list[rn.Commit]:
        return self.commits.get((base, head), [])

    def pr_authors(self) -> dict[int, tuple[str, bool]]:
        return self.prs

    def had_prior_contribution(self, login: str, before_tag: str) -> bool:
        return login in self.veterans

    def set_body(self, tag: str, body: str) -> None:
        self.bodies[tag] = body


def commit(sha: str, subject: str, login: str | None, trailer: str = "") -> rn.Commit:
    message = subject + (f"\n\n{trailer}" if trailer else "")
    return rn.Commit(sha=sha * 40, subject=subject, message=message, login=login)


RP_BODY = """## [1.0.1](https://github.com/acme/pkg/compare/v1.0.0...v1.0.1) (2026-02-02)


### Bug Fixes

* **cli:** reject empty suffix ([#12](https://github.com/acme/pkg/issues/12)) ([aaaaaaa](https://github.com/acme/pkg/commit/aaaaaaa))
"""


def test_patch_release_omits_owner_byline_and_contributor_section() -> None:
    gh = FakeGitHub(prs={12: ("maint", False)})
    body = rn.build_notes("v1.0.1", RP_BODY, gh, CFG)
    assert body.startswith("## v1.0.1 (2026-02-02)\n")
    assert "### Bug Fixes" in body
    assert "- **cli:** reject empty suffix (#12)" in body
    assert "by @maint" not in body
    assert "New Contributors" not in body
    assert "**Full Changelog**: https://github.com/acme/pkg/compare/v1.0.0...v1.0.1" in body
    assert body.rstrip().endswith(rn.MARKER)


def test_feature_release_orders_sections_and_omits_empty_ones() -> None:
    original = (
        "## [1.0.0](x) (2026-02-01)\n\n### Bug Fixes\n\n* fix a (#2)\n\n"
        "### Features\n\n* **api:** add b (#1)\n\n### Documentation\n\n* docs: c (#3)\n"
    )
    gh = FakeGitHub(prs={1: ("maint", False), 2: ("maint", False), 3: ("maint", False)})
    body = rn.build_notes("v1.0.0", original + "\nNot published to PyPI\n", gh, CFG)
    assert body.index("### Features") < body.index("### Bug Fixes")
    assert "### Performance" not in body and "### Breaking Changes" not in body
    assert "<details><summary>Documentation, maintenance and other changes (1)" in body
    assert "Not published to PyPI" in body


def test_breaking_change_keeps_upgrade_guidance() -> None:
    original = (
        "## What's Changed\n\n### Breaking\n- Drop v1 support (#5)\n\n"
        "### Upgrade\nRun `pip install -U pkg` and rename `foo` to `bar`.\n\n"
        "### Added\n- thing (#6)\n"
    )
    gh = FakeGitHub(prs={5: ("maint", False), 6: ("maint", False)})
    body = rn.build_notes("v1.0.1", original, gh, CFG)
    assert "### \u26a0\ufe0f Breaking Changes" in body
    assert body.index("Drop v1 support") < body.index("rename `foo` to `bar`")
    assert body.index("rename `foo`") < body.index("### Features")
    assert "#### Upgrade" in body  # keeps the original heading so existing anchors still resolve


def test_first_time_contributor_only_when_verified() -> None:
    gh = FakeGitHub(
        commits={
            ("v1.0.0", "v1.0.1"): [
                commit("a", "fix: handle x (#12)", "newbie"),
                commit("b", "fix: handle y (#13)", "maint"),
                commit("c", "chore(deps): bump z (#14)", "dependabot[bot]"),
                commit("d", "fix: agent tweak (#15)", "agent-bot-user"),
            ]
        },
        prs={12: ("newbie", False), 13: ("maint", False)},
    )
    body = rn.build_notes("v1.0.1", "### Bug Fixes\n- fix x (#12)\n- fix y (#13)\n", gh, CFG)
    assert "- @newbie made their first contribution in #12" in body
    assert "@maint made their first" not in body
    assert "dependabot" not in body and "agent-bot-user" not in body


def test_external_pr_author_is_credited_when_owner_squashes_pr() -> None:
    gh = FakeGitHub(
        commits={
            ("v1.0.0", "v1.0.1"): [
                commit("e", "feat: add integration (#42)", "maint"),
            ]
        },
        prs={42: ("external-dev", False)},
        veterans=set(),
    )
    body = rn.build_notes("v1.0.1", "### Features\n- add integration (#42)\n", gh, CFG)
    assert "(#42) by @external-dev" in body
    assert "@external-dev made their first contribution in #42" in body
    assert "by @maint" not in body
    assert "@maint made their first contribution" not in body


def test_owner_never_appears_as_new_contributor_even_without_history() -> None:
    gh = FakeGitHub(
        commits={
            ("v1.0.0", "v1.0.1"): [
                commit("e", "fix: correct issue (#42)", "maint"),
            ]
        },
        prs={42: ("maint", False)},
        veterans=set(),
    )
    body = rn.build_notes("v1.0.1", "### Bug Fixes\n- correct issue (#42)\n", gh, CFG)
    assert "New Contributors" not in body
    assert "by @maint" not in body


def test_bots_and_non_human_accounts_are_never_credited() -> None:
    gh = FakeGitHub(prs={1: ("app/dependabot", True), 2: ("agent-bot-user", False)})
    body = rn.build_notes("v1.0.1", "- bump a (#1)\n- tweak b (#2)\n", gh, CFG)
    assert " by @" not in body


def test_coauthor_credit_requires_noreply_address() -> None:
    gh = FakeGitHub(
        commits={
            ("v1.0.0", "v1.0.1"): [
                commit(
                    "a",
                    "fix: z (#20)",
                    "maint",
                    "Co-authored-by: Real <77+realperson@users.noreply.github.com>\n"
                    "Co-authored-by: Guess <someone@example.com>\n"
                    "Co-authored-by: Agent <12+agent-bot-user@users.noreply.github.com>",
                )
            ]
        },
        prs={20: ("maint", False)},
        veterans={"maint", "realperson"},
    )
    body = rn.build_notes("v1.0.1", "### Bug Fixes\n- z (#20)\n", gh, CFG)
    assert "(#20) by @realperson" in body
    assert "by @maint" not in body
    assert "someone" not in body and "agent-bot-user" not in body


def test_compare_only_release_is_reconstructed_and_labelled() -> None:
    gh = FakeGitHub(
        commits={
            ("v1.0.0", "v1.0.1"): [
                commit("a", "fix(core): tolerate empty input (#30)", "maint"),
                commit("b", "chore(main): release 1.0.1", "maint"),
            ]
        },
        prs={30: ("maint", False)},
    )
    original = "<!-- generated -->\n\n**Full Changelog**: https://github.com/acme/old-pkg/compare/v1.0.0...v1.0.1\n"
    body = rn.build_notes("v1.0.1", original, gh, CFG)
    assert "reconstructed from the commits in `v1.0.0...v1.0.1`" in body
    assert "**core:** tolerate empty input (#30)" in body
    assert "by @maint" not in body
    assert "release 1.0.1" not in body


def test_unrecoverable_release_says_so_instead_of_inventing() -> None:
    body = rn.build_notes(
        "v1.0.1", "**Full Changelog**: x/compare/v1.0.0...v1.0.1", FakeGitHub(), CFG
    )
    assert "No user-facing changes could be reconstructed" in body


def test_github_generated_notes_are_normalised_and_legacy_links_rewritten() -> None:
    original = (
        "Not published to PyPI\n\n## What's Changed\n"
        "* feat(x): add thing by @maint in https://github.com/acme/old-pkg/pull/7\n"
        "## New Contributors\n"
        "* @someone made their first contribution in https://github.com/acme/old-pkg/pull/8\n"
        "**Full Changelog**: https://github.com/acme/old-pkg/compare/v0.9.0...v1.0.0\n"
    )
    body = rn.build_notes("v1.0.0", original, FakeGitHub(prs={7: ("maint", False)}), CFG)
    assert "- **x:** add thing (#7)" in body
    assert "by @maint" not in body
    assert "old-pkg" not in body
    assert "@someone" not in body  # unverified claim is dropped, not repeated


def test_losing_a_pr_reference_or_protected_phrase_is_refused() -> None:
    assert rn.verify("- a (#1)\n- b (#2)", "- a (#1)", "v1.0.1", CFG)
    assert rn.verify("x", "## v1.0.0\n", "v1.0.0", CFG) == [
        "protected phrase missing: 'Not published to PyPI'"
    ]


def test_rendering_is_idempotent() -> None:
    gh = FakeGitHub(prs={12: ("maint", False), 13: ("maint", False)})
    original = (
        "### Features\n- feat: add a (#12)\n### Documentation\n- docs(x): b (#13)\n"
        "### Breaking\n- gone (#14)\n### Notes\nStatus: fine.\n"
    )
    once = rn.build_notes("v1.0.1", original, gh, CFG)
    twice = rn.build_notes("v1.0.1", once, gh, CFG)
    assert once == twice


def test_apply_is_skipped_once_standardised_and_backs_up_nothing_unneeded(
    capsys: pytest.CaptureFixture[str],
) -> None:
    gh = FakeGitHub(prs={12: ("maint", False)}, bodies={"v1.0.1": RP_BODY})
    args = argparse.Namespace(tag="v1.0.1", dry_run=False, force=False, backup=None)
    assert rn.cmd_apply(args, CFG, gh) == 0
    first = gh.bodies["v1.0.1"]
    assert rn.MARKER in first
    assert rn.cmd_apply(args, CFG, gh) == 0
    assert gh.bodies["v1.0.1"] == first
    assert "already standardized" in capsys.readouterr().out


def test_unverifiable_first_contribution_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    client = rn.GitHubApi("acme/pkg")

    def boom(method: str, path: str, payload: dict[str, object] | None = None) -> object:
        raise rn.GitHubError(f"{method} {path} -> HTTP 403")

    monkeypatch.setattr(client, "_request", boom)
    # API failure must never turn into "first contribution"
    assert client.had_prior_contribution("someone", "v1.0.0") is True


def test_cookbook_snapshot_notes_do_not_claim_pypi_publication() -> None:
    cfg = rn.Config(repo="acme/pkg", owner_login="maint", snapshot_only=True)
    gh = FakeGitHub(prs={12: ("maint", False)})
    first = rn.build_notes("v1.0.1", RP_BODY, gh, cfg)
    assert "**GitHub recipe snapshot**" in first
    assert "nothing is published to PyPI" in first
    assert "by @maint" not in first
    assert first.index("GitHub recipe snapshot") < first.index("### Bug Fixes")
    assert rn.build_notes("v1.0.1", first, gh, cfg) == first


# ---------------------------------------------------------------- GitHub REST client


class FakeTransport:
    """Route ``GitHubApi._request`` to canned responses keyed by path prefix."""

    def __init__(self, routes: dict[str, object]) -> None:
        self.routes = routes
        self.calls: list[tuple[str, str, dict[str, object] | None]] = []

    def __call__(self, method: str, path: str, payload: dict[str, object] | None = None) -> object:
        self.calls.append((method, path, payload))
        for prefix, value in self.routes.items():
            if path.startswith(prefix):
                if isinstance(value, Exception):
                    raise value
                if callable(value):
                    return value(path)
                return value
        raise rn.GitHubError(f"unrouted {method} {path}")


def api_with(
    routes: dict[str, object], monkeypatch: pytest.MonkeyPatch
) -> tuple[rn.GitHubApi, FakeTransport]:
    client = rn.GitHubApi("acme/pkg")
    transport = FakeTransport(routes)
    monkeypatch.setattr(client, "_request", transport)
    return client, transport


RELEASES = [
    {"tag_name": "v1.0.0", "published_at": "2026-02-01T00:00:00Z", "created_at": "x",
     "draft": False, "body": "old body"},
    {"tag_name": "v1.0.1", "published_at": None, "created_at": "2026-02-02T00:00:00Z",
     "draft": False, "body": None},
    {"tag_name": "v1.0.2", "published_at": None, "created_at": "2026-02-03T00:00:00Z",
     "draft": True, "body": "draft"},
]  # fmt: skip


def test_api_releases_skip_drafts_and_fall_back_to_created_at(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, transport = api_with({"/repos/acme/pkg/releases": RELEASES}, monkeypatch)
    assert client.releases() == [
        ("v1.0.0", "2026-02-01T00:00:00Z"),
        ("v1.0.1", "2026-02-02T00:00:00Z"),
    ]
    assert client.release_body("v1.0.0") == "old body"
    assert client.release_body("v1.0.1") == ""
    with pytest.raises(rn.GitHubError):
        client.release_body("v9.9.9")
    assert len(transport.calls) == 1  # release list is cached


def test_api_pages_follow_full_pages(monkeypatch: pytest.MonkeyPatch) -> None:
    def pages(path: str) -> list[int]:
        return list(range(100)) if path.endswith("page=1") else [1, 2]

    client, _ = api_with({"/x": pages}, monkeypatch)
    assert len(client._pages("/x?state=closed")) == 102


def test_api_compare_maps_commits_and_paginates(monkeypatch: pytest.MonkeyPatch) -> None:
    def raw(i: int, author: dict[str, object] | None, msg: str) -> dict[str, object]:
        return {"sha": f"{i:040d}", "commit": {"message": msg}, "author": author}

    def compare(path: str) -> dict[str, object]:
        if path.endswith("page=1"):
            return {"commits": [raw(i, {"login": "u"}, "fix: a\n\nbody") for i in range(100)]}
        return {
            "commits": [
                raw(100, {"login": "dep[bot]", "type": "Bot"}, "chore: b"),
                raw(101, None, ""),
            ]
        }

    client, _ = api_with({"/repos/acme/pkg/compare/": compare}, monkeypatch)
    commits = client.compare("v1.0.0", "v1.0.1")
    assert len(commits) == 102
    assert commits[0].subject == "fix: a" and commits[0].login == "u"
    assert commits[100].login_is_bot is True
    assert commits[101].subject == "" and commits[101].login is None


def test_api_pr_authors_only_merged_with_user(monkeypatch: pytest.MonkeyPatch) -> None:
    prs = [
        {"number": 1, "merged_at": "t", "user": {"login": "a", "type": "User"}},
        {"number": 2, "merged_at": "t", "user": {"login": "b[bot]", "type": "Bot"}},
        {"number": 3, "merged_at": None, "user": {"login": "c"}},
        {"number": 4, "merged_at": "t", "user": None},
    ]
    client, transport = api_with({"/repos/acme/pkg/pulls": prs}, monkeypatch)
    assert client.pr_authors() == {1: ("a", False), 2: ("b[bot]", True)}
    client.pr_authors()
    assert len(transport.calls) == 1


def test_api_prior_contribution_by_commit_pr_search_and_cache(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, transport = api_with(
        {
            "/repos/acme/pkg/commits/v1.0.0": {"commit": {"committer": {"date": "2026-02-01"}}},
            "/repos/acme/pkg/commits?author=old": [{"sha": "1"}],
            "/repos/acme/pkg/commits?author=prdev": [],
            "/repos/acme/pkg/commits?author=new": [],
            "/search/issues?q=repo%3Aacme": lambda p: {"total_count": 1 if "prdev" in p else 0},
        },
        monkeypatch,
    )
    assert client.had_prior_contribution("old", "v1.0.0") is True
    calls = len(transport.calls)
    assert client.had_prior_contribution("old", "v2.0.0") is True  # cached veteran
    assert len(transport.calls) == calls
    assert client.had_prior_contribution("prdev", "v1.0.0") is True
    assert client.had_prior_contribution("new", "v1.0.0") is False


def test_api_set_body_patches_release_by_id(monkeypatch: pytest.MonkeyPatch) -> None:
    client, transport = api_with(
        {"/repos/acme/pkg/releases/tags/v1.0.0": {"id": 77}, "/repos/acme/pkg/releases/77": {}},
        monkeypatch,
    )
    client.set_body("v1.0.0", "new")
    assert transport.calls[-1] == ("PATCH", "/repos/acme/pkg/releases/77", {"body": "new"})


class FakeResponse:
    def __init__(self, status: int, raw: str) -> None:
        self.status = status
        self._raw = raw

    def read(self) -> bytes:
        return self._raw.encode()


class FakeConnection:
    seen: list[tuple[str, str, str | None, dict[str, str]]] = []
    response = FakeResponse(200, "{}")

    def __init__(self, host: str, timeout: int) -> None:
        self.closed = False

    def request(self, method: str, path: str, body: str | None, headers: dict[str, str]) -> None:
        FakeConnection.seen.append((method, path, body, headers))

    def getresponse(self) -> FakeResponse:
        return FakeConnection.response

    def close(self) -> None:
        self.closed = True


def test_request_sends_auth_and_parses_json(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GH_TOKEN", "tok")
    monkeypatch.setattr(http.client, "HTTPSConnection", FakeConnection)
    FakeConnection.seen = []
    FakeConnection.response = FakeResponse(200, '{"ok": true}')
    client = rn.GitHubApi("acme/pkg")
    assert client._request("PATCH", "/p", {"a": 1}) == {"ok": True}
    method, path, body, headers = FakeConnection.seen[0]
    assert (method, path, body) == ("PATCH", "/p", '{"a": 1}')
    assert headers["Authorization"] == "Bearer tok"


def test_request_without_token_empty_body_and_http_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("GH_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.setattr(http.client, "HTTPSConnection", FakeConnection)
    FakeConnection.seen = []
    FakeConnection.response = FakeResponse(200, "")
    client = rn.GitHubApi("acme/pkg")
    assert client._request("GET", "/p") is None
    assert "Authorization" not in FakeConnection.seen[0][3]
    FakeConnection.response = FakeResponse(404, "{}")
    with pytest.raises(rn.GitHubError, match="HTTP 404"):
        client._request("GET", "/p")


def test_get_caches_responses(monkeypatch: pytest.MonkeyPatch) -> None:
    client, transport = api_with({"/p": {"v": 1}}, monkeypatch)
    assert client._get("/p") == {"v": 1} and client._get("/p") == {"v": 1}
    assert len(transport.calls) == 1


# ---------------------------------------------------------------- config + parsing edges


def test_config_load_reads_all_fields(tmp_path: Path) -> None:
    path = tmp_path / "cfg.json"
    path.write_text(
        json.dumps(
            {
                "repo": "acme/pkg",
                "owner_login": "maint",
                "snapshot_only": True,
                "legacy_repos": ["acme/old"],
                "non_human_logins": ["Bot-User"],
                "protected": {"v1": ["keep"]},
                "annotations": {"v1": {"notes": ["a", "b"]}},
            }
        ),
        encoding="utf-8",
    )
    cfg = rn.Config.load(path)
    assert cfg.snapshot_only is True and cfg.owner_login == "maint"
    assert cfg.non_human_logins == {"bot-user"}
    assert cfg.protected == {"v1": ["keep"]} and cfg.annotations == {"v1": {"notes": ["a", "b"]}}


@pytest.mark.parametrize(
    ("heading", "expected"),
    [
        ("Highlights", ("highlights", None)),
        ("New Contributors", ("skip", None)),
        ("Upgrade notes", ("upgrade", None)),
        ("Notes", ("notes", None)),
        ("Breaking changes", ("items", "Breaking Changes")),
        ("Features", ("items", "Features")),
        ("Bug Fixes", ("items", "Bug Fixes")),
        ("Performance", ("items", "Performance")),
        ("Reverts", ("items", "Reverts")),
        ("Documentation", ("items", "Documentation")),
        ("Something else", ("items", None)),
    ],
)
def test_classify_heading(heading: str, expected: tuple[str, str | None]) -> None:
    assert rn._classify_heading(heading) == expected


def test_parse_item_variants() -> None:
    gh_style = rn.parse_item("Add thing by @someone in https://github.com/acme/pkg/pull/9", None)
    assert gh_style.prs == [9] and gh_style.title == "Add thing"
    bang = rn.parse_item("feat(api)!: drop v1 (#4)", None)
    assert bang.section == "Breaking Changes" and bang.title == "**api:** drop v1"
    plain = rn.parse_item("perf: faster (#5)", rn.OTHER)
    assert plain.section == "Performance"
    sha = rn.parse_item("tidy ([abcdef1](https://github.com/acme/pkg/commit/abcdef1))", None)
    assert sha.shas == ["abcdef1"] and sha.section == rn.OTHER


def test_parse_body_handles_details_rules_nested_headings_and_extras() -> None:
    body = (
        "## v1.0.0 (2026-02-01)\n\n---\n\nIntro paragraph\n\n"
        "### Highlights\n\nBig thing\n\n#### Sub heading\n\ndetail\n\n"
        "### Features\n\n- a (#1)\n  continuation line\n<details>\n- b (#2)\n</details>\n"
        "**Full Changelog**: https://github.com/acme/pkg/compare/v0.9.0...v1.0.0\n"
        "### New Contributors\n- @x made their first contribution\n"
    )
    parsed = rn.parse_body(body)
    assert parsed.date == "2026-02-01"
    assert parsed.notes == ["Intro paragraph"]
    assert parsed.highlights == ["Big thing", "", "#### Sub heading", "", "detail"]
    assert parsed.compare_prev == "v0.9.0"
    assert [i.prs for i in parsed.items] == [[1], [2]]
    assert parsed.items[0].extra == ["  continuation line"]


# ---------------------------------------------------------------- attribution edges


def test_coauthors_only_human_noreply_trailers() -> None:
    message = (
        "x\n\nCo-authored-by: A <12+alice@users.noreply.github.com>\n"
        "Co-authored-by: B <b@example.com>\n"
        "Co-authored-by: C <agent-bot-user@users.noreply.github.com>\n"
    )
    assert rn.coauthors(message, CFG) == ["alice"]


def test_attribute_credits_external_via_commit_and_trailer() -> None:
    item = rn.parse_item("fix: thing (#7)", None)
    commits = [
        commit("a", "fix: thing (#7)", "ext", "Co-authored-by: P <5+pair@users.noreply.github.com>")
    ]
    rn.attribute(item, commits, {}, CFG)
    assert item.authors == ["ext", "pair"]
    assert item.line().endswith("by @ext, @pair")

    keyed = rn.parse_item("fix: other", None)
    rn.attribute(keyed, [commit("b", "fix: other", "ext2")], {}, CFG)
    assert keyed.authors == ["ext2"]

    bot = rn.parse_item("fix: thing (#7)", None)
    rn.attribute(bot, commits, {7: ("dep[bot]", True)}, CFG)
    assert "dep[bot]" not in bot.authors


def test_new_contributors_uses_pr_authors_coauthors_and_no_prev() -> None:
    gh = FakeGitHub()
    commits = [
        commit("a", "chore(main): release 1.0.1", "ext"),
        commit("b", "fix: x (#3)", None, "Co-authored-by: P <5+pair@users.noreply.github.com>"),
        commit("c", "fix: y", "direct"),
    ]
    firsts = rn.new_contributors(commits, gh, "v1.0.0", CFG, {3: ("prauthor", False)})
    assert firsts == [("prauthor", "#3"), ("pair", "#3"), ("direct", "c" * 7)]
    assert rn.new_contributors(commits, gh, None, CFG) == []


# ---------------------------------------------------------------- rendering + orchestration


def test_render_legacy_repo_links_reconstruction_and_new_contributors() -> None:
    parsed = rn.parse_body("Moved from https://github.com/acme/old-pkg/issues/1\n")
    body = rn.render("v1.0.1", parsed, CFG, "v1.0.0", [("newbie", "#9")], "v1.0.0...v1.0.1")
    assert "github.com/acme/pkg/issues/1" in body and "old-pkg" not in body
    assert "reconstructed from the commits in `v1.0.0...v1.0.1`" in body
    assert "- @newbie made their first contribution in #9" in body


def test_render_empty_release_explains_nothing_to_show() -> None:
    body = rn.render("v1.0.1", rn.Parsed(), CFG, None, [])
    assert "No user-facing changes could be reconstructed" in body
    assert "Full Changelog" not in body


def test_render_unclassified_items_use_changes_section() -> None:
    parsed = rn.Parsed(items=[rn.Item(title="misc")])
    body = rn.render("v1.0.1", parsed, CFG, "v1.0.0", [])
    assert "### Changes" in body and "<details>" not in body


def test_previous_tag_orders_by_version_and_falls_back_to_compare_link() -> None:
    releases = [("v1.10.0", ""), ("v1.2.0", ""), ("v1.9.0", "")]
    assert rn.previous_tag("v1.10.0", releases) == "v1.9.0"
    assert rn.previous_tag("v1.2.0", releases) is None
    assert rn.previous_tag("v2.0.0", releases, rn.Parsed(compare_prev="v1.10.0")) == "v1.10.0"


def test_compare_only_body_is_reconstructed_from_commits() -> None:
    gh = FakeGitHub(
        commits={
            ("v1.0.0", "v1.0.1"): [
                commit("a", "chore(main): release 1.0.1", "maint"),
                commit("b", "feat: add widget (#20)", "maint"),
            ]
        },
        prs={20: ("maint", False)},
    )
    body = rn.build_notes(
        "v1.0.1",
        "**Full Changelog**: https://github.com/acme/pkg/compare/v1.0.0...v1.0.1\n",
        gh,
        CFG,
        published="2026-02-02T10:00:00Z",
    )
    assert body.startswith("## v1.0.1 (2026-02-02)")
    assert "- add widget (#20)" in body and "release 1.0.1" not in body
    assert "reconstructed from the commits" in body


def test_annotations_are_appended_once() -> None:
    parsed = rn.Parsed(notes=["existing"])
    blocks = {"notes": ["Clarified"], "highlights": ["Shiny"]}
    rn.apply_annotations(parsed, blocks)
    rn.apply_annotations(parsed, blocks)
    assert parsed.notes == ["existing", "", "Clarified"]
    assert parsed.highlights == ["Shiny"]


def test_build_notes_refuses_when_protected_phrase_or_reference_would_be_lost() -> None:
    cfg = rn.Config(repo="acme/pkg", protected={"v1.0.1": ["MUST KEEP"]})
    gh = FakeGitHub()
    with pytest.raises(ValueError, match="protected phrase missing"):
        rn.build_notes("v1.0.1", RP_BODY, gh, cfg)
    problems = rn.verify(
        "* thing ([#99](u)) ([abcdef1](https://github.com/acme/pkg/commit/abcdef1))\n"
        "* tidy ([1234567](https://github.com/acme/pkg/commit/1234567))\n",
        "nothing here",
        "v1.0.1",
        CFG,
    )
    assert "lost PR reference #99" in problems
    assert "lost commit reference 1234567" in problems


# ---------------------------------------------------------------- CLI


def write_cfg(tmp_path: Path) -> Path:
    path = tmp_path / "cfg.json"
    path.write_text(json.dumps({"repo": "acme/pkg", "owner_login": "maint"}), encoding="utf-8")
    return path


def patch_api(monkeypatch: pytest.MonkeyPatch, gh: FakeGitHub) -> None:
    monkeypatch.setattr(rn, "GitHubApi", lambda repo: gh)


def test_cmd_apply_dry_run_backup_and_idempotency(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    gh = FakeGitHub(bodies={"v1.0.1": RP_BODY}, prs={12: ("maint", False)})
    patch_api(monkeypatch, gh)
    cfg = str(write_cfg(tmp_path))
    assert rn.main(["--config", cfg, "apply", "v1.0.1", "--dry-run"]) == 0
    assert "### Bug Fixes" in capsys.readouterr().out
    assert gh.bodies["v1.0.1"] == RP_BODY

    backup = tmp_path / "backup"
    assert rn.main(["--config", cfg, "apply", "v1.0.1", "--backup", str(backup)]) == 0
    assert rn.MARKER in gh.bodies["v1.0.1"]
    saved = json.loads((backup / "v1.0.1.json").read_text(encoding="utf-8"))
    assert saved == {"tagName": "v1.0.1", "body": RP_BODY}

    capsys.readouterr()
    assert rn.main(["--config", cfg, "apply", "v1.0.1"]) == 0
    assert "already standardized" in capsys.readouterr().out
    assert rn.main(["--config", cfg, "apply", "v1.0.1", "--force"]) == 0


def test_cmd_render_from_release_and_body_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    gh = FakeGitHub(bodies={"v1.0.1": RP_BODY}, prs={12: ("maint", False)})
    patch_api(monkeypatch, gh)
    cfg = str(write_cfg(tmp_path))
    assert rn.main(["--config", cfg, "render", "v1.0.1"]) == 0
    from_release = capsys.readouterr().out
    body_file = tmp_path / "body.md"
    body_file.write_text(RP_BODY, encoding="utf-8")
    assert rn.main(["--config", cfg, "render", "v1.0.1", "--body-file", str(body_file)]) == 0
    assert capsys.readouterr().out == from_release


def test_cmd_preview_writes_outputs_and_reports_failures(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    patch_api(monkeypatch, FakeGitHub(prs={12: ("ext", False)}))
    backup = tmp_path / "backup"
    backup.mkdir()
    (backup / "v1.0.1.json").write_text(
        json.dumps({"tagName": "v1.0.1", "body": RP_BODY, "publishedAt": "2026-02-02T00:00:00Z"}),
        encoding="utf-8",
    )
    out = tmp_path / "out"
    cfg = str(write_cfg(tmp_path))
    assert rn.main(["--config", cfg, "preview", "--backup", str(backup), "--out", str(out)]) == 0
    assert (out / "v1.0.1.md").exists() and (out / "v1.0.1.diff").exists()
    assert "credits: @ext" in (out / "SUMMARY.txt").read_text(encoding="utf-8")

    strict = tmp_path / "strict.json"
    strict.write_text(
        json.dumps({"repo": "acme/pkg", "protected": {"v1.0.1": ["MUST KEEP"]}}), encoding="utf-8"
    )
    capsys.readouterr()
    assert (
        rn.main(["--config", str(strict), "preview", "--backup", str(backup), "--out", str(out)])
        == 1
    )
    assert "FAIL v1.0.1" in capsys.readouterr().out
