# Python v2 Programming Model

This document explains the Azure Functions Python v2 programming model, how it differs from the v1 model, and how to apply it in production-ready apps.

## Why v2 exists

Python v1 worked well, but it required two sources of truth:

- `__init__.py` for function logic.
- `function.json` for trigger and binding metadata.

That split made refactoring harder because route names, queue names, and binding contracts were not colocated with code.

Python v2 introduces decorators and app-level registration to keep function behavior and metadata together.

## v1 vs v2 at a glance

| Dimension | Python v1 | Python v2 |
| --- | --- | --- |
| Metadata location | `function.json` | Python decorators |
| App entry point | One folder per function | Central `function_app.py` + optional modules |
| Function registration | Folder discovery | `FunctionApp()` object registration |
| Reuse/modularity | Manual imports across folders | `Blueprint` composition |
| Refactoring safety | Metadata can drift from code | Trigger/binding metadata next to code |
| Local readability | Split view (JSON + Python) | Single-file view |

## Core building blocks in v2

### `func.FunctionApp()`

`FunctionApp` is the central container for your functions.

- Owns registration of all triggers and bindings.
- Defines auth defaults for HTTP endpoints.
- Lets you keep one explicit app graph.

Example:

```python
import azure.functions as func

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)
```

### Decorators

Decorators declare the trigger and bindings directly on the function.

- Trigger decorators define invocation source.
- Input/output binding decorators define connected resources.
- `function_name` gives stable explicit function names.

Example:

```python
import azure.functions as func

app = func.FunctionApp()

@app.function_name(name="hello_http")
@app.route(route="hello/{name}", methods=["GET"])
def hello(req: func.HttpRequest) -> func.HttpResponse:
    name = req.route_params.get("name", "world")
    return func.HttpResponse(f"Hello, {name}!")
```

### `func.Blueprint`

`Blueprint` helps you organize functions by domain without creating many app roots.

- Define related functions in separate modules.
- Register all blueprints into a single app.
- Keep startup simple while codebase grows.

`shared/orders.py`:

```python
import azure.functions as func

bp = func.Blueprint()

@bp.function_name(name="orders_ping")
@bp.route(route="orders/ping", methods=["GET"])
def orders_ping(req: func.HttpRequest) -> func.HttpResponse:
    return func.HttpResponse("orders ok")
```

`function_app.py`:

```python
import azure.functions as func
from shared.orders import bp as orders_bp

app = func.FunctionApp()
app.register_functions(orders_bp)
```

## v1 to v2 code comparison

### Python v1 style

Folder layout:

```text
my_func_app/
  HttpExample/
    __init__.py
    function.json
  host.json
```

`HttpExample/function.json`:

```json
{
  "scriptFile": "__init__.py",
  "bindings": [
    {
      "authLevel": "function",
      "type": "httpTrigger",
      "direction": "in",
      "name": "req",
      "methods": ["get"],
      "route": "items/{id}"
    },
    {
      "type": "http",
      "direction": "out",
      "name": "$return"
    }
  ]
}
```

`HttpExample/__init__.py`:

```python
import azure.functions as func

def main(req: func.HttpRequest) -> func.HttpResponse:
    item_id = req.route_params.get("id", "unknown")
    return func.HttpResponse(f"item={item_id}")
```

### Python v2 style

Folder layout:

```text
my_func_app/
  function_app.py
  host.json
```

`function_app.py`:

```python
import azure.functions as func

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

@app.function_name(name="http_example")
@app.route(route="items/{id}", methods=["GET"])
def http_example(req: func.HttpRequest) -> func.HttpResponse:
    item_id = req.route_params.get("id", "unknown")
    return func.HttpResponse(f"item={item_id}")
```

## Availability and support boundaries

Python v2 is generally available on Azure Functions runtime v4.

Typical requirements:

- Azure Functions runtime 4.x.
- Python worker with v2 support.
- `azure-functions` package version that includes decorator APIs.

Practical checks:

- Confirm local Core Tools is v4.
- Confirm `FUNCTIONS_EXTENSION_VERSION` is `~4` in Azure.
- Confirm extensions used by your bindings are supported in your extension bundle.

## Current limitations and caveats

The v2 model removes many pain points, but keep these in mind:

- Not every historical v1 sample pattern maps one-to-one to decorators.
- Some extensions or niche bindings may lag behind in docs/examples.
- Durable Functions in Python still uses generator-based orchestrators (`yield`), not `async def` orchestrators.
- Mixing heavy import-time side effects in `function_app.py` can slow cold start.

Operational caveats:

- Use stable function names to avoid accidental rename impacts.
- Keep module imports deterministic and lightweight.
- Keep app settings consistent between local and cloud.

## Recommended migration approach from v1 to v2

1. Inventory all existing `function.json` files.
2. Port one trigger at a time into decorator syntax.
3. Keep function names stable where possible.
4. Move shared logic to normal Python modules.
5. Introduce `Blueprint` for feature grouping.
6. Validate local behavior with `func start`.
7. Deploy to a non-production slot first.

## Migration checklist

- [ ] `function_app.py` exists and initializes `FunctionApp()`.
- [ ] Every function has explicit `@app.function_name(...)`.
- [ ] Trigger decorators fully mirror original `function.json` contracts.
- [ ] Connection setting names are present in app settings.
- [ ] `host.json` settings are reviewed after migration.
- [ ] Integration tests run against local host and cloud host.

## Design tips for maintainable v2 apps

- Prefer one business capability per module/blueprint.
- Keep decorator declarations close to thin handlers.
- Push domain logic into pure Python services.
- Centralize configuration key names.
- Fail fast for missing required configuration.

## Relationship to other concepts

Use this page together with:

- Trigger and binding contracts: [Triggers and Bindings Overview](triggers-bindings-overview.md)
- Durable orchestration specifics: [Durable Functions Overview](../reference/durable.md)
- Identity settings and RBAC: [Identity-Based Connections](../guides/identity-based-connections.md)
- CI/CD and hosting choices: [Deployment Patterns](../guides/deployment-patterns.md)

## Microsoft Learn references

- Azure Functions Python developer guide: https://learn.microsoft.com/azure/azure-functions/functions-reference-python
- Python v2 programming model details: https://learn.microsoft.com/azure/azure-functions/functions-reference-python#programming-model
- Azure Functions triggers and bindings concepts: https://learn.microsoft.com/azure/azure-functions/functions-triggers-bindings
- Azure Functions host/runtime versions: https://learn.microsoft.com/azure/azure-functions/functions-versions
- Azure Functions Core Tools: https://learn.microsoft.com/azure/azure-functions/functions-run-local

## Quick recap

- Python v2 uses decorators and `FunctionApp()` for single-source function metadata.
- `Blueprint` enables clean modular composition.
- Migration from v1 is straightforward when done incrementally.
- Validate extension support, settings, and naming stability early.
