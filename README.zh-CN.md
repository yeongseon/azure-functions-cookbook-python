# Azure Functions Python Cookbook

[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue)](https://github.com/yeongseon/azure-functions-cookbook-python)
[![CI](https://github.com/yeongseon/azure-functions-cookbook-python/actions/workflows/ci-smoke.yml/badge.svg)](https://github.com/yeongseon/azure-functions-cookbook-python/actions/workflows/ci-smoke.yml)
[![Docs](https://github.com/yeongseon/azure-functions-cookbook-python/actions/workflows/docs.yml/badge.svg)](https://github.com/yeongseon/azure-functions-cookbook-python/actions/workflows/docs.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

其他语言: [English](README.md) | [한국어](README.ko.md) | [日本語](README.ja.md)

使用 Python 构建实际 Azure Functions 的实用食谱集合。

## Why Use It

启动新的 Azure Functions 项目时，往往需要整合零散的文档、博客文章和示例代码。本食谱提供精选的、可运行的示例，旨在回答：

- 针对此场景我应该构建什么？
- 架构应该是什么样的？
- 我如何从一个可工作的基准开始？

## Scope

- Azure Functions Python **v2 编程模型**
- 基于装饰器的 `func.FunctionApp()` 应用程序
- 包含可运行示例的实用食谱
- 架构说明和生产环境注意事项

本仓库以内容为主，不是 CLI 工具。

## Recipes

### HTTP

| Recipe | Difficulty | Description |
| --- | --- | --- |
| Hello HTTP Minimal | Beginner | Smallest possible HTTP trigger |
| HTTP Routing, Query, and Body | Beginner | Route params, query strings, JSON body, status codes |
| HTTP Auth Levels | Beginner | Anonymous, Function, and Admin auth levels |
| GitHub Webhook | Intermediate | HMAC-SHA256 signature verification |
| EasyAuth Claims | Intermediate | EasyAuth principal extraction with role-based access control |
| JWT Bearer Validation | Intermediate | JWT Bearer token validation with claim-based access control |
| Multi-Tenant Auth | Intermediate | Multi-tenant access control with tenant allowlist |

### Timer

| Recipe | Difficulty | Description |
| --- | --- | --- |
| Timer Cron Job | Beginner | NCRONTAB expressions, timezone, catch-up |

### Queue

| Recipe | Difficulty | Description |
| --- | --- | --- |
| Queue Producer | Beginner | HTTP trigger with Queue output binding |
| Queue Consumer | Beginner | Queue trigger message processing |

### Blob

| Recipe | Difficulty | Description |
| --- | --- | --- |
| Blob Upload Processor | Intermediate | Polling-based blob trigger |
| Blob Event Grid Trigger | Intermediate | Event Grid-based blob trigger (faster) |

### Service Bus

| Recipe | Difficulty | Description |
| --- | --- | --- |
| Service Bus Worker | Intermediate | Service Bus queue trigger |

### Event Hub

| Recipe | Difficulty | Description |
| --- | --- | --- |
| Event Hub Consumer | Intermediate | Event Hub stream processing |

### Cosmos DB

| Recipe | Difficulty | Description |
| --- | --- | --- |
| Change Feed Processor | Intermediate | Cosmos DB change feed trigger |

### Patterns

| Recipe | Difficulty | Description |
| --- | --- | --- |
| Blueprint Modular App | Intermediate | Modular function apps with Blueprints |
| Retry and Idempotency | Intermediate | Retry policies and idempotency patterns |
| Output Binding vs SDK | Intermediate | Side-by-side binding vs SDK client comparison |
| Managed Identity (Storage) | Advanced | Identity-based Storage connection |
| Managed Identity (Service Bus) | Advanced | Identity-based Service Bus connection |
| host.json Tuning | Advanced | host.json configuration guide |
| Concurrency Tuning | Advanced | Dynamic concurrency for Queue/Blob/Service Bus |

### Durable Functions

| Recipe | Difficulty | Description |
| --- | --- | --- |
| Hello Sequence | Beginner | Activity chaining pattern |
| Fan-Out / Fan-In | Intermediate | Parallel activity execution |
| Human Interaction | Intermediate | External events with timeout |
| Entity Counter | Intermediate | Durable entity state management |
| Retry Pattern | Intermediate | Activity retry with RetryOptions |
| Determinism Gotchas | Advanced | Orchestrator determinism rules |
| Unit Testing | Intermediate | Mock-based orchestrator testing |

### AI

| Recipe | Difficulty | Description |
| --- | --- | --- |
| MCP Server | Advanced | Model Context Protocol server on Azure Functions |

### Local Development

| Recipe | Difficulty | Description |
| --- | --- | --- |
| Local Run and Direct Invoke | Beginner | func start vs direct Python invocation |

每个模式页面都位于 `docs/patterns/` 目录下，对应的可运行项目在 `examples/` 中。

## Repository Layout

```text
docs/              发布的文档
  patterns/        精选模式文档（67个食谱）
examples/          按类别组织的可运行示例项目
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

本手册是 **Azure Functions Python DX Toolkit** 的 **内部实践（dogfood）** —— 每个示例都是在接近生产的场景中使用工具链库的真实、可运行的 Azure Function。在手册中能用的库，在真实环境中也能用。

**Status** 列反映每个包在本仓库中当前的实际使用情况：**Dogfooded**（被真实示例导入并运行）、**Experimental**（已介绍但尚未被任何示例使用）、**Planned**（已跟踪集成但尚未开始）。计数为导入该包的示例项目数量；对于 CLI 工具（例如脚手架生成器），计数反映由 CLI 生成或驱动的示例数量，而非直接导入。

| 包 | 职责 | Status |
|---------|------|--------|
| [azure-functions-openapi-python](https://github.com/yeongseon/azure-functions-openapi-python) | OpenAPI 规范生成与 Swagger UI | Dogfooded（24 个示例） |
| [azure-functions-validation-python](https://github.com/yeongseon/azure-functions-validation-python) | 请求/响应校验与序列化 | Dogfooded（23 个示例） |
| [azure-functions-logging-python](https://github.com/yeongseon/azure-functions-logging-python) | 结构化日志与可观测性 | Dogfooded（41 个示例） |
| [azure-functions-db-python](https://github.com/yeongseon/azure-functions-db-python) | 基于 SQLAlchemy 的数据库集成助手（基于轮询的伪触发器，输入/输出/客户端注入） | Dogfooded（9 个示例） |
| [azure-functions-langgraph-python](https://github.com/yeongseon/azure-functions-langgraph-python) | 面向 Azure Functions 的 LangGraph 部署适配器 | Dogfooded（2 个示例） |
| [azure-functions-scaffold-python](https://github.com/yeongseon/azure-functions-scaffold-python) | 项目脚手架 CLI | Dogfooded（1 个示例，CLI 生成） |
| [azure-functions-doctor-python](https://github.com/yeongseon/azure-functions-doctor-python) | 部署前诊断 CLI | Dogfooded（1 个示例） |
| [azure-functions-durable-graph-python](https://github.com/yeongseon/azure-functions-durable-graph-python) | 基于 Durable Functions 的清单优先图运行时 *(实验性)* | Experimental —— 尚未内部实践 ([#76](https://github.com/yeongseon/azure-functions-cookbook-python/issues/76)) |
| [azure-functions-knowledge-python](https://github.com/yeongseon/azure-functions-knowledge-python) | 知识检索（RAG）装饰器 | Experimental —— `rag_knowledge_api` 使用本地桩而非真实库 ([#76](https://github.com/yeongseon/azure-functions-cookbook-python/issues/76)) |
| **azure-functions-cookbook-python** *(本仓库)* | 面向完整工具链的内部实践示例 | 77 个示例 |

## Disclaimer

本项目是一个独立的社区项目，不隶属于 Microsoft，也不受其认可或维护。

Azure 和 Azure Functions 是 Microsoft Corporation 的商标。

## License

MIT
