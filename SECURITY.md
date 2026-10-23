# Security policy

Report suspected vulnerabilities privately through this repository's GitHub
security reporting channel. Do not include credentials, model prompts or user
data in public issues or scanner artifacts.

## Reporting a vulnerability

Use [GitHub private vulnerability reporting](https://github.com/yeongseon/azure-functions-cookbook-python/security/advisories/new)
or email yeongseon.choe@gmail.com. Include a description, reproduction steps,
impact assessment and any suggested mitigation, without credentials or private
data. Initial response is targeted within 48 hours, with a status update within
7 days. The latest release is supported; older releases are not.

## Scope and gates

This cookbook distributes runnable source examples, not a PyPI runtime package.
Release Please creates a tag and GitHub Release; there is no publish gate to
extend. `tag-verification.yml` now depends on a reusable resolved dependency
policy job before its existing build/install checks. This verifies a tagged
snapshot **after tagging**, not before Release Please creates the GitHub Release.
A failed verification means the snapshot is not security-verified; fix forward
or retry a transient audit error on the same unchanged tag.

| Surface | Where | Policy |
| --- | --- | --- |
| Existing src Bandit, pinned Semgrep, CodeQL, SPDX SBOM | Existing workflows | Unchanged |
| All runnable examples, Python helper scripts/tools | `security.yml` recipe-security job | Exact inventory, manifest, Bandit and settings/structure policy block the job |
| Root runtime closure and every generated recipe requirements set | PR/main `security.yml`, scheduled/manual `dependency-audit.yml` | Visible findings and policy evaluation, reporting-only to avoid unrelated advisories blocking every PR |
| Same resolved dependency closures | `tag-verification.yml` dependency prerequisite | Blocking: all unexcepted known advisories, any missing/invalid/skipped audit |
| Real paid-AI host metadata | `security.yml` paid-ai-host job; opt-in local test | Core Tools + Azurite; no cloud/model credentials |

The existing `ci-required` aggregation, job names, test matrix and 95% coverage
floor are unchanged. New jobs do not silently become branch-protection-required
checks; existing full-suite tests include negative manifest/policy regressions.
Scheduled development dependency reporting remains separate from runtime policy.
Existing SPDX generation remains unchanged; dependency evidence inventories
resolved packages and does not claim an SPDX document for every recipe.

Run additive tooling using the repository Python 3.11 environment:

```bash
make security-manifest SECURITY_PYTHON="hatch run python"
make security-static SECURITY_PYTHON="hatch run python"
make security-dependencies-report SECURITY_PYTHON="hatch run python"
```

Omit `--reporting` for blocking dependency evaluation. Dependency resolution uses
isolated temporary environments and pinned `pip-audit==2.10.1`, not the contributor
environment's development packages. Root `project.dependencies` is currently
empty: its verified runtime closure is explicitly recorded as empty, not inferred
from a zero-file scanner result. Every recipe's requirements must exactly match
`scripts/gen_requirements.py` output from its pyproject; unique requirement sets
are resolved independently (not an incompatible cross-recipe union). Identical
sets share one audit result, with each recipe still represented in the report.

## Route-risk model

`security/recipe-security-manifest.json` classifies all runnable `function_app.py`
projects and their declared HTTP handlers, inherited blueprint auth and adapter
auth. Discovery mirrors generated requirements, recursively under `examples/`.
No example code is imported or executed. Zero projects, missing classifications,
unresolved auth, stale declarations or a paid-backend anonymous default fail.
Grouped recipe reasons describe differing route purposes where needed; concrete
handler auth is recorded separately. Auth is not globally banned from being
anonymous:

- `public-health` / `public-api-documentation`: deliberately public probes/docs;
  protected diagnostic/webhook routes keep their bindings.
- `auth-demonstration`: JWT/EasyAuth/multitenant/auth-level teaching examples keep
  anonymous bindings where their own authorization is the subject.
- `public-webhook-with-own-verification`: HMAC validation is its boundary.
- `local-demo-no-backend`: educational local HTTP surface, not production auth.
- `cloud-backend-demo` / `edge-auth-demonstration`: existing cloud demos retain
  behavior; isolate ingress/egress and apply authorization/quotas before deployment.
- `paid-backend`: the three direct paid-AI recipes require FUNCTION by default;
  explicit `COOKBOOK_PUBLIC_DEMO=true` is an intentional unsafe demo override.
- `protected` / `non-http`: function-key HTTP surfaces or event-only triggers.

Static adapter records represent declared adapter auth, not enumeration of every
library-generated route (notably intentionally public lightweight health).
Unknown future dynamic registration must be reviewed; this is not a whole-program
proof of Azure ingress. See [paid AI guidance](docs/paid-ai-security.md).

## Evidence, exceptions, and scanner failure

`PASS` means the stated policy completed; `FAIL` means findings violate policy.
`TOOL_ERROR` means execution/output/policy is unusable; `INCOMPLETE` means scope
or inventory is missing. Neither error nor incomplete is a clean pass. The tag
job blocks on every non-PASS result. All advisories block there, including unknown
severity; severity is informational, not an excuse to omit a known advisory.

`security/bandit-exceptions.json` entries match exact finding id/file/line;
`security/dependency-exceptions.json` entries match exact advisory id/package.
Every exception requires reason, owner, added date and expiry, no more than 90
days after addition. Expired/future-dated/malformed entries block evaluation.
Review before renewal; never use blanket package ignores. The MCP calculator
`B307` exception explicitly tracks #426; this change does not remediate that issue.
Other reviewed educational randomness, subprocess invocations and existing URL
integration risks remain visible with bounded exceptions.

Bandit ignores inline suppressions while scanning; a separate inventory rejects
any `# nosec` comment without an exact reviewed `INLINE_NOSEC` exception. Recipe
test directories are explicitly excluded from deployed Python scanning; their
assertions are tested by pytest. Generated Python under examples and requirements
helpers under scripts/tools are included.

The pinned Semgrep action uses repository-wide `p/python` scope, which includes
examples unless its own ignore configuration excludes them. Added evidence
records its outcome, but reports `INCOMPLETE` because the action does not expose
an exact analyzed-file inventory through its outputs. It never turns that into a
clean pass or masks action failure. Full Semgrep inventory/SARIF integration is a
follow-up, not a claim made by the action wrapper.

Offline Bicep checks inventory actual templates, flag explicit insecure TLS/HTTP
settings and classify explicit public networking as educational cloud exposure.
They do not infer missing deployment properties or provision Azure. Shell scripts
receive `bash -n` plus secret checks, not a claim of full ShellCheck coverage.
Settings templates and `.env*` files under examples are checked for real-looking
key/connection-string literals; placeholders and local emulator configuration are
allowed. Do not treat pattern matching as a complete secret detector.

Only allow-listed IDs, package/path inventory, line numbers, severity and counts
are persisted in ignored `security-results/**` JSON and Job Summary artifacts,
uploaded `if: always()`. Raw scanner code excerpts, advisory descriptions,
provider diagnostics and arbitrary exception text are discarded. Never upload
raw SDK/host logs with credentials. Review platform telemetry independently.

## Remaining deployment checks

Azure authorization failures, Entra/RBAC, Managed Identity token acquisition,
network isolation, actual cost/quotas and public-service configuration need a real
deployment review. Offline structure checks do not certify them. The cookbook's
existing cloud integration demos are not silently hardened by this issue.
