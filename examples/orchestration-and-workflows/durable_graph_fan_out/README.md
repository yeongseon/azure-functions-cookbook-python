# Durable Graph Fan Out

📖 [Full documentation](https://yeongseon.dev/azure-functions-python/cookbook/patterns/orchestration-and-workflows/)

Fan-out/fan-in DAG orchestration with azure-functions-durable-graph, driven by a declarative ManifestBuilder graph.

## Run

```bash
pip install -e ".[dev]"
cp local.settings.json.example local.settings.json
func start
```

## Endpoints

The durable-graph runtime exposes generic graph endpoints (the graph name is `review_fan_in`):

- `POST /api/graphs/review_fan_in/runs` — start a run. JSON body: `{"text": "the app keeps giving an error and a crash"}`. The graph seeds state, walks the `score_length → score_keywords → score_sentiment` chain, then the terminal `aggregate` node fans the partial scores back into a `decision` (`escalate` or `auto-resolve`).

> When `azure-functions-durable-graph` is not installed the recipe instead exposes `GET /api/fan-in/status` returning `501`.
