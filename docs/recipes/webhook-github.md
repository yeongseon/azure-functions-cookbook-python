# Webhook GitHub

## Overview
This recipe documents the GitHub webhook receiver in `examples/http/webhook_github/`.
It combines signature verification,
JSON validation,
event-type dispatch,
and structured response payloads.

The endpoint is anonymous by design,
but it is protected by HMAC-SHA256 verification using the `X-Hub-Signature-256` header
and a shared secret from `GITHUB_WEBHOOK_SECRET`.

It handles `push`,
`pull_request`,
and `issues` events with dedicated handlers,
then falls back for unknown events.

## When to Use
- You need to receive GitHub events securely in Azure Functions.
- You want a clean event-dispatch pattern for multiple webhook event types.
- You need a reference for rejecting invalid signatures and malformed JSON.

## Architecture
```text
+-----------------+   POST /api/github/webhook   +-------------------------------+
| GitHub Webhooks | ---------------------------> | github_webhook(req)           |
+--------+--------+                              +---------------+---------------+
         |                                                        |
         | X-Hub-Signature-256                                   | verify with secret
         v                                                        v
  HMAC SHA256 signature check                         +-----------------------------+
                                                      | _is_signature_valid(...)    |
                                                      +---------------+-------------+
                                                                      |
                                                                      v
                                                      +-----------------------------+
                                                      | Event dispatch by header    |
                                                      | push / pull_request /issues |
                                                      +---------------+-------------+
                                                                      |
                                                                      v
                                                      +-----------------------------+
                                                      | JSON response to caller     |
                                                      +-----------------------------+
```

## Prerequisites
- Python 3.10+
- Azure Functions Core Tools v4
- `azure-functions` package from `requirements.txt`
- `GITHUB_WEBHOOK_SECRET` configured in environment/local settings
- Ability to compute test signatures for local webhook replay

## Project Structure
```text
examples/http/webhook_github/
├── function_app.py
├── host.json
├── local.settings.json.example
├── requirements.txt
└── README.md
```

## Implementation
The function uses helper methods for consistency:

- `_json_response` standardizes JSON serialization and content type.
- `_is_signature_valid` verifies request authenticity.
- `_handle_push`, `_handle_pull_request`, and `_handle_issues` map event payloads to outputs.

Signature verification from `function_app.py`:

```python
def _is_signature_valid(signature_header: str | None, payload: bytes, secret: str) -> bool:
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    expected = (
        "sha256="
        + hmac.new(
            key=secret.encode("utf-8"),
            msg=payload,
            digestmod=hashlib.sha256,
        ).hexdigest()
    )
    return hmac.compare_digest(expected, signature_header)
```

Main route and validation sequence:

```python
@app.route(route="github/webhook", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def github_webhook(req: func.HttpRequest) -> func.HttpResponse:
    secret = os.environ.get("GITHUB_WEBHOOK_SECRET", "")
    if not secret:
        return _json_response({"error": "Server is not configured with GITHUB_WEBHOOK_SECRET."}, status_code=500)

    signature = req.headers.get("X-Hub-Signature-256")
    raw_body = req.get_body()
    if not _is_signature_valid(signature, raw_body, secret):
        return _json_response({"error": "Invalid or missing webhook signature."}, status_code=401)
```

Event dispatch behavior:

```python
event_type = req.headers.get("X-GitHub-Event", "")
if event_type == "push":
    return _json_response(_handle_push(payload), status_code=200)
if event_type == "pull_request":
    return _json_response(_handle_pull_request(payload), status_code=200)
if event_type == "issues":
    return _json_response(_handle_issues(payload), status_code=200)
```

Status code intent:

- `500` when the server is misconfigured (missing secret).
- `401` when signature is invalid or absent.
- `400` when JSON is malformed or not an object.
- `200` when event is accepted and processed,
  including unhandled event types with a generic message.

## Run Locally
```bash
cd examples/http/webhook_github
pip install -r requirements.txt
func start
```

## Expected Output
```text
POST /api/github/webhook with valid signature and X-GitHub-Event: push

-> 200 OK
{
  "event": "push",
  "repository": "octo/repo",
  "ref": "refs/heads/main",
  "commits": 1,
  "message": "Processed push with 1 commit(s)."
}

POST with invalid signature -> 401
{"error":"Invalid or missing webhook signature."}
```

## Production Considerations
- Scaling: Webhooks can burst during high repo activity; keep handlers fast and offload heavy work to queues.
- Retries: GitHub retries failed deliveries, so return non-2xx only for true failures and ensure deterministic handling.
- Idempotency: Use `X-GitHub-Delivery` or payload identifiers to deduplicate repeated deliveries.
- Observability: Log event type, delivery ID, repository, and outcome with structured fields for triage.
- Security: Rotate webhook secrets, enforce TLS end to end, and never trust payloads before signature validation.

## Related Recipes
- [HTTP Auth Levels](./http-auth-levels.md)
- [HTTP Routing Query Body](./http-routing-query-body.md)
- [Queue Producer](./queue-producer.md)
