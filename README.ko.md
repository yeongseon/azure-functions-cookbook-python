# Azure Functions Python Cookbook

[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue)](https://github.com/yeongseon/azure-functions-cookbook-python)
[![CI](https://github.com/yeongseon/azure-functions-cookbook-python/actions/workflows/ci-smoke.yml/badge.svg)](https://github.com/yeongseon/azure-functions-cookbook-python/actions/workflows/ci-smoke.yml)
[![Docs](https://github.com/yeongseon/azure-functions-cookbook-python/actions/workflows/docs.yml/badge.svg)](https://github.com/yeongseon/azure-functions-cookbook-python/actions/workflows/docs.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

다른 언어: [English](README.md) | [日本語](README.ja.md) | [简体中文](README.zh-CN.md)

Python으로 실제 서비스 가능한 Azure Functions를 구축하기 위한 실용적인 레시피 모음입니다.

## Why Use It

새로운 Azure Functions 프로젝트를 시작할 때 흩어져 있는 문서나 블로그 포스트, 샘플 코드를 일일이 찾아 맞추는 일은 번거롭습니다. 이 쿡북은 다음과 같은 질문에 답이 되는 엄선된 실행 가능한 레시피를 제공합니다.

- 이 시나리오에서는 무엇을 구축해야 할까?
- 아키텍처는 어떤 모습이어야 할까?
- 검증된 기본 코드에서 어떻게 시작할 수 있을까?

## Scope

- Azure Functions Python **v2 프로그래밍 모델**
- 데코레이터 기반 `func.FunctionApp()` 애플리케이션
- 실행 가능한 예제가 포함된 실용적인 레시피
- 아키텍처 설명 및 운영 시 고려사항

이 저장소는 콘텐츠 중심으로 구성되었습니다. CLI 도구가 아닙니다.

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

각 패턴 문서는 `docs/patterns/` 아래에 있으며, 대응하는 실행 가능한 예제는 `examples/`에 있습니다.

## Repository Layout

```text
docs/              게시된 문서
  patterns/        엄선된 패턴 문서 (67개 레시피)
examples/          카테고리별 실행 가능한 예제 프로젝트
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

- 제품 요구사항: `PRD.md`
- 설계 원칙: `DESIGN.md`
- 기여 가이드: `CONTRIBUTING.md`

## Ecosystem

이 쿡북은 **Azure Functions Python DX Toolkit**의 **도그푸드**입니다 — 모든 예제는 프로덕션에 가까운 시나리오에서 툴킷 라이브러리를 사용하는 실제 실행 가능한 Azure Function입니다. 쿡북에서 동작하는 라이브러리는 실제 환경에서도 동작합니다.

**Status** 열은 각 패키지가 이 저장소에서 현재 어떻게 활용되는지를 나타냅니다: **Dogfooded**(실제 예제에서 임포트되어 실행됨), **Experimental**(소개되었으나 아직 어떤 예제에서도 활용되지 않음), **Planned**(통합이 추적되고 있으나 아직 시작되지 않음). 개수는 해당 패키지를 임포트하는 예제 프로젝트의 수이며, CLI 도구(예: 스캐폴드 생성기)의 경우 직접 임포트가 아니라 CLI로 생성되거나 구동되는 예제의 수를 반영합니다.

| 패키지 | 역할 | Status |
|---------|------|--------|
| [azure-functions-openapi-python](https://github.com/yeongseon/azure-functions-openapi-python) | OpenAPI 스펙 생성 및 Swagger UI | Dogfooded (예제 24개) |
| [azure-functions-validation-python](https://github.com/yeongseon/azure-functions-validation-python) | 요청/응답 검증 및 직렬화 | Dogfooded (예제 23개) |
| [azure-functions-logging-python](https://github.com/yeongseon/azure-functions-logging-python) | 구조화된 로깅 및 관측성 | Dogfooded (예제 41개) |
| [azure-functions-db-python](https://github.com/yeongseon/azure-functions-db-python) | SQLAlchemy 기반 DB 통합 헬퍼 (폴링 기반 의사 트리거, 입력/출력/클라이언트 주입) | Dogfooded (예제 9개) |
| [azure-functions-langgraph-python](https://github.com/yeongseon/azure-functions-langgraph-python) | Azure Functions용 LangGraph 배포 어댑터 | Dogfooded (예제 2개) |
| [azure-functions-scaffold-python](https://github.com/yeongseon/azure-functions-scaffold-python) | 프로젝트 스캐폴딩 CLI | Dogfooded (예제 1개, CLI 생성) |
| [azure-functions-doctor-python](https://github.com/yeongseon/azure-functions-doctor-python) | 배포 전 진단 CLI | Dogfooded (예제 1개) |
| [azure-functions-durable-graph-python](https://github.com/yeongseon/azure-functions-durable-graph-python) | Durable Functions 기반 매니페스트 우선 그래프 런타임 *(실험적)* | Experimental — 아직 도그푸드되지 않음 ([#76](https://github.com/yeongseon/azure-functions-cookbook-python/issues/76)) |
| [azure-functions-knowledge-python](https://github.com/yeongseon/azure-functions-knowledge-python) | 지식 검색(RAG) 데코레이터 | Experimental — `rag_knowledge_api`는 실제 라이브러리가 아닌 로컬 스텁을 사용함 ([#76](https://github.com/yeongseon/azure-functions-cookbook-python/issues/76)) |
| **azure-functions-cookbook-python** *(이 저장소)* | 전체 툴킷을 위한 도그푸드 예제 | 예제 77개 |

## Disclaimer

본 프로젝트는 독립적인 커뮤니티 프로젝트이며, Microsoft와 제휴하거나 Microsoft의 보증 또는 지원을 받지 않습니다.

Azure 및 Azure Functions는 Microsoft Corporation의 상표입니다.

## License

MIT
