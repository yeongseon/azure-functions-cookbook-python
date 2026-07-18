# Scheduled & Background

Use this category for recurring jobs and autonomous background execution. These recipes focus on work that starts from time-based schedules rather than user-facing requests.

## Category map

```mermaid
flowchart LR
    Timer[Timer schedule / NCRONTAB] --> Fn[Azure Function]
    Fn --> Work[Background work]
    Work --> Out[(Downstream / store)]
```

| Recipe | Trigger | Difficulty |
| --- | --- | --- |
| [Timer Cron Job](./timer-cron-job.md) | Timer | Beginner |
| Coming Soon | Timer / scheduled background work | Coming Soon |
