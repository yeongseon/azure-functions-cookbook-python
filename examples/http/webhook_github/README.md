# webhook_github

GitHub webhook receiver example with HMAC-SHA256 signature verification.

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
pip install -r requirements.txt
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
