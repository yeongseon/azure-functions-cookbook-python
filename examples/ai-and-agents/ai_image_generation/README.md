# AI Image Generation

📖 [Full documentation](https://yeongseon.github.io/azure-functions-cookbook-python/patterns/ai-and-agents/ai-image-generation/)

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
