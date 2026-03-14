# blob_upload_processor

Blob-triggered Azure Function that processes uploaded files from `uploads/{name}`.

## What It Demonstrates

- Blob trigger in storage polling mode
- Logging blob name, size, and metadata
- Handling edge cases for empty blobs and large blob warnings

## Run Locally

```bash
cd examples/blob/blob_upload_processor
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp local.settings.json.example local.settings.json
func start
```

## Expected Output

- Uploading a blob to `uploads/` triggers processing logs.
- Empty blobs are skipped with a warning, and large blobs log a size warning.
