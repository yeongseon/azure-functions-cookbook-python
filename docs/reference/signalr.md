# SignalR Trigger, Input, and Output Bindings

SignalR bindings let Azure Functions act as a serverless negotiation endpoint, upstream event handler, and realtime message publisher. They are best for lightweight hub integration where Functions handles auth, fan-out decisions, or event-driven backend logic.

## Trigger

Use `@app.signalr_trigger(...)` to react to upstream events sent from Azure SignalR Service.

Key parameters: `hub_name`, `category`, `event`, `connection_string_setting`, and `arg_name`.

```python
import azure.functions as func

app = func.FunctionApp()

@app.signalr_trigger(
    arg_name="invocation",
    hub_name="chat",
    category="messages",
    event="sendMessage",
    connection_string_setting="AzureSignalRConnectionString",
)
def signalr_example(invocation: str) -> None:
    print(invocation)
```

## Input Binding

The negotiate endpoint usually uses the SignalR connection info input binding.

```python
import azure.functions as func

app = func.FunctionApp()

@app.route(route="negotiate", methods=["POST"])
@app.signalr_connection_info_input(
    arg_name="connection_info",
    hub_name="chat",
    connection_string_setting="AzureSignalRConnectionString",
    user_id="{headers.x-ms-client-principal-id}",
)
def negotiate(req: func.HttpRequest, connection_info: str) -> func.HttpResponse:
    return func.HttpResponse(connection_info, mimetype="application/json")
```

## Output Binding

Use the output binding to broadcast messages or manage groups.

```python
import json
import azure.functions as func

app = func.FunctionApp()

@app.queue_trigger(arg_name="msg", queue_name="chat-events", connection="AzureWebJobsStorage")
@app.signalr_output(arg_name="signalr", hub_name="chat", connection_string_setting="AzureSignalRConnectionString")
def publish_chat(msg: func.QueueMessage, signalr: func.Out[str]) -> None:
    signalr.set(json.dumps({
        "target": "newMessage",
        "arguments": [msg.get_body().decode("utf-8")]
    }))
```

## Configuration

SignalR bindings need little `host.json` customization:

```json
{
  "version": "2.0"
}
```

`local.settings.json` commonly includes `AzureSignalRConnectionString` plus any auth-related settings for negotiate endpoints and any trigger-side connection strings for chained workflows.

## Scaling Behavior

Negotiate endpoints scale like normal HTTP functions. Upstream SignalR events also arrive as HTTP-triggered invocations behind the scenes, so scale depends on request volume. Message fan-out happens inside the SignalR Service; your function is responsible only for producing the outbound message payload or handling the upstream event.

## Common Pitfalls

- The output binding shape must match SignalR's expected message contract (`target`, `arguments`, optional `userId`/`groupName`).
- Negotiation endpoints often fail because the client principal header is missing locally; use a fallback user ID for local testing.
- SignalR bindings are great for simple publish flows, but complex hub workflows often need the SDK for richer management operations.

## Related Patterns

- [Realtime](../patterns/realtime/index.md)
- [Output Binding vs SDK](../patterns/runtime-and-ops/output-binding-vs-sdk.md)
- [Blueprint Modular App](../patterns/runtime-and-ops/blueprint-modular-app.md)

## Related Links

- https://learn.microsoft.com/azure/azure-functions/functions-bindings-signalr-service-trigger?pivots=programming-language-python&tabs=python-v2
- https://learn.microsoft.com/azure/azure-functions/functions-bindings-signalr-service-output?pivots=programming-language-python&tabs=python-v2
