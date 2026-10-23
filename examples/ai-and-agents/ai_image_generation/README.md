# AI Image Generation

📖 [Full documentation](https://yeongseon.dev/azure-functions-python/cookbook/patterns/ai-and-agents/ai-image-generation/)

HTTP-triggered sample that sends a prompt to Azure OpenAI image generation and
returns the generated image URL.

## Run
```bash
pip install -e ".[dev]"
cp local.settings.json.example local.settings.json
func start
```

## Endpoint
- `POST /api/images/generate` - generate an image URL from a text prompt

## Environment Variables

Copy `local.settings.json.example` to `local.settings.json` and fill these in. In Azure, set
them as app settings.

| Setting | Required | Default | Purpose |
| --- | --- | --- | --- |
| `AZURE_OPENAI_ENDPOINT` | For real calls | none | Azure OpenAI resource endpoint, for example `https://<resource>.openai.azure.com`. |
| `AZURE_OPENAI_KEY` | For real calls | none | API key for the Azure OpenAI resource. |
| `AZURE_OPENAI_IMAGE_DEPLOYMENT` | No | `dall-e-3` | Deployment name of the image model. |
| `AZURE_OPENAI_API_VERSION` | No | `2024-02-01` | Azure OpenAI REST API version. |
| `AzureWebJobsStorage` | Yes | `UseDevelopmentStorage=true` | Functions runtime storage. Use Azurite locally. |
| `FUNCTIONS_WORKER_RUNTIME` | Yes | `python` | Required by the Functions host. |

When `AZURE_OPENAI_ENDPOINT` or `AZURE_OPENAI_KEY` is unset (or the `openai` package is not
installed), the endpoint still answers `200` with a placeholder image URL, so the sample stays
runnable offline. Set both to exercise the real Azure OpenAI call.

Prefer Key Vault references or a managed identity over a raw `AZURE_OPENAI_KEY` in production.

## Secure deployment

Default auth is `FUNCTION`. On Azure send `x-functions-key: <key>` (preferred) or
`?code=<key>`; missing/invalid keys return host HTTP 401:

```bash
curl "https://<app>.azurewebsites.net/api/images/generate" \
  -H "x-functions-key: ${FUNCTION_KEY}" -H "Content-Type: application/json" \
  -d '{"prompt":"A diagram of a function app"}'
```

Ordinary local `func start` does not enforce keys; localhost examples still work.
Only for an intentional public demo, set `COOKBOOK_PUBLIC_DEMO=true` before
startup; only the exact lowercase string `true` switches to `ANONYMOUS`.
Case variants, `1`, `yes`, empty values and whitespace/newlines stay protected.
The app logger emits a warning that may not appear in every host configuration;
ordinary Core Tools captures did not show it. Host tests assert auth metadata only.

Request bodies are capped at 32,768 bytes (413), prompts at 4,000 characters
(validation 422); malformed JSON returns 400. These statuses are verified through
the real validation decorator. Work is capped at one standard-quality image per request. Provider
failures return a generic 502; absent credentials preserve the placeholder image.
Application logs exclude prompts, keys, authorization headers and model responses.

Keys are not per-user authorization, rate/concurrency limits or quotas. Use
APIM/Entra, restricted ingress, distributed limits and model quotas; this example
does not implement an in-process limiter. Keep local credentials low-quota and
untracked. Managed Identity requires changing SDK construction to a token provider;
enabling identity alone does not change this key-based code. See
[paid-AI deployment guidance](../../../docs/paid-ai-security.md).
