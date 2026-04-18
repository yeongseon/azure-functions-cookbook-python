# Streaming AI Response Example

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
