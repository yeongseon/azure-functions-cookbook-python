# MCP Server Example (Azure Functions)

This example hosts a manual Model Context Protocol (MCP) server on Azure Functions
using a standard HTTP trigger and JSON-RPC 2.0 messages.

Because `azure-functions-extension-mcp` may not be broadly available yet, this project
shows how to implement the MCP surface directly in `function_app.py` with no extra MCP package.

## Prerequisites

- Python 3.10+
- [Azure Functions Core Tools v4](https://learn.microsoft.com/azure/azure-functions/functions-run-local)
- [Azurite](https://learn.microsoft.com/azure/storage/common/storage-use-azurite) (local Storage emulator)

## What This Example Implements

- `initialize`: protocol handshake and server capabilities
- `tools/list`: returns available tools and JSON schemas
- `tools/call`: invokes a named tool with provided arguments

Included tools:

- `get_weather` (mock weather response)
- `calculate` (safe-ish expression evaluator with character allowlist)

## Files

- `function_app.py`: MCP JSON-RPC endpoint (`POST /api/mcp`)
- `host.json`: Functions host configuration
- `local.settings.json.example`: local runtime settings template
- `pyproject.toml`: Python dependencies

## Run Locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp local.settings.json.example local.settings.json
func start
```

The endpoint is available at:

`http://localhost:7071/api/mcp`

## Test with curl

Use your local function key (for `auth_level=FUNCTION`).

### 1) Initialize

```bash
curl -s -X POST "http://localhost:7071/api/mcp?code=<FUNCTION_KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {}
  }'
```

### 2) List tools

```bash
curl -s -X POST "http://localhost:7071/api/mcp?code=<FUNCTION_KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/list",
    "params": {}
  }'
```

### 3) Call a tool

```bash
curl -s -X POST "http://localhost:7071/api/mcp?code=<FUNCTION_KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
      "name": "calculate",
      "arguments": {"expression": "(2 + 3) * 4"}
    }
  }'
```

## Learn More

- Azure Functions docs: https://learn.microsoft.com/azure/azure-functions/
- Model Context Protocol overview on Microsoft Learn: https://learn.microsoft.com/azure/ai-foundry/model-context-protocol/
