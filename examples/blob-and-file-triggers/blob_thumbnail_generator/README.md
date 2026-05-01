# Blob Thumbnail Generator

📖 [Full documentation](https://yeongseon.github.io/azure-functions-cookbook-python/patterns/blob-and-file-triggers/blob-thumbnail-generator/)

Event Grid-driven blob processor that generates thumbnails and writes them to a separate output container.

## Prerequisites

- Python 3.10+
- Azure Functions Core Tools v4
- Azurite or Azure Storage account with blob containers

## Run Locally

```bash
cd examples/blob-and-file-triggers/blob_thumbnail_generator
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp local.settings.json.example local.settings.json
func start
```

## Expected Output

- Blob-created Event Grid notifications invoke the function.
- The function writes a resized image to the `thumbnails` container.
