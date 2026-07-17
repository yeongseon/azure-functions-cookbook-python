# Blob & File Triggers

Use this category for storage-driven ingestion and file processing flows. These recipes show how to react to object creation events and process files with minimal polling logic.

## Category map

```mermaid
flowchart LR
    Blob[(Blob storage)] -->|create event| Fn[Blob / Event Grid Function]
    Fn --> Process[Process file]
    Process --> Out[(Output store / downstream)]
```

| Recipe | Trigger | Difficulty |
| --- | --- | --- |
| [Blob Upload Processor](./blob-upload-processor.md) | Blob trigger | Intermediate |
| [Blob Event Grid Trigger](./blob-eventgrid-trigger.md) | Event Grid for blob events | Intermediate |
| Coming Soon | Blob / file event | Coming Soon |
