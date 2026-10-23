# Streaming AI Response

📖 [Full documentation](https://yeongseon.dev/azure-functions-python/cookbook/patterns/ai-and-agents/streaming-ai-response/)

HTTP-triggered sample that converts Azure OpenAI streaming chat completions into
Server-Sent Events.

## Run
```bash
pip install -e ".[dev]"
cp local.settings.json.example local.settings.json
func start
```

## Endpoint
- `POST /api/stream` - return `text/event-stream` output for one prompt

## Secure deployment

Default auth is `FUNCTION`. On Azure send `x-functions-key: <key>` (preferred) or
`?code=<key>`; missing/invalid keys return host HTTP 401:

```bash
curl "https://<app>.azurewebsites.net/api/stream" \
  -H "x-functions-key: ${FUNCTION_KEY}" -H "Content-Type: application/json" \
  -d '{"message":"Explain Azure Functions"}'
```

Ordinary local `func start` does not enforce keys. For an intentional public demo
only, set `COOKBOOK_PUBLIC_DEMO=true` before startup; this switches to `ANONYMOUS`
(only the exact lowercase string `true`). Case variants, `1`, `yes`, empty values
and whitespace/newlines stay protected. The app logger emits a warning that may
not appear in every host configuration; ordinary Core Tools captures did not show
it. Host tests assert auth metadata only. Remove it and restart to restore protection.

Bodies are capped at 32,768 bytes (413), message/system prompts at 4,000 characters
each (validation 422); malformed JSON returns 400. These statuses are verified
through the real validation decorator. Output is capped at 256 tokens. SSE frames are buffered before
returning; provider failures return a generic 502 without partial output. Missing
credentials retain the existing offline SSE fallback. Application logs exclude
prompts, keys, authorization headers and model responses.

Keys are not per-user authorization, rate/concurrency limits or quotas. Use
APIM/Entra, restricted ingress, distributed limits and model quotas; an in-process
limiter is intentionally out of scope. Keep separate low-quota demo credentials
untracked. Production Managed Identity needs SDK token-provider construction,
not just enabling an identity. See
[paid-AI deployment guidance](../../../docs/paid-ai-security.md).
