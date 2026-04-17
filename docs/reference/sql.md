# SQL Trigger, Input, and Output Bindings

Azure SQL bindings cover row lookups, upserts, and change-triggered processing without writing repetitive client code. They are useful for CRUD-style APIs and straightforward database event handlers, especially when the binding contract is simpler than direct SDK or driver usage.

## Trigger

Use `@app.sql_trigger(...)` to process row changes captured through the SQL extension.

Key parameters: `table_name`, `connection_string_setting`, `arg_name`, and optional polling/change settings exposed by the extension version.

```python
import azure.functions as func

app = func.FunctionApp()

@app.sql_trigger(
    arg_name="changes",
    table_name="dbo.ToDo",
    connection_string_setting="SqlConnectionString",
)
def sql_change_example(changes: str) -> None:
    print(changes)
```

## Input Binding

Use SQL input bindings for parameterized reads in HTTP or message-driven functions.

```python
import azure.functions as func

app = func.FunctionApp()

@app.route(route="todos/{id}", methods=["GET"])
@app.sql_input(
    arg_name="rows",
    command_text="select * from dbo.ToDo where Id = @Id",
    parameters="@Id={id}",
    connection_string_setting="SqlConnectionString",
)
def get_todo(req: func.HttpRequest, rows: str) -> func.HttpResponse:
    return func.HttpResponse(rows, mimetype="application/json")
```

## Output Binding

Use SQL output bindings for simple inserts or upserts.

```python
import json
import azure.functions as func

app = func.FunctionApp()

@app.route(route="todos", methods=["POST"])
@app.sql_output(
    arg_name="todo",
    command_text="dbo.ToDo",
    connection_string_setting="SqlConnectionString",
)
def save_todo(req: func.HttpRequest, todo: func.Out[str]) -> func.HttpResponse:
    payload = req.get_json()
    todo.set(json.dumps(payload))
    return func.HttpResponse(status_code=201)
```

## Configuration

SQL bindings usually need minimal `host.json` customization:

```json
{
  "version": "2.0"
}
```

`local.settings.json` commonly includes `SqlConnectionString`. For production, managed identity plus connection-string-style setting names is preferred when supported by the binding extension version.

## Scaling Behavior

SQL input and output bindings scale with the parent trigger. SQL triggers themselves poll for change notifications and process batches of changed rows, so throughput depends on database throughput, polling cadence, and how quickly workers can acknowledge progress. Delivery is at-least-once, so duplicate-safe writes matter.

## Common Pitfalls

- SQL output bindings are convenient for simple writes, but stored procedure, transaction, or bulk-load needs usually push you back to a proper database client.
- Parameter names in `parameters` must match the SQL placeholders exactly.
- SQL triggers depend on database-side prerequisites; missing change tracking or extension setup can make the trigger appear idle.

## Related Patterns

- [DB Input and Output Bindings](../patterns/data-and-pipelines/db-input-output.md)
- [Output Binding vs SDK](../patterns/runtime-and-ops/output-binding-vs-sdk.md)
- [Blueprint Modular App](../patterns/runtime-and-ops/blueprint-modular-app.md)

## Related Links

- https://learn.microsoft.com/azure/azure-functions/functions-bindings-azure-sql-trigger?pivots=programming-language-python&tabs=python-v2
- https://learn.microsoft.com/azure/azure-functions/functions-bindings-azure-sql-input?pivots=programming-language-python&tabs=python-v2
