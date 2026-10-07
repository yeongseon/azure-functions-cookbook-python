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
