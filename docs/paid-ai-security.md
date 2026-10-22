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
that ordinary local requests still work without keys.

For a deliberately public demonstration only, set the app setting
`COOKBOOK_PUBLIC_DEMO=true` **before worker startup**, then restart. This switches
the three apps to `ANONYMOUS` and logs a warning. Other values, including `1`, do
not enable it. Remove the setting to restore protection. This is not recommended
with live paid credentials; place APIM/Entra and distributed limits in front of
the endpoint if public access is necessary.

## Budgets, data handling, and production ingress

All three recipes reject bodies larger than **32,768 bytes** before JSON parsing
and model invocation (413). Prompts and optional system instructions are capped
at **4,000 characters each** by Pydantic (400 validation response). Chat and
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
