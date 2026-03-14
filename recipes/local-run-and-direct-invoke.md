# Local Run and Direct Invoke

## Overview
This recipe demonstrates two complementary local testing workflows for Azure Functions
Python handlers.
You can run the full Functions host with `func start` for end-to-end behavior,
or import handlers directly in Python for fast unit-style checks.

The included `invoke.py` script constructs `azure.functions.HttpRequest` instances
and calls `greet` directly.
This avoids host startup overhead and is useful while iterating on request parsing
and response formatting logic.

## When to Use
- You need quick feedback loops while editing request/response code.
- You need parity checks between direct invocation and real host execution.
- You want to teach newcomers how Azure Functions handlers are regular Python callables.

## Architecture
```text
Path A: Full host
+--------+      HTTP request       +--------------------------+
| Client | ----------------------> | func host + route table  |
+--------+                         +------------+-------------+
                                              |
                                              v
                                        greet(req)

Path B: Direct invoke
+------------------+      construct HttpRequest      +----------------+
| invoke.py script | ------------------------------> | greet(req)      |
+--------+---------+                                 +--------+-------+
         |                                                     |
         +---------------- response body/status --------------+
```

## Prerequisites
- Python 3.10+
- Azure Functions Core Tools v4
- `azure-functions` package installed in local environment
- Optional: `curl` for endpoint calls when running full host

## Project Structure
```text
examples/local_run_and_direct_invoke/
|- function_app.py
|- invoke.py
|- host.json
|- local.settings.json.example
|- requirements.txt
`- README.md
```

## Implementation
The HTTP handler supports query string and JSON body input for `name`.

```python
@app.route(route="greet", methods=["GET", "POST"], auth_level=func.AuthLevel.ANONYMOUS)
def greet(req: func.HttpRequest) -> func.HttpResponse:
    name = req.params.get("name")
    if not name:
        try:
            body = req.get_json()
            name = body.get("name")
        except ValueError:
            pass
    if not name:
        return func.HttpResponse(json.dumps({"error": "Please provide a 'name' query param or JSON body."}),
                                 mimetype="application/json", status_code=400)
    return func.HttpResponse(json.dumps({"greeting": f"Hello, {name}!"}),
                             mimetype="application/json", status_code=200)
```

`invoke.py` constructs three request variants and prints responses.

```python
get_req = func.HttpRequest(method="GET", url="/api/greet", body=b"", headers={}, params={"name": "Alice"})
get_resp = greet(get_req)

post_req = func.HttpRequest(method="POST", url="/api/greet",
                            body=json.dumps({"name": "Bob"}).encode(),
                            headers={"Content-Type": "application/json"})
post_resp = greet(post_req)

err_req = func.HttpRequest(method="GET", url="/api/greet", body=b"", headers={})
err_resp = greet(err_req)
```

Why both paths matter:

- `func start` validates binding metadata, route registration, and runtime integration.
- direct import validates pure handler logic quickly without host startup or emulator setup.
- combining both catches different classes of bugs early.

## Run Locally
```bash
cd examples/local_run_and_direct_invoke
pip install -r requirements.txt
func start
```

## Expected Output
```text
Direct invocation (`python invoke.py`) prints:

GET  /api/greet?name=Alice -> 200: {"greeting": "Hello, Alice!"}
POST /api/greet           -> 200: {"greeting": "Hello, Bob!"}
GET  /api/greet           -> 400: {"error": "Please provide a 'name' query param or JSON body."}

Host-based curl calls return the same JSON payloads and status codes.
```

## Production Considerations
- Scaling: direct invocation is local-only; production behavior still depends on host scaling.
- Retries: HTTP callers own retries; keep handlers fast and predictable for safe retries.
- Idempotency: design POST semantics so repeated submissions do not create duplicate side effects.
- Observability: use structured logs and correlation IDs in both local and hosted tests.
- Security: avoid anonymous auth for sensitive routes once moving beyond local experimentation.

## Related Recipes
- [MCP Server Example](./mcp-server-example.md)
- [Durable Unit Testing](./durable-unit-testing.md)
- [Durable Entity Counter](./durable-entity-counter.md)
