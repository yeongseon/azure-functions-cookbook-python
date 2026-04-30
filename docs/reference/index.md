# Reference

Quick-lookup pages for Azure Functions Python v2 triggers and bindings.

| Trigger Type | Input Bindings | Output Bindings | Delivery Guarantee | Max Batch | Ordering |
| --- | --- | --- | --- | --- | --- |
| [HTTP](./http.md) | Blob, Cosmos DB, SQL, SignalR connection info | HTTP response, Queue Storage, Blob, Service Bus, Event Grid, SignalR, SQL | Request/response; caller retries are app-defined | 1 request/invocation | Not guaranteed globally |
| [Timer](./timer.md) | None | Any supported output binding | At-least-once for scheduled occurrences when monitor is enabled | 1 schedule occurrence | Cron schedule order |
| [Queue Storage](./queue-storage.md) | Queue message body plus optional Blob/SQL/Cosmos lookups | Queue Storage, Blob, Service Bus, Event Grid | At-least-once | Configurable prefetch/batch; default host-managed | Best-effort, not FIFO |
| [Blob Storage](./blob-storage.md) | Trigger blob plus optional Blob/SQL/Cosmos lookups | Blob, Queue Storage, Service Bus, Event Grid | At-least-once | Usually 1 blob per invocation | Per-container ordering not guaranteed |
| [Event Grid](./event-grid.md) | Event payload plus optional Blob/SQL/Cosmos lookups | Event Grid, Queue Storage, Service Bus | At-least-once with Event Grid retry policy | Event array supported; commonly 1 | Not guaranteed |
| [Service Bus](./service-bus.md) | Brokered message plus optional Blob/SQL/Cosmos lookups | Service Bus queue/topic, Blob, Event Grid | Peek-lock processing is at-least-once | Configurable batch/cardinality | Queues preserve order per entity; sessions preserve per-session order |
| [Event Hub](./event-hub.md) | Event stream payload plus optional Blob/SQL/Cosmos lookups | Event Hub, Blob, Service Bus | At-least-once per partition checkpoint | Configurable batch size | Ordered within a partition only |
| [Cosmos DB](./cosmos-db.md) | Change feed items plus point-read/query input | Cosmos DB, Queue Storage, Service Bus | At-least-once from change feed | Configurable feed batch | Ordered within a logical partition feed range |
| [SQL](./sql.md) | SQL change rows plus SQL input query/lookup | SQL row upsert plus other output bindings | At-least-once for SQL change tracking trigger | Host-managed change batches | Ordered by change version, not strict transactional replay |

## Other reference pages

| Page | Scope |
| --- | --- |
| [Durable Functions](./durable.md) | Durable Functions concepts, APIs, and caveats |
