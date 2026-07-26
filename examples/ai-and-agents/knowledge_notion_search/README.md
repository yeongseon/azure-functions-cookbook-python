# Knowledge Notion Search

📖 [Full documentation](https://yeongseon.github.io/azure-functions-cookbook-python/patterns/ai-and-agents/knowledge-notion-search/)

Notion-backed knowledge retrieval with azure-functions-knowledge KnowledgeBindings input/inject_client decorators.

## Run

```bash
pip install -e ".[dev]"
cp local.settings.json.example local.settings.json
func start
```

## Endpoints

- `GET /api/search?q=<query>` — return the top Notion documents matching `q` (title, url, id). Injected via `@kb.input`.
- `GET /api/page/{page_id}` — fetch a single Notion page (title, content, url) via an injected provider client (`@kb.inject_client`).

Set the `NOTION_TOKEN` app setting (used by the `%NOTION_TOKEN%` binding) to a Notion integration token before running.
