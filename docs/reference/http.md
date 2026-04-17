# HTTP Trigger and HTTP-Centric Bindings

HTTP-triggered functions are the front door for request/response APIs, webhooks, and lightweight orchestration starters. In Python v2, the route decorator defines the trigger while other decorators can attach lookup or fan-out bindings without manual client setup.

## Trigger

Use `@app.route(...)` for the HTTP trigger.

Key parameters: `route`, `methods`, `auth_level`, and optional route tokens such as `{id}`.

```python
import azure.functions as func

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

@app.route(route="orders/{order_id}", methods=["GET"], auth_level=func.AuthLevel.FUNCTION)
def http_example(req: func.HttpRequest) -> func.HttpResponse:
    order_id = req.route_params["order_id"]
    include_items = req.params.get("includeItems") == "true"
    return func.HttpResponse(f"order={order_id}, include_items={include_items}")
```

## Input Binding

HTTP handlers often combine the trigger with a lookup binding so the function body stays focused on validation and response shaping.

```python
import azure.functions as func

app = func.FunctionApp()

@app.route(route="profiles/{user_id}", methods=["GET"])
@app.sql_input(
    arg_name="profile",
    command_text="select * from dbo.UserProfiles where UserId = @UserId",
    parameters="@UserId={user_id}",
    connection_string_setting="SqlConnectionString",
)
def get_profile(req: func.HttpRequest, profile: str) -> func.HttpResponse:
    return func.HttpResponse(profile, mimetype="application/json")
```

## Output Binding

Return the HTTP response normally, and use an output binding when the request should also enqueue or persist work.

```python
import json
import azure.functions as func

app = func.FunctionApp()

@app.route(route="tasks", methods=["POST"])
@app.queue_output(arg_name="out_msg", queue_name="task-jobs", connection="AzureWebJobsStorage")
def create_task(req: func.HttpRequest, out_msg: func.Out[str]) -> func.HttpResponse:
    payload = req.get_json()
    out_msg.set(json.dumps(payload))
    return func.HttpResponse(status_code=202, body="Accepted")
```

## Configuration

`host.json` usually focuses on HTTP concurrency and routing defaults:

```json
{
  "version": "2.0",
  "extensions": {
    "http": {
      "routePrefix": "api",
      "maxOutstandingRequests": 200,
      "maxConcurrentRequests": 100
    }
  }
}
```

`local.settings.json` keys commonly include `AzureWebJobsStorage`, `SqlConnectionString`, and any app-specific secrets used by downstream output bindings.

## Scaling Behavior

HTTP scales from request pressure. On Consumption and Flex Consumption plans, the platform adds instances based on concurrent request load, but a single request still runs on one worker. Long-running requests tie up concurrency slots, so HTTP is often used to enqueue background work rather than perform heavy processing inline.

## Common Pitfalls

- Returning a value does not populate a non-HTTP output binding; use `func.Out[...]` or the binding-specific return contract.
- Route params are strings, so convert and validate before using them in queries or downstream messages.
- Large request bodies can increase cold-start pain and memory pressure; offload file uploads to Blob Storage when possible.

## Related Patterns

- [Hello HTTP Minimal](../patterns/apis-and-ingress/hello-http-minimal.md)
- [HTTP Routing Query Body](../patterns/apis-and-ingress/http-routing-query-body.md)
- [HTTP Auth Levels](../patterns/apis-and-ingress/http-auth-levels.md)

## Related Links

- https://learn.microsoft.com/azure/azure-functions/functions-bindings-http-webhook-trigger?pivots=programming-language-python&tabs=python-v2%2Cisolated-process%2Cnodejs-v4%2Cfunctionsv1
- https://learn.microsoft.com/azure/azure-functions/functions-reference-python
