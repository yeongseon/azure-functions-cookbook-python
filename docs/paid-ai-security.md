# Paid AI recipe security

The **Azure OpenAI Direct Chat**, **AI Image Generation**, and **Streaming AI
Response** recipes now declare `func.AuthLevel.FUNCTION` by default, including
when no model credentials are configured. On Azure, missing or invalid function
keys are rejected by the host with HTTP 401 before the handler runs.

```bash
curl "https://<app>.azurewebsites.net/api/chat" \
  -H "x-functions-key: ${FUNCTION_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"message":"Explain Azure Functions"}'
```

The image route is `/api/images/generate` with a `prompt` field; the streaming
route is `/api/stream` with a `message` field. A `?code=<function-key>` query
parameter also works, but the header avoids putting keys in URL histories and
proxy logs. Never paste real keys into tracked configuration or documentation.

## Local development and explicit public demos

Ordinary `func start` does **not** enforce function keys locally (Core Tools has
an explicit `--enableAuth` option). Existing localhost curl examples therefore
continue to work without keys. Do not expose the local host to the internet.
Handler tests assert binding declarations; they cannot prove host authorization.
The dedicated host check inspects the real indexed binding metadata and checks
that ordinary local requests still work without keys. It installs each recipe's
own requirements in an isolated virtual environment and covers default FUNCTION,
exact `true` ANONYMOUS, and a case-variant value that remains FUNCTION.

For a deliberately public demonstration only, set the app setting
`COOKBOOK_PUBLIC_DEMO=true` **before worker startup**, then restart. This switches
the three apps to `ANONYMOUS`. Only the exact lowercase string `true` opts in;
`True`, `TRUE`, `1`, `yes`, `false`, empty values, surrounding whitespace, and
trailing newlines stay protected. The app logger emits a warning, but it may not
appear in every host configuration; ordinary Core Tools captures did not show it.
The real-host test asserts declared auth metadata, not warning visibility.
Remove the setting to restore protection. This is not recommended
with live paid credentials; place APIM/Entra and distributed limits in front of
the endpoint if public access is necessary.

## Budgets, data handling, and production ingress

All three recipes reject bodies larger than **32,768 bytes** before JSON parsing
and model invocation (413). Prompts and optional system instructions are capped
at **4,000 characters each** by Pydantic (422 validation response). Malformed JSON
returns 400. These status codes are verified through the real validation decorator. Chat and
streaming calls set `max_tokens=256`; image generation explicitly requests one
standard-quality image in one of the three documented sizes. Calls use a
30-second SDK timeout with automatic retries disabled. These are per-call work
limits, not billing guarantees. The streaming example buffers SSE frames; it is
not a low-memory, incremental HTTP streaming server.

Provider errors produce a generic 502 without provider text or stack traces.
Application logs record operation/deployment metadata, not prompts, authorization
headers, API keys, or model responses. `with_context` adds invocation correlation;
its optional lifecycle/error logging remains disabled. Do not enable SDK debug
payload logging (`OPENAI_LOG=debug`) or HTTP wire logging in production. Platform
telemetry and user-supplied middleware require a separate redaction review.

Function keys are shared application secrets: **not per-user authentication,
authorization, rate limiting, concurrency control, or quota enforcement**.
Use Entra-authenticated APIM or another trusted edge, restrict direct backend
ingress, apply per-user rate limits and distributed concurrency/quotas, set model
deployment quotas and billing alerts, and validate content policies. A tiny
in-process limiter would reset on restarts and multiply across workers, so these
examples intentionally do not pretend to provide one. See the rate-limiting and
concurrency-tuning recipes for their separate educational scopes.

## Credentials

Missing endpoint/key settings retain the original offline fallback; no provider
request is made. Local developers may supply a separate, low-quota demo resource
key in ignored `local.settings.json`, never in its tracked `.example` template.
Use Key Vault references if retaining key authentication in Azure.

For production, prefer Azure OpenAI Microsoft Entra authentication: enable a
Function App managed identity, grant the appropriate Cognitive Services OpenAI
role, and configure the SDK's `azure_ad_token_provider` using
`DefaultAzureCredential`/`get_bearer_token_provider` with
`https://cognitiveservices.azure.com/.default`. These recipes still use key-based
SDK construction; setting an identity alone does not change that code path.
Identity/RBAC, edge limits and deployed 401 behavior need Azure verification.

The JWT, EasyAuth, multitenant, webhook and public health recipes retain their
existing route-level behavior. An anonymous binding can be intentional; it is
not evidence that handler or edge authorization is absent.

## Static inspection limits

Paid-backend recipes now require a **canonical allow-list**, not merely absence
of known dangerous constructs. The entrypoint and recursively imported local
modules must match supported imports/constants, exactly one keyword-form
`app = func.FunctionApp(http_auth_level=...)`, direct static registration, and
the narrow logging/Pydantic/OpenAI-fallback/decorator shapes used by these three
examples. Only the exact public-demo conditional is modelled. Positional auth,
constructor/import/app aliases, imported apps, arbitrary top-level control flow,
expanded arguments and indirect registration are UNKNOWN. First-party imports
outside the inspected recipe are UNKNOWN. Existing manifest review entries do
not waive paid canonical rejection; extensions require deliberate code review
and SDK tests. Runtime recipe code is unchanged. See SECURITY.md for the exact
statement grammar and the justified exceptions for these three modules.

Recursive inspection includes executed package initializers, not just the final
dotted module: importing `a.b.c` includes every existing ancestor `__init__.py`.
Absolute/from-submodule and package-relative imports, re-exports and unambiguous
namespace packages are resolved without execution. Missing/ambiguous local
targets or imports escaping the recipe are UNKNOWN. Adjacent bytecode, native
extensions, zip/egg candidates and sourceless package initializers are UNKNOWN;
`__pycache__`-only bytecode is not Python 3 sourceless import discovery. Relative
imports in the non-package entrypoint are UNKNOWN.

The worker application imports `function_app.py` and its closure, not pytest
conftest discovery. Interpreter startup hooks are separate: local settings that
put the recipe directory on `PYTHONPATH` can cause sitecustomize/usercustomize to
execute before indexing. The earlier no-PYTHONPATH tripwire run is not evidence
against this. Startup hooks/`.pth` files and PYTHONPATH-like recipe settings are
flagged incomplete (paid recipes FAIL); interpreter startup execution remains
outside the source guard. No real recipe currently has such hooks/settings.

The manifest guard prevents accidental public exposure; it is not a sandbox for
adversarial code. Unsupported registration/auth mutation makes inspection UNKNOWN
even alongside protected routes or event triggers. Paid recipes fail; non-paid
recipes report incomplete inspection with file:line. Dynamic execution/imports,
namespace/app reflection, private/auth attribute mutation, call-style route
registration, class/nested-function registration, app escapes to unresolved
callables, and non-stdlib star imports require review. Inspection also rejects
argument expansion (`*args` / `**kwargs` even beside explicit auth)
and bound/escaped registration methods or partial decorator factories on apps
and blueprints. Route, schedule, trigger, function-name and blueprint-registration
methods must remain direct modelled uses. The exact construct list
rejects rebinding of names used for auth or app construction: only a single
preceding top-level assignment is modelled, using the value visible at declaration
time. Later assignments never rewrite earlier bindings; conditional, nested,
augmented, walrus and global writes are UNKNOWN. The exact construct list
and file/line/AST-digest review-entry contract are in
[the security inspection boundary](https://github.com/yeongseon/azure-functions-cookbook-python/blob/main/SECURITY.md#conservative-inspection-boundary).
