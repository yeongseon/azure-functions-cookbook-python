# Local Run and Direct Invoke Example

This example shows two local testing workflows for an Azure Functions Python app:

1. Run the full Azure Functions host with `func start`
2. Invoke the handler directly from Python with `python invoke.py`

The HTTP function is `greet`, available at `GET/POST /api/greet`.

## Files

- `function_app.py`: function definition and request handling
- `invoke.py`: direct invocation script using `azure.functions.HttpRequest`
- `host.json`: Functions host config
- `local.settings.json.example`: local environment template
- `requirements.txt`: Python dependencies (`azure-functions`)

## Option 1: Run with Azure Functions Host

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp local.settings.json.example local.settings.json
func start
```

Then call the endpoint:

```bash
curl "http://localhost:7071/api/greet?name=Alice"
curl -X POST "http://localhost:7071/api/greet" \
  -H "Content-Type: application/json" \
  -d '{"name":"Bob"}'
```

## Option 2: Direct Python Invocation (No Host)

```bash
python invoke.py
```

Expected output:

```text
GET  /api/greet?name=Alice -> 200: {"greeting": "Hello, Alice!"}
POST /api/greet           -> 200: {"greeting": "Hello, Bob!"}
GET  /api/greet           -> 400: {"error": "Please provide a 'name' query param or JSON body."}
```

This direct-invoke pattern is useful for quick feedback while iterating on function logic.
