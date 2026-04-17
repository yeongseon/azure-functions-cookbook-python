# API Reference

`azure-functions-python-cookbook` is a **content-first cookbook**, not a runtime library. There is no public Python API to import or install as a dependency.

## What this project provides

- **Patterns** — 60+ production-ready pattern documents under `docs/patterns/`, organized by category.
- **Foundations** — In-depth explanations of cross-cutting topics under `docs/foundations/`.
- **Runnable examples** — 60+ executable Azure Functions projects under `examples/`, organized by category.

!!! info "This is not a pip package"
    While the repository uses `pyproject.toml` for development tooling (linting, testing, docs), it is **not** intended to be installed as a runtime dependency in your application. You consume it by reading recipes and copying example patterns into your own projects.

## Using the examples

Each example is a self-contained Azure Functions project. Clone the repo, navigate to an example, and run it:

```bash
cd examples/apis-and-ingress/hello_http_minimal
pip install -e .
func start
```

Copy the relevant handler pattern into your own Functions app:

```python
# Example: minimal HTTP handler from hello-http-minimal recipe
import azure.functions as func

app = func.FunctionApp()

@app.function_name(name="hello")
@app.route(route="hello", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def hello(req: func.HttpRequest) -> func.HttpResponse:
    name = req.params.get("name", "world")
    return func.HttpResponse(f"Hello, {name}!")
```

## Package metadata

The `src/azure_functions_python_cookbook/` directory contains only package metadata used by the build system:

```python
from azure_functions_python_cookbook import __version__
# __version__ = "0.1.2"
```

This is used internally for versioning and is **not** a public API.

## Related Documents

- [Getting Started](getting-started.md)
- [Usage](usage.md)
- [Patterns](patterns/index.md)
- [Foundations](foundations/index.md)
