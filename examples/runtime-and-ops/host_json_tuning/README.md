# host_json_tuning

This recipe focuses on host-level tuning using a timer trigger plus a richly configured `host.json`.

## Prerequisites

- Python 3.10+
- [Azure Functions Core Tools v4](https://learn.microsoft.com/azure/azure-functions/functions-run-local)
- [Azurite](https://learn.microsoft.com/azure/storage/common/storage-use-azurite) (local Storage emulator)
## Logging

- `logging.logLevel.default`: baseline verbosity
- `Host.Results=Error`: reduce noise from result logs
- `Function=Information`: keep function logs visible
- `Host.Aggregator=Trace`: detailed host aggregation diagnostics
- `applicationInsights.samplingSettings`: control telemetry volume and cost

When to change:

- increase verbosity while debugging production issues
- reduce verbosity and sampling in high-throughput steady-state workloads

Performance impact:

- higher verbosity increases I/O and telemetry overhead
- sampling protects telemetry ingestion limits and spend

## Function timeout

- `functionTimeout="00:10:00"`

When to change:

- raise for legitimately long-running jobs
- lower to fail fast and avoid hung executions

Performance impact:

- long timeouts can tie up workers
- short timeouts can increase retries/failures if work is under-provisioned

## Queue extension settings

- `maxPollingInterval`: max delay between queue polls
- `visibilityTimeout`: lock window while a message is being processed
- `batchSize`: messages fetched per pull
- `maxDequeueCount`: poison message threshold
- `newBatchThreshold`: fetch trigger for next batch

When to change:

- tune for latency (`maxPollingInterval`) vs throughput (`batchSize`)
- raise `visibilityTimeout` if processing takes longer than expected

Performance impact:

- larger batches improve throughput but can increase memory and contention
- tighter polling improves responsiveness but adds storage transactions

## Service Bus extension settings

- `prefetchCount`: messages prefetched into memory
- `maxConcurrentCalls`: concurrent handler invocations per instance
- `maxAutoRenewDuration`: lock renewal cap for long processing

When to change:

- raise prefetch and concurrency for I/O-heavy handlers
- cap concurrency for CPU-bound handlers to prevent saturation

Performance impact:

- high concurrency increases throughput until CPU or downstream dependencies bottleneck
- prefetch lowers receive latency but consumes memory

## Run locally

```bash
cd examples/recipes/host_json_tuning
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp local.settings.json.example local.settings.json
func start
```
