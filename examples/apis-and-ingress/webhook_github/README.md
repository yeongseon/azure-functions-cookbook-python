# webhook_github

GitHub webhook receiver example with HMAC-SHA256 signature verification.

## Prerequisites

- Python 3.10+
- [Azure Functions Core Tools v4](https://learn.microsoft.com/azure/azure-functions/functions-run-local)
- [Azurite](https://learn.microsoft.com/azure/storage/common/storage-use-azurite) (local Storage emulator)

## Environment Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `GITHUB_WEBHOOK_SECRET` | Shared secret for HMAC-SHA256 signature verification | `my-webhook-secret` |

Set in `local.settings.json` under `Values`. Copy `local.settings.json.example` as a starting template.

## What It Demonstrates

- Anonymous webhook endpoint at `POST /api/github/webhook`
- Validation of `X-Hub-Signature-256` using `hmac.compare_digest`
- Event dispatching via `X-GitHub-Event` for `push`, `pull_request`, and `issues`
- Structured JSON responses and basic webhook logging

## Run Locally

```bash
cd examples/http/webhook_github
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp local.settings.json.example local.settings.json
func start
```

## Expected Output Example

```bash
curl -X POST "http://localhost:7071/api/github/webhook" \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: push" \
  -H "X-Hub-Signature-256: sha256=<computed-signature>" \
  -d '{"ref":"refs/heads/main","repository":{"full_name":"octo/repo"},"commits":[{}]}'
```

```json
{"event":"push","repository":"octo/repo","ref":"refs/heads/main","commits":1,"message":"Processed push with 1 commit(s)."}
```
