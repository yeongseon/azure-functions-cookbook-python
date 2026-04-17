# concurrency_tuning

This recipe demonstrates host-level dynamic concurrency:

## Prerequisites

- Python 3.10+
- [Azure Functions Core Tools v4](https://learn.microsoft.com/azure/azure-functions/functions-run-local)
- [Azurite](https://learn.microsoft.com/azure/storage/common/storage-use-azurite) (local Storage emulator)

- `dynamicConcurrencyEnabled=true`
- `snapshotPersistenceEnabled=true`

## Dynamic concurrency vs static `batchSize`

- dynamic concurrency: runtime automatically adjusts per-instance parallelism using observed health,
  CPU pressure, and processing latency
- static `batchSize` (queue extension): fixed fetch/dispatch behavior you tune manually

## When to use dynamic concurrency

- workload characteristics vary over time
- handlers are mostly I/O-bound and benefit from adaptive parallelism
- you want less manual retuning across environments

## When to use static controls

- strict predictability is required
- workload is CPU-bound and you need hard concurrency ceilings
- downstream dependencies enforce strict request limits

Many production workloads combine both: enable dynamic concurrency and still cap extension-level
settings when external systems need protection.

## Run locally

```bash
cd examples/recipes/concurrency_tuning
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp local.settings.json.example local.settings.json
func start
```
