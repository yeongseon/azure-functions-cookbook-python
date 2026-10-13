# Package runtime gates

The canonical package-native HTTP recipe is
`examples/apis-and-ingress/full_stack_crud_api`. Its live tests are selectable
independently so upstream release gates exercise the package they claim to verify.

| Package | Example | Pytest selection |
| --- | --- | --- |
| `azure-functions-validation` | Full Stack CRUD API | `-m package_validation` |
| `azure-functions-logging` | Full Stack CRUD API | `-m package_logging` |
| `azure-functions-openapi` | Full Stack CRUD API | `-m package_openapi` |

Run a gate with, for example:

```bash
hatch run pytest tests/e2e/test_package_runtime.py -m package_validation --no-cov
```

These tests start a real local Functions host. They require Functions Core Tools
and Azurite, but no Azure subscription or cloud credentials.
