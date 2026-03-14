# concurrency_tuning

This recipe demonstrates host-level dynamic concurrency:

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
pip install -r requirements.txt
func start
```
