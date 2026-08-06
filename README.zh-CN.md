# Azure Functions Python Cookbook

[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue)](https://github.com/yeongseon/azure-functions-cookbook-python)
[![CI](https://github.com/yeongseon/azure-functions-cookbook-python/actions/workflows/ci-smoke.yml/badge.svg)](https://github.com/yeongseon/azure-functions-cookbook-python/actions/workflows/ci-smoke.yml)
[![codecov](https://codecov.io/gh/yeongseon/azure-functions-cookbook-python/branch/main/graph/badge.svg)](https://codecov.io/gh/yeongseon/azure-functions-cookbook-python)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://pre-commit.com/)
[![Docs](https://github.com/yeongseon/azure-functions-cookbook-python/actions/workflows/docs.yml/badge.svg)](https://github.com/yeongseon/azure-functions-cookbook-python/actions/workflows/docs.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

其他语言阅读: [한국어](README.ko.md) | [日本語](README.ja.md) | [简体中文](README.zh-CN.md)

用于使用 Python 构建真实生产级 Azure Functions 的实用配方集。

## Why Use It

启动一个新的 Azure Functions 项目通常意味着要拼凑分散的文档、
博客文章和示例代码。本手册提供精心整理、可运行的配方，回答以下问题:

- 针对该场景我应该构建什么?
- 架构应当如何设计?
- 如何从一个可用的基线开始?

## Scope

- Azure Functions Python **v2 编程模型**
- 基于装饰器的 `func.FunctionApp()` 应用
- 带可运行示例的实用配方
- 架构说明与生产注意事项

本仓库以内容为先。它不是一个 CLI 工具。

## Quick Index

跳转到分类: [APIs and Ingress](#apis-and-ingress) · [Scheduled and Background](#scheduled-and-background) · [Blob and File Triggers](#blob-and-file-triggers) · [Async APIs and Jobs](#async-apis-and-jobs) · [Messaging and Pub/Sub](#messaging-and-pubsub) · [Streams and Telemetry](#streams-and-telemetry) · [Data and Pipelines](#data-and-pipelines) · [Orchestration and Workflows](#orchestration-and-workflows) · [Reliability](#reliability) · [Security and Tenancy](#security-and-tenancy) · [Runtime and Ops](#runtime-and-ops) · [Realtime](#realtime) · [AI and Agents](#ai-and-agents) · [Guides](#guides)

---

## Recipes

### APIs and Ingress

| 配方 | 说明 |
| --- | --- |
| [APIM Function Backend](examples/apis-and-ingress/apim_function_backend/) | 设计为位于 Azure API Management 策略之后（用于认证、限流和缓存）的 HTTP 触发 Azure Functions 后端。 |
| [BFF Facade API](examples/apis-and-ingress/bff_facade_api/) | 将多个后端服务调用聚合为单个面向客户端响应的 HTTP Backend-for-Frontend 外观。 |
| [EasyAuth Claims Extraction](examples/apis-and-ingress/auth_easyauth/) | 面向 Azure Functions、带基于角色访问控制的 EasyAuth 主体提取。 |
| [Full Stack CRUD API](examples/apis-and-ingress/full_stack_crud_api/) | 围绕单个 `items` 资源将 Azure Functions Python DX Toolkit 串联起来的示范性 HTTP API。 |
| [HTTP Auth Levels](examples/apis-and-ingress/http_auth_levels/) | 演示匿名、函数密钥和管理员密钥端点的 HTTP 触发示例。 |
| [HTTP Routing Query Body](examples/apis-and-ingress/http_routing_query_body/) | 演示路由参数、查询字符串、JSON 主体解析和状态码的 HTTP CRUD 与搜索示例。 |
| [Hello HTTP Minimal](examples/apis-and-ingress/hello_http_minimal/) | 返回问候语的最小化 HTTP 触发 Azure Function。 |
| [JWT Bearer Validation](examples/apis-and-ingress/auth_jwt_validation/) | 面向 Azure Functions、带基于声明访问控制的 JWT Bearer 令牌校验。 |
| [Multi-Tenant Auth](examples/apis-and-ingress/auth_multitenant/) | 面向 Azure Functions、使用租户允许列表的多租户访问控制。 |
| [Scaffold Walkthrough — from afs new to a running HTTP API](examples/apis-and-ingress/scaffold_walkthrough_app/) | 本配方是使用默认 `strict` 预设的 **`azure-functions-scaffold` 已提交输出**。用它来准确了解脚手架 CLI 为全新的 Azure Functions Python v2 HTTP 项目生成了什么，并学习推荐的本地开发循环。 |
| [Webhook GitHub](examples/apis-and-ingress/webhook_github/) | 带 HMAC-SHA256 签名校验的 GitHub Webhook 接收器示例。 |

### Scheduled and Background

| 配方 | 说明 |
| --- | --- |
| [Durable Timer Reminder](examples/scheduled-and-background/durable_timer_reminder/) | 等待较长延迟后执行提醒回调活动的 Durable Functions 编排。 |
| [Queue Scheduled Dispatch](examples/scheduled-and-background/queue_scheduled_dispatch/) | 将到期工作释放到 Azure Storage Queue 供下游工作者处理的计时器驱动计划调度模式。 |
| [Timer Cron Job](examples/scheduled-and-background/timer_cron_job/) | 每 5 分钟运行一次计划维护作业的计时器触发 Azure Function。 |

### Blob and File Triggers

| 配方 | 说明 |
| --- | --- |
| [Blob CSV to Table](examples/blob-and-file-triggers/blob_csv_to_table/) | 读取上传的 CSV Blob 并将规范化行写入 Azure Table Storage 的 Event Grid 驱动摄取模式。 |
| [Blob Event Grid Trigger](examples/blob-and-file-triggers/blob_eventgrid_trigger/) | 为 Event Grid 源通知配置的 Blob 触发 Azure Function。 |
| [Blob Thumbnail Generator](examples/blob-and-file-triggers/blob_thumbnail_generator/) | 生成缩略图并将其写入单独输出容器的 Event Grid 驱动 Blob 处理器。 |
| [Blob Upload Processor](examples/blob-and-file-triggers/blob_upload_processor/) | 处理从 `uploads/{name}` 上传文件的 Blob 触发 Azure Function。 |

### Async APIs and Jobs

| 配方 | 说明 |
| --- | --- |
| [Async HTTP 202 Polling](examples/async-apis-and-jobs/async_http_polling/) | 返回 `202 Accepted` 和用于客户端轮询的 `statusQueryGetUri` 的 HTTP 触发 Durable Functions 示例。 |
| [Callback Completion](examples/async-apis-and-jobs/callback_completion/) | 在 `/api/tasks` 接受工作并在后台处理完成时发送 HTTP 回调的 HTTP + Queue 示例。 |
| [Queue-Backed Job](examples/async-apis-and-jobs/queue_backed_job/) | 接受作业、返回 `202 Accepted` 并轮询已存储状态记录的 HTTP + Storage Queue 配方。 |

### Messaging and Pub/Sub

| 配方 | 说明 |
| --- | --- |
| [Claim Check Pattern](examples/messaging-and-pubsub/claim_check_pattern/) | 将负载存储在 Blob Storage 中、仅通过队列传递引用的大消息模式。 |
| [Event Grid Domain Events](examples/messaging-and-pubsub/eventgrid_domain_events/) | 将自定义订单域事件发布到 Event Grid 自定义主题的 HTTP 触发 Azure Function，以及记录由此产生事件的 Event Grid 触发订阅者。 |
| [Event Grid Event Router](examples/messaging-and-pubsub/eventgrid_router/) | 使用事件类型和主题过滤器将事件路由到不同处理器的 Event Grid 触发 Azure Function。 |
| [Queue Consumer](examples/messaging-and-pubsub/queue_consumer/) | 解析并处理任务消息的队列触发 Azure Function。 |
| [Queue Producer](examples/messaging-and-pubsub/queue_producer/) | 校验 JSON 并将任务入队到 Storage Queue 的 HTTP 触发 Azure Function。 |
| [Service Bus DLQ Replay](examples/messaging-and-pubsub/servicebus_dlq_replay/) | 在检查与修复后，将死信 Service Bus 队列消息重放回主队列。 |
| [Service Bus Sessions](examples/messaging-and-pubsub/servicebus_sessions/) | 演示使用 Azure Service Bus 会话进行有序消息处理的 Azure Functions 示例。 |
| [Service Bus Topic Fan-out](examples/messaging-and-pubsub/servicebus_topic_fanout/) | 演示使用三个独立订阅处理器进行 Service Bus 主题扇出的 Azure Functions 示例。 |
| [Service Bus Worker](examples/messaging-and-pubsub/servicebus_worker/) | 用于可靠后台工作消费的 Service Bus 队列触发 Azure Function。 |

### Streams and Telemetry

| 配方 | 说明 |
| --- | --- |
| [Event Hub Batch Window](examples/streams-and-telemetry/eventhub_batch_window/) | 处理批处理窗口并记录聚合遥测总计的 Event Hub 触发 Azure Function。 |
| [Event Hub Checkpoint Replay](examples/streams-and-telemetry/eventhub_checkpoint_replay/) | 演示带偏移量跟踪和幂等处理的重放感知 Event Hub 消费的 Azure Functions 示例。 |
| [Event Hub Consumer](examples/streams-and-telemetry/eventhub_consumer/) | 用于近实时遥测流处理的 Event Hub 触发 Azure Function。 |

### Data and Pipelines

| 配方 | 说明 |
| --- | --- |
| [CQRS Read Projection](examples/data-and-pipelines/cqrs_read_projection/) | 面向 Azure Functions Python 的 CQRS 示例，其中: |
| [Change Feed Processor](examples/data-and-pipelines/change_feed_processor/) | 用于下游同步的 Cosmos DB 更改源触发 Azure Function。 |
| [DB Input and Output Bindings](examples/data-and-pipelines/db_input_output/) | 演示 `azure-functions-db-python` 的输入/输出绑定与 SQLAlchemy 支持的存储结合，并与 `azure-functions-validation-python` 和 `azure-functions-openapi-python` 一起使用。 |
| [ETL Enrichment](examples/data-and-pipelines/etl_enrichment/) | 读取原始 JSON 客户记录、用查找数据加以丰富并将丰富后的行写入数据库的 Blob 触发 ETL 示例。 |
| [File Processing Pipeline](examples/data-and-pipelines/file_processing_pipeline/) | 校验上传的 CSV 或 JSON 文件、转换记录并将处理结果持久化到数据库的 Blob 触发 Azure Function。 |
| [SQLAlchemy REST Pagination](examples/data-and-pipelines/sqlalchemy_rest_pagination/) | 组合以下内容的 HTTP API 示例: |

### Orchestration and Workflows

| 配方 | 说明 |
| --- | --- |
| [Async Job Lifecycle](examples/orchestration-and-workflows/async_job_lifecycle/) | 用于完整异步作业生命周期管理（创建、状态、取消和清除）的 Durable Functions 配方。 |
| [Durable Determinism Gotchas](examples/orchestration-and-workflows/durable_determinism_gotchas/) | 演示确定性编码模式的 Durable Functions 编排器。 |
| [Durable Entity Counter](examples/orchestration-and-workflows/durable_entity_counter/) | 管理计数器状态的 Durable Entity 示例。 |
| [Durable Fan-Out Fan-In](examples/orchestration-and-workflows/durable_fan_out_fan_in/) | 使用并行活动的 Durable Functions 扇出/扇入编排。 |
| [Durable Graph Fan Out](examples/orchestration-and-workflows/durable_graph_fan_out/) | 由声明式 ManifestBuilder 图驱动的、基于 azure-functions-durable-graph 的扇出/扇入 DAG 编排。 |
| [Durable Hello Sequence](examples/orchestration-and-workflows/durable_hello_sequence/) | 按顺序链接活动的 Durable Functions 编排器。 |
| [Durable Human Interaction](examples/orchestration-and-workflows/durable_human_interaction/) | 带超时等待外部审批事件的 Durable Functions 工作流。 |
| [Durable Retry Pattern](examples/orchestration-and-workflows/durable_retry_pattern/) | 重试不稳定活动的 Durable Functions 编排。 |
| [Durable Singleton Monitor](examples/orchestration-and-workflows/durable_singleton_monitor/) | 持续轮询外部依赖并在发生变化时发出告警的 Durable Functions 单例编排。 |
| [Durable Unit Testing](examples/orchestration-and-workflows/durable_unit_testing/) | 聚焦基于模拟的编排器单元测试的 Durable Functions 示例。 |
| [Saga Compensation](examples/orchestration-and-workflows/saga_compensation/) | 在失败时补偿先前已完成步骤的 Durable Functions Saga 编排。 |
| [Sub-Orchestration](examples/orchestration-and-workflows/sub_orchestration/) | 将工作委派给两个子编排器的 Durable Functions 父编排。 |

### Reliability

| 配方 | 说明 |
| --- | --- |
| [Circuit Breaker](examples/reliability/circuit_breaker/) | 本配方展示了使用简单的内存熔断器保护下游 API 的 HTTP 触发 Azure Function。 |
| [Outbox Pattern](examples/reliability/outbox_pattern/) | 面向 Azure Functions Python 的事务性发件箱示例，其中: |
| [Poison Message Handling](examples/reliability/poison_message_handling/) | 让重复失败自动移动到毒消息队列、随后记录失败负载以便运维跟进的队列触发 Azure Functions 配方。 |
| [Rate Limiting / Throttle](examples/reliability/rate_limiting/) | 本配方展示了使用内存令牌桶对请求进行限流、并在本地桶为空时返回 `429 Too Many Requests` 的 HTTP 触发 Azure Function。 |
| [Retry and Idempotency](examples/reliability/retry_and_idempotency/) | 本配方展示了两个相关的弹性模式: |

### Security and Tenancy

| 配方 | 说明 |
| --- | --- |
| [Managed Identity Service Bus](examples/security-and-tenancy/managed_identity_servicebus/) | 本配方展示了使用 `connection="ServiceBusConnection"` 的 Service Bus 队列触发器。 |
| [Managed Identity Storage](examples/security-and-tenancy/managed_identity_storage/) | 本配方展示了使用 `connection="StorageConnection"` 的 Azure Storage Queue 触发器。该设置可由连接字符串或托管标识设置来支撑。 |
| [Secretless Key Vault](examples/security-and-tenancy/secretless_keyvault/) | 从由 Azure Key Vault 引用填充的环境变量中读取机密的 HTTP 触发 Azure Function。该函数仅使用标准环境访问和 `azure_functions_logging`。 |
| [Tenant Isolation](examples/security-and-tenancy/tenant_isolation/) | 从 `X-Tenant-ID` 或 Bearer 令牌声明解析租户上下文、随后使用 `azure-functions-db-python` 查询特定租户数据库的 HTTP 配方。 |

### Runtime and Ops

| 配方 | 说明 |
| --- | --- |
| [Blueprint Modular App](examples/runtime-and-ops/blueprint_modular_app/) | 本配方演示了使用 `func.Blueprint` 的模块化 Azure Functions 应用。 |
| [Cold Start Mitigation](examples/runtime-and-ops/cold_start_mitigation/) | 本配方演示了 Azure Functions Python 的实用冷启动缓解: |
| [Concurrency Tuning](examples/runtime-and-ops/concurrency_tuning/) | 本配方演示了主机级动态并发: |
| [Doctor Diagnostics Endpoint](examples/runtime-and-ops/doctor_diagnostics_endpoint/) | 将 [`azure-functions-doctor`](https://github.com/yeongseon/azure-functions-doctor-python) 诊断作为经过身份验证的 HTTP 端点公开，使运维人员无需进入容器即可在部署后查询部署健康状况。 |
| [Observability Tracing](examples/runtime-and-ops/observability_tracing/) | 演示关联 ID 传播、结构化日志和适配 Application Insights 的跟踪上下文的 HTTP 触发跟踪配方。 |
| [Output Binding vs SDK](examples/runtime-and-ops/output_binding_vs_sdk/) | 本配方比较了发送同一队列消息的两种方式: |
| [host.json Tuning](examples/runtime-and-ops/host_json_tuning/) | 本配方聚焦于使用计时器触发器加上丰富配置的 `host.json` 进行主机级调优。 |

### Realtime

| 配方 | 说明 |
| --- | --- |
| [WebSocket Proxy](examples/realtime/websocket_proxy/) | 为 Azure Web PubSub 协商客户端令牌并转发发布请求的 Azure Functions 前门。 |

### AI and Agents

| 配方 | 说明 |
| --- | --- |
| [AI Image Generation](examples/ai-and-agents/ai_image_generation/) | 向 Azure OpenAI 图像生成发送提示并返回生成图像 URL 的 HTTP 触发示例。 |
| [Azure OpenAI Direct Chat](examples/ai-and-agents/openai_direct_chat/) | 使用 `openai` Python SDK 向 Azure OpenAI 发送一条消息的最小化 HTTP 触发 Azure Functions 示例。 |
| [Durable AI Pipeline](examples/ai-and-agents/durable_ai_pipeline/) | 编排嵌入、向量搜索和答案生成三个 AI 步骤的 Durable Functions 示例。 |
| [Embedding Vector Search](examples/ai-and-agents/embedding_vector_search/) | 创建 Azure OpenAI 嵌入并使用其对 Azure AI Search 运行向量查询的 HTTP 触发示例。 |
| [Knowledge Notion Search](examples/ai-and-agents/knowledge_notion_search/) | 使用 azure-functions-knowledge 的 KnowledgeBindings input/inject_client 装饰器实现的基于 Notion 的知识检索。 |
| [LangGraph Agent](examples/ai-and-agents/langgraph_agent/) | 演示 `azure-functions-langgraph-python` 适配器与 `azure-functions-logging-python`、`azure-functions-validation-python` 和 `azure-functions-openapi-python` 的结合。 |
| [LangGraph RAG Agent](examples/ai-and-agents/langgraph_rag_agent/) | 本示例展示了如何组合: |
| [Langgraph Tool Use](examples/ai-and-agents/langgraph_tool_use/) | 在推理节点与可调用工具之间路由的、基于 azure-functions-langgraph 的工具使用 LangGraph 智能体。 |
| [MCP Server Example](examples/ai-and-agents/mcp_server_example/) | 本示例使用标准 HTTP 触发器和 JSON-RPC 2.0 消息在 Azure Functions 上托管一个手动的 Model Context Protocol (MCP) 服务器。 |
| [RAG Knowledge API](examples/ai-and-agents/rag_knowledge_api/) | 演示使用 Azure AI Search 和 Azure OpenAI，并结合 `azure-functions-validation-python`、`azure-functions-openapi-python` 和 `azure-functions-logging-python` 的最小化 RAG API。 |
| [Streaming AI Response](examples/ai-and-agents/streaming_ai_response/) | 将 Azure OpenAI 流式聊天补全转换为 Server-Sent Events 的 HTTP 触发示例。 |

### Guides

| 配方 | 说明 |
| --- | --- |
| [Local Run and Direct Invoke](examples/guides/local_run_and_direct_invoke/) | 本示例展示了 Azure Functions Python 应用的两种本地测试工作流: |

_80 个配方。每个配方的难度标签在 [#117](https://github.com/yeongseon/azure-functions-cookbook-python/issues/117) 中跟踪。_

每个模式页面位于 `docs/patterns/` 下，并在 `examples/` 中有对应的可运行项目。

## Running Examples

每个配方都可使用 Azure Functions Core Tools 在本地运行。大多数触发器可用
[Azurite](https://learn.microsoft.com/azure/storage/common/storage-use-azurite) 模拟；
少数需要真实的云服务或 API 密钥。下表按分类列出外部
依赖以及在没有实时服务的情况下如何运行。

<details>
<summary><strong>Local emulation cheat sheet</strong> — 各分类的外部依赖及本地运行方式</summary>

| 分类 | 外部服务 | 本地运行方式 |
| --- | --- | --- |
| APIs and Ingress | 无（纯 HTTP） | `func start` — 无需模拟器 |
| Scheduled and Background | Storage（计时器/队列状态） | Azurite (`AzureWebJobsStorage=UseDevelopmentStorage=true`) |
| Blob and File Triggers | Azure Storage / Event Grid | Blob 用 Azurite；Event Grid 触发器需要真实订阅或重放的负载 |
| Async APIs and Jobs | Storage Queue | Azurite |
| Messaging and Pub/Sub | Service Bus / Event Grid / Storage Queue | Storage Queue 用 Azurite；Service Bus 和 Event Grid 需要真实命名空间 |
| Streams and Telemetry | Event Hubs | 真实的 Event Hubs 命名空间（无本地模拟器） |
| Data and Pipelines | Cosmos DB / SQL / Storage | DB 配方用 Azurite 或 SQLite；Cosmos 更改源需要真实账户 |
| Orchestration and Workflows | Durable Functions（Storage） | Azurite（Durable 任务中心） |
| Reliability | Storage Queue | Azurite |
| Security and Tenancy | Managed Identity / Key Vault / Service Bus | 本地开发使用连接字符串；标识路径需要 Azure |
| Runtime and Ops | 无 / Storage | `func start`；部分使用 Azurite |
| Realtime | Web PubSub / SignalR | 真实的 Web PubSub 服务 |
| AI and Agents | Azure OpenAI / Azure AI Search | 默认针对本地桩运行；为真实服务设置端点/密钥环境变量 |
| Guides | 无 | `func start` |

</details>

每个示例的 `README.md` 都记录了其特定的 `local.settings.json` 值。
AI 示例附带本地回退桩，因此无需凭据即可运行 — 请参阅
每个配方的 README，了解切换到真实服务的环境变量。

### Test tiers

测试按 pytest 标记分离，因此默认可运行快速层级，
并显式选择更重的层级:

- **unit**（默认） — `make test`；无外部服务，无模拟器。
- **smoke** — `hatch run smoke`；针对不可模拟触发器的模块导入检查。
- **e2e** — `hatch run e2e`；需要 Azurite 和运行中的 `func` 主机。

## Repository Layout

```text
docs/              已发布文档
  patterns/        精选的模式文档
examples/          按分类组织的可运行示例项目
  apis-and-ingress/
  scheduled-and-background/
  blob-and-file-triggers/
  async-apis-and-jobs/
  messaging-and-pubsub/
  streams-and-telemetry/
  data-and-pipelines/
  orchestration-and-workflows/
  reliability/
  security-and-tenancy/
  runtime-and-ops/
  realtime/
  ai-and-agents/
  guides/
```

## Development

```bash
git clone https://github.com/yeongseon/azure-functions-cookbook-python.git
cd azure-functions-cookbook-python
make install
make check-all
make docs
```

## Documentation

- 产品需求: `PRD.md`
- 设计原则: `DESIGN.md`
- 贡献指南: `CONTRIBUTING.md`

## Ecosystem

本手册是 **Azure Functions Python DX Toolkit** 的 **dogfood（自用验证）** — 每个示例都是在贴近生产的场景中使用工具包库的真实可运行 Azure Function。如果某个库在手册中可用，那么它在真实环境中也可用。

**Status** 列反映了每个包当前在本仓库中的使用情况: **Dogfooded**（被真实示例导入并运行）、**Experimental**（已宣传但尚未被任何示例使用）或 **Planned**（已跟踪集成但尚未开始）。计数为导入该包的示例项目数量，但对于 CLI 工具（例如脚手架生成器），计数反映的是由 CLI 生成或驱动的示例数量，而非直接导入。

| 包 | 作用 | Status |
|---------|------|--------|
| [azure-functions-openapi-python](https://github.com/yeongseon/azure-functions-openapi-python) | OpenAPI 规范生成与 Swagger UI | Dogfooded ([24 个示例](https://github.com/search?q=repo%3Ayeongseon%2Fazure-functions-cookbook-python+azure_functions_openapi+path%3Aexamples&type=code)) |
| [azure-functions-validation-python](https://github.com/yeongseon/azure-functions-validation-python) | 请求/响应校验与序列化 | Dogfooded ([23 个示例](https://github.com/search?q=repo%3Ayeongseon%2Fazure-functions-cookbook-python+azure_functions_validation+path%3Aexamples&type=code)) |
| [azure-functions-logging-python](https://github.com/yeongseon/azure-functions-logging-python) | 结构化日志与可观测性 | Dogfooded ([41 个示例](https://github.com/search?q=repo%3Ayeongseon%2Fazure-functions-cookbook-python+azure_functions_logging+path%3Aexamples&type=code)) |
| [azure-functions-db-python](https://github.com/yeongseon/azure-functions-db-python) | 基于 SQLAlchemy 的 DB 集成助手（基于轮询的伪触发器，输入/输出/客户端注入） | Dogfooded ([9 个示例](https://github.com/search?q=repo%3Ayeongseon%2Fazure-functions-cookbook-python+azure_functions_db+path%3Aexamples&type=code)) |
| [azure-functions-langgraph-python](https://github.com/yeongseon/azure-functions-langgraph-python) | 面向 Azure Functions 的 LangGraph 部署适配器 | Dogfooded ([3 个示例](https://github.com/search?q=repo%3Ayeongseon%2Fazure-functions-cookbook-python+azure_functions_langgraph+path%3Aexamples&type=code)) |
| [azure-functions-scaffold-python](https://github.com/yeongseon/azure-functions-scaffold-python) | 项目脚手架 CLI | Dogfooded ([1 个示例，CLI 生成](examples/apis-and-ingress/scaffold_walkthrough_app/)) |
| [azure-functions-doctor-python](https://github.com/yeongseon/azure-functions-doctor-python) | 部署前诊断 CLI | Dogfooded ([1 个示例](https://github.com/search?q=repo%3Ayeongseon%2Fazure-functions-cookbook-python+azure_functions_doctor+path%3Aexamples&type=code)) |
| [azure-functions-durable-graph-python](https://github.com/yeongseon/azure-functions-durable-graph-python) | 基于 Durable Functions 的清单优先图运行时 *(实验性)* | Dogfooded ([1 个示例](examples/orchestration-and-workflows/durable_graph_fan_out/) — `durable_graph_fan_out`) |
| [azure-functions-knowledge-python](https://github.com/yeongseon/azure-functions-knowledge-python) | 知识检索（RAG）装饰器 | Dogfooded ([1 个示例](examples/ai-and-agents/knowledge_notion_search/) — `knowledge_notion_search` 使用真实的 `KnowledgeBindings` API) |
| **azure-functions-cookbook-python** *(本仓库)* | 面向整个工具包的 dogfood 示例 | [80 个示例](examples/) |

## For AI Coding Assistants

本仓库在根目录中包含 `llms.txt` 和 `llms-full.txt` — 针对 LLM 上下文窗口优化的快速参考和完整参考。在 AI 辅助编码环境中处理这些配方时，可用它们获得更好的上下文。

## Disclaimer

本项目是一个独立的社区项目，与 Microsoft 无关，
也未获得 Microsoft 的认可或维护。

Azure 和 Azure Functions 是 Microsoft Corporation 的商标。

## License

MIT
