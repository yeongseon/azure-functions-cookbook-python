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

Use `make security-dependencies` for blocking dependency evaluation. Dependency resolution uses
isolated temporary environments and pinned `pip-audit==2.10.1`, not the contributor
environment's development packages. Root `project.dependencies` is currently
empty: its verified runtime closure is explicitly recorded as empty, not inferred
from a zero-file scanner result. Every recipe's requirements must exactly match
`scripts/gen_requirements.py` output from its pyproject; unique requirement sets
are resolved independently (not an incompatible cross-recipe union). Identical
sets share one audit result, with each recipe still represented in the report.

## Route-risk model

### Paid-backend canonical allow-list

Paid-backend PASS now requires a positive canonical-form check; the non-paid
inspection rules below remain diagnostic defense in depth, not the paid trust
decision. Unknown paid shapes fail closed and cannot be waived by the nineteen
existing inspection/binding review entries. Extending this grammar requires a
deliberate reviewed code change with real-SDK regression coverage.

The entrypoint and recursively resolved recipe-local import **execution closure**
are parsed without executing code. `import a.b.c` includes `a/__init__.py`,
`a/b/__init__.py`, then the resolved module or package initializer.
`from a import b` resolves either `a/b.py` or `a/b/__init__.py` when present;
otherwise `b` must be a statically declared/re-exported name. Relative imports
are based on the importing file's package (`__init__.py` is that package), with
all ancestor initializers up to the top-level package included. Every included
initializer must pass the same canonical grammar; an event trigger does not
excuse hidden initializer HTTP registration. Re-exported blueprint identities are
resolved recursively, with cycles bounded. Docstring-only initializers pass.
Namespace directories without initializers are supported only along unambiguous
local paths. Missing local targets, module/package collisions, relative escapes,
or symlinks to first-party code outside the recipe are UNKNOWN. Third-party and
stdlib imports remain declared dependencies, not recursively audited source.
An import resolving to first-party source outside that recipe is UNKNOWN. The accepted
module-top-level statements are:

- String docstrings and `from __future__ import annotations`.
- Imports that do not rebind/shadow app, func, constants or auth dependencies.
  `func` must come only from `import azure.functions as func`. Trusted logging,
  validation, OpenAPI and Pydantic helper names must retain their exact imports.
- Single-name literal/enum constant assignments, assigned once before use.
- Exactly one `app = func.FunctionApp(http_auth_level=...)` in keyword form.
  Auth is a literal or resolved single-assignment enum, or the exact opt-in
  expression below. Alias constructors, default/positional construction,
  attribute assignments, app aliases and rebinding are UNKNOWN.
- Function definitions with direct app registration decorators and literal/enum
  keyword arguments, no expansion. The inspected SDK route signature permits one
  leading literal route string, never positional auth. Explicit anonymous route
  overrides are outside the protected paid form. Function bodies/defaults may
  not reference app, constructors, dynamic execution/imports, or namespace/app
  reflection. Imported registration functions and nested registration are not
  canonical.

The three real paid modules require these narrow additional shapes, supported
explicitly rather than changing the examples: their exact optional OpenAI
`try: from openai import AzureOpenAI, OpenAIError` fallback (sets AzureOpenAI to
None and defines the empty OpenAIError exception); exact logging setup/get_logger;
Pydantic BaseModel classes containing only annotated fields and literal/Field
defaults; exact imported `openapi`, `with_context`, `validate_http` decorator
stacks with static model/limit arguments. Their startup opt-in is exactly
`PUBLIC_DEMO: Final = os.getenv("COOKBOOK_PUBLIC_DEMO", "") == "true"`, followed by
`ANONYMOUS if PUBLIC_DEMO else FUNCTION`, and their exact logger warning block.
No other top-level try/if/loop/with/class execution is accepted. The scanner
models default protection independent of the developer environment; real-SDK
tests explicitly set/unset the opt-in and establish ANONYMOUS only for `true`.

The runtime modules are unchanged. The full 82/104/74 extracted table and all
nineteen existing exact reviews remain unchanged on Python 3.11 and 3.14.

The Functions worker's application discovery imports `function_app.py` and its
import closure. Interpreter startup customization is a separate mechanism:
`sitecustomize`, `usercustomize` and `.pth` hooks can execute before application
indexing. In particular, putting the recipe directory on `PYTHONPATH` through its
own settings can cause local `sitecustomize.py` to execute (including with worker
indexing enabled). The earlier ordinary-host tripwire run without that setting
does **not** prove startup hooks cannot execute. Startup customization and
external dependency internals remain outside the source guard. The guard now
flags any recipe `sitecustomize.py`, `usercustomize.py`, `*.pth`, or PYTHONPATH /
PYTHONHOME-like local.settings/.env setting as incomplete inspection (FAIL for
paid recipes); no real recipe currently contains one. `conftest.py` is pytest
discovery, not worker application discovery.

Recipe-local import candidates must be plain `.py` source. Adjacent sourceless
`.pyc`/`.pyo`, extension `.so`/`.pyd` variants, `.zip`/`.egg` candidates and opaque
package initializers are UNKNOWN, including local candidates shadowing declared
stdlib/third-party names. Python 3 does not import sourceless files from
`__pycache__` alone; cache-only bytecode is not an opaque import candidate.
Top-level worker entrypoint relative imports are UNKNOWN because that module has
no package context; package-module relative imports remain supported. Discovery
prunes `.venv`, venv/env, `__pycache__`, site-packages and other generated paths
before traversal; source/security/dependency/requirements checks share this rule.

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

The supported constructor subset follows the inspected SDK signature:
`FunctionApp(http_auth_level=FUNCTION)` accepts its auth level positionally or by
keyword. Resolved enum/constructor import aliases and enum variables retain their
meaning; unresolved values, `*args`, `**kwargs`, unknown factories, star-import
rebinding and unresolved blueprint registration fail closed as `UNKNOWN`.
Conditional/loop registration is unresolved unless its controlling boolean is
statically known. Empty HTTP inventory alone is not evidence of an event-only
recipe: known apps need positive event-trigger/schedule declarations; a source
without any application or registration declarations is also non-HTTP. Existing
event-only examples retain their classifications.

Auth expressions use declaration-order snapshots, not final module bindings.
A referenced name is modelled only when its single top-level assignment precedes
the constructor/decorator use. Multiple assignments anywhere in the module,
including function/class-local stores, conditional/loop/try/with writes,
augmented assignments, walrus expressions and `global`/`nonlocal`, make that
name UNKNOWN. App/blueprint rebinding is subject to the same rule. Later values
never retroactively protect earlier SDK bindings.

Seven exact `binding_reviews` entries preserve existing literal SDK import and
fallback blocks: Durable AI's `df`; callback completion, Event Grid domain/router,
Service Bus DLQ and secretless Key Vault's `func`; poison handling's
`_func_module`. Each pins file/line/name/block digest and review reason. All stores
of the reviewed name must remain inside that block; a later rebind invalidates
the review. No real example rebinds an auth-level value. The twelve registration
inspection reviews are unchanged.

### Conservative inspection boundary

This check guards against **accidental public exposure**, especially in paid
recipes. It is **not a sandbox against adversarial Python** and is not a proof of
whole-program behavior. A construct that can register or mutate the exported
application but is outside the model makes inspection `UNKNOWN`, regardless of
otherwise protected routes or positive timer/event-trigger evidence. Paid-backend
recipes fail; other categories report `INCOMPLETE` with `INCOMPLETE_INSPECTION`
findings carrying the exact file and line. No empty inventory or event trigger
can override such a gap.

The guard scans every deployed Python module within each recipe directory
(including locally imported modules; hidden environments and tests are excluded).
The unmodelled-construct list is:

- Calls to built-in `exec`, `eval`, `compile`, `__import__`, or `importlib.*` /
  `runpy.*`, including resolved import aliases.
- Namespace reflection through `globals()`, `locals()`, `vars()`, and
  `getattr` / `setattr` / `delattr` on application-like objects.
- Assignment/deletion of private/underscore or auth-level-like attributes on
  apps/blueprints. `http_auth_level` assignment is not an SDK auth mutation.
- Call-style registration such as `app.route(...)(lambda/partial/call-result)`.
- Any `*args` or `**kwargs` in an app/blueprint constructor or registration
  decorator, even beside an explicit auth keyword. Expanded dictionaries are not
  treated as an implicit FUNCTION default.
- Bound/escaped registration methods or decorator factories: assigning
  `alias = app.route` (or `bp.route`), attribute aliases, passing a registration
  method as an argument, and `functools.partial` wrappers. Direct modelled calls
  are required. Registration methods include `route`, `schedule`, every
  `*_trigger`, Service Bus/Event Hub/Cosmos DB/Durable decorators,
  `function_name`, `register_functions`, and `register_blueprint`.
- Route registration in class bodies or nested functions. Class-local bindings
  never overwrite module bindings; their registration remains unmodelled.
- Passing app/blueprint objects to unresolved callables; the modelled
  `register_functions` relationship remains supported.
- Non-stdlib star imports, which can overwrite bindings or expose registration.

Known existing constructs require an explicit `inspection_reviews` manifest
entry matching **file, line, rule and SHA-256 of the exact AST construct**, plus
owner and review reason. Editing the construct or moving it invalidates the
entry. These are route-inspection reviews, not general security waivers or human
approval claims. The current twelve entries cover six literal Functions SDK
fallback imports, two Service Bus client/error imports, Requests warmup, a Queue
client import, the read-only toolkit metadata scan, and the existing MCP eval
tracked separately by #426. Runtime behavior and the 82-recipe route table are
unchanged. Blanket module or rule exclusions are not supported.

## Evidence, exceptions, and scanner failure

`PASS` means the stated policy completed; `FAIL` means findings violate policy.
`TOOL_ERROR` means execution/output/policy is unusable; `INCOMPLETE` means scope
or inventory is missing. An unresolvable requirement produces `TOOL_ERROR`, not
`INCOMPLETE`. Neither error nor incomplete is a clean pass. The tag
job blocks on every non-PASS result. All advisories block there, including unknown
severity; severity is informational, not an excuse to omit a known advisory.

`security/bandit-exceptions.json` entries match exact finding id/file/line;
`security/dependency-exceptions.json` entries match exact advisory id/package.
Every exception requires reason, owner, added date and expiry, no more than 90
days after addition, evaluated against the UTC date. Expired/future-dated/malformed entries block evaluation.
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
