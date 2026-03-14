# http_auth_levels

HTTP trigger example that demonstrates anonymous, function-key, and admin-key endpoints.

## What It Demonstrates

- `AuthLevel.ANONYMOUS` route with no key requirement
- `AuthLevel.FUNCTION` route requiring a function key
- `AuthLevel.ADMIN` route requiring the master/admin key

## Run Locally

```bash
cd examples/http/http_auth_levels
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp local.settings.json.example local.settings.json
func start
```

## Expected Output Example

```bash
curl "http://localhost:7071/api/public"
```

```text
This endpoint is public (anonymous).
```
