# Azure OpenAI Direct Chat Example

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
