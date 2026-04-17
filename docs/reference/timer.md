# Timer Trigger

Timer-triggered functions run on a schedule instead of in response to external traffic. They are a good fit for maintenance jobs, polling loops, and lightweight recurring automation where NCRONTAB precision matters more than low-latency event delivery.

## Trigger

Use `@app.timer_trigger(...)` with an NCRONTAB schedule.

Key parameters: `schedule`, `arg_name`, `run_on_startup`, and `use_monitor`.

```python
import datetime
import azure.functions as func

app = func.FunctionApp()

@app.timer_trigger(schedule="0 */5 * * * *", arg_name="timer", run_on_startup=False, use_monitor=True)
def timer_example(timer: func.TimerRequest) -> None:
    if timer.past_due:
        print("Timer is running late")
    print(f"Ran at {datetime.datetime.utcnow().isoformat()}Z")
```

## Input Binding

Timer has no native input payload, but it composes well with lookup bindings.

```python
import azure.functions as func

app = func.FunctionApp()

@app.timer_trigger(schedule="0 0 * * * *", arg_name="timer")
@app.blob_input(arg_name="config", path="app-config/daily.json", connection="AzureWebJobsStorage")
def load_schedule_config(timer: func.TimerRequest, config: bytes) -> None:
    print(config.decode("utf-8"))
```

## Output Binding

Timers commonly publish work to another system.

```python
import json
import azure.functions as func

app = func.FunctionApp()

@app.timer_trigger(schedule="0 */15 * * * *", arg_name="timer")
@app.queue_output(arg_name="out_msg", queue_name="maintenance-jobs", connection="AzureWebJobsStorage")
def enqueue_maintenance(timer: func.TimerRequest, out_msg: func.Out[str]) -> None:
    out_msg.set(json.dumps({"job": "cleanup", "past_due": timer.past_due}))
```

## Configuration

`host.json` usually only needs the extension bundle; timer-specific persistence is handled by the runtime monitor:

```json
{
  "version": "2.0"
}
```

`local.settings.json` commonly needs `AzureWebJobsStorage` because schedule monitoring uses the storage account. If you reference app settings in the NCRONTAB string, add those keys too.

## Scaling Behavior

A timer schedule is coordinated so one host instance claims each occurrence when monitoring is enabled. Timers do not scale out the way queues or hubs do; instead, one due occurrence becomes one invocation. Missed occurrences can replay as `past_due` after restarts depending on monitor state.

## Common Pitfalls

- `use_monitor=False` can skip persisted schedule tracking and is usually wrong for production jobs.
- NCRONTAB has six fields in Azure Functions, including seconds.
- Timer functions are poor choices for high-throughput parallel fan-out unless they immediately hand work to queues, hubs, or Durable Functions.

## Related Patterns

- [Timer Cron Job](../patterns/scheduled-and-background/timer-cron-job.md)
- [host.json Tuning](../patterns/runtime-and-ops/host-json-tuning.md)
- [Retry and Idempotency](../patterns/reliability/retry-and-idempotency.md)

## Related Links

- https://learn.microsoft.com/azure/azure-functions/functions-bindings-timer?pivots=programming-language-python&tabs=python-v2
- https://learn.microsoft.com/azure/azure-functions/functions-bindings-timer#ncrontab-expressions
