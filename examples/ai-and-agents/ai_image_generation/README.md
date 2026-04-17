# AI Image Generation Example

HTTP-triggered sample that sends a prompt to Azure OpenAI image generation and
returns the generated image URL.

## Run
```bash
pip install -r requirements.txt
cp local.settings.json.example local.settings.json
func start
```

## Endpoint
- `POST /api/images/generate` - generate an image URL from a text prompt
