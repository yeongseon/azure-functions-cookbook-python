# Azure OpenAI Direct Chat

📖 [Full documentation](https://yeongseon.dev/azure-functions-python/cookbook/patterns/ai-and-agents/openai-direct-chat/)

Minimal HTTP-triggered Azure Functions sample that sends one message to Azure
OpenAI with the `openai` Python SDK.

## Run
```bash
pip install -e ".[dev]"
cp local.settings.json.example local.settings.json
func start
```

## Endpoint
- `POST /api/chat` - submit a single message and receive a JSON answer

## Secure deployment

Default auth is `FUNCTION`. On Azure send `x-functions-key: <key>` (preferred) or
`?code=<key>`; missing/invalid keys return host HTTP 401. For example:

```bash
curl "https://<app>.azurewebsites.net/api/chat" \
  -H "x-functions-key: ${FUNCTION_KEY}" -H "Content-Type: application/json" \
  -d '{"message":"Explain Azure Functions"}'
```

Ordinary local `func start` does not enforce keys, so localhost requests need no
key. Only an intentional public demo should set `COOKBOOK_PUBLIC_DEMO=true`
before startup; only the exact lowercase string `true` switches auth to `ANONYMOUS`.
Case variants, `1`, `yes`, empty values and whitespace/newlines stay protected.
The app logger emits a warning that may not appear in every host configuration;
ordinary Core Tools captures did not show it. Host tests assert auth metadata only.

Bodies are capped at 32,768 bytes (413), message/system prompts at 4,000 characters
each (validation 422); malformed JSON returns 400. Output is capped at 256 tokens.
These input statuses are verified through the real validation decorator. Provider failures return a generic
502. Missing credentials retain the offline fallback. Application logs do not
include prompts, keys, authorization headers or model responses.

Function keys do not provide per-user authorization, rate limits, concurrency
limits or quotas. Use APIM/Entra, restrict direct ingress, and set distributed
limits and model quotas. No in-process limiter is claimed. Use separate low-quota
local credentials; use Key Vault references or implement the documented Managed
Identity token-provider path for production (this code still uses API keys).
See [paid-AI deployment guidance](../../../docs/paid-ai-security.md).
