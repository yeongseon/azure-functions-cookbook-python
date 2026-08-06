# Azure Functions Python Cookbook

[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue)](https://github.com/yeongseon/azure-functions-cookbook-python)
[![CI](https://github.com/yeongseon/azure-functions-cookbook-python/actions/workflows/ci-smoke.yml/badge.svg)](https://github.com/yeongseon/azure-functions-cookbook-python/actions/workflows/ci-smoke.yml)
[![codecov](https://codecov.io/gh/yeongseon/azure-functions-cookbook-python/branch/main/graph/badge.svg)](https://codecov.io/gh/yeongseon/azure-functions-cookbook-python)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://pre-commit.com/)
[![Docs](https://github.com/yeongseon/azure-functions-cookbook-python/actions/workflows/docs.yml/badge.svg)](https://github.com/yeongseon/azure-functions-cookbook-python/actions/workflows/docs.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

다른 언어로 읽기: [한국어](README.ko.md) | [日本語](README.ja.md) | [简体中文](README.zh-CN.md)

Python으로 실제 프로덕션 수준의 Azure Functions를 구축하기 위한 실용적인 레시피 모음입니다.

## Why Use It

새로운 Azure Functions 프로젝트를 시작하려면 흩어져 있는 문서, 블로그 게시물,
샘플 코드를 짜맞춰야 하는 경우가 많습니다. 이 쿡북은 다음 질문에 답하는, 큐레이팅된 실행 가능한 레시피를 제공합니다:

- 이 시나리오에서 무엇을 만들어야 하는가?
- 아키텍처는 어떻게 구성해야 하는가?
- 동작하는 기준점에서 어떻게 시작하는가?

## Scope

- Azure Functions Python **v2 프로그래밍 모델**
- 데코레이터 기반 `func.FunctionApp()` 애플리케이션
- 실행 가능한 예제를 갖춘 실용적인 레시피
- 아키텍처 설명 및 프로덕션 노트

이 저장소는 콘텐츠 중심입니다. CLI 도구가 아닙니다.

## Quick Index

카테고리로 이동: [APIs and Ingress](#apis-and-ingress) · [Scheduled and Background](#scheduled-and-background) · [Blob and File Triggers](#blob-and-file-triggers) · [Async APIs and Jobs](#async-apis-and-jobs) · [Messaging and Pub/Sub](#messaging-and-pubsub) · [Streams and Telemetry](#streams-and-telemetry) · [Data and Pipelines](#data-and-pipelines) · [Orchestration and Workflows](#orchestration-and-workflows) · [Reliability](#reliability) · [Security and Tenancy](#security-and-tenancy) · [Runtime and Ops](#runtime-and-ops) · [Realtime](#realtime) · [AI and Agents](#ai-and-agents) · [Guides](#guides)

---

## Recipes

### APIs and Ingress

| 레시피 | 설명 |
| --- | --- |
| [APIM Function Backend](examples/apis-and-ingress/apim_function_backend/) | 인증, 속도 제한, 캐싱을 위한 Azure API Management 정책 뒤에 배치하도록 설계된 HTTP 트리거 Azure Functions 백엔드. |
| [BFF Facade API](examples/apis-and-ingress/bff_facade_api/) | 여러 백엔드 서비스 호출을 하나의 클라이언트 대상 응답으로 집계하는 HTTP Backend-for-Frontend 파사드. |
| [EasyAuth Claims Extraction](examples/apis-and-ingress/auth_easyauth/) | Azure Functions용 역할 기반 액세스 제어를 갖춘 EasyAuth 주체(principal) 추출. |
| [Full Stack CRUD API](examples/apis-and-ingress/full_stack_crud_api/) | 하나의 `items` 리소스를 중심으로 Azure Functions Python DX Toolkit을 연결하는 쇼케이스 HTTP API. |
| [HTTP Auth Levels](examples/apis-and-ingress/http_auth_levels/) | 익명, 함수 키, 관리자 키 엔드포인트를 보여주는 HTTP 트리거 예제. |
| [HTTP Routing Query Body](examples/apis-and-ingress/http_routing_query_body/) | 라우트 파라미터, 쿼리 문자열, JSON 본문 파싱, 상태 코드를 보여주는 HTTP CRUD 및 검색 예제. |
| [Hello HTTP Minimal](examples/apis-and-ingress/hello_http_minimal/) | 인사말을 반환하는 최소한의 HTTP 트리거 Azure Function. |
| [JWT Bearer Validation](examples/apis-and-ingress/auth_jwt_validation/) | Azure Functions용 클레임 기반 액세스 제어를 갖춘 JWT Bearer 토큰 검증. |
| [Multi-Tenant Auth](examples/apis-and-ingress/auth_multitenant/) | Azure Functions용 테넌트 허용 목록을 사용한 멀티테넌트 액세스 제어. |
| [Scaffold Walkthrough — from afs new to a running HTTP API](examples/apis-and-ingress/scaffold_walkthrough_app/) | 이 레시피는 기본 `strict` 프리셋을 사용한 **`azure-functions-scaffold`의 커밋된 출력**입니다. 스캐폴드 CLI가 새로운 Azure Functions Python v2 HTTP 프로젝트에 대해 정확히 무엇을 생성하는지 확인하고 권장 로컬 개발 루프를 익히는 데 사용하세요. |
| [Webhook GitHub](examples/apis-and-ingress/webhook_github/) | HMAC-SHA256 서명 검증을 갖춘 GitHub 웹훅 수신기 예제. |

### Scheduled and Background

| 레시피 | 설명 |
| --- | --- |
| [Durable Timer Reminder](examples/scheduled-and-background/durable_timer_reminder/) | 긴 지연을 기다린 후 리마인더 콜백 액티비티를 실행하는 Durable Functions 오케스트레이션. |
| [Queue Scheduled Dispatch](examples/scheduled-and-background/queue_scheduled_dispatch/) | 만기 작업을 다운스트림 워커를 위해 Azure Storage Queue로 방출하는 타이머 기반 예약 디스패치 패턴. |
| [Timer Cron Job](examples/scheduled-and-background/timer_cron_job/) | 5분마다 예약된 유지 관리 작업을 실행하는 타이머 트리거 Azure Function. |

### Blob and File Triggers

| 레시피 | 설명 |
| --- | --- |
| [Blob CSV to Table](examples/blob-and-file-triggers/blob_csv_to_table/) | 업로드된 CSV 블롭을 읽어 정규화된 행을 Azure Table Storage에 기록하는 Event Grid 기반 수집 패턴. |
| [Blob Event Grid Trigger](examples/blob-and-file-triggers/blob_eventgrid_trigger/) | Event Grid 소스 알림용으로 구성된 블롭 트리거 Azure Function. |
| [Blob Thumbnail Generator](examples/blob-and-file-triggers/blob_thumbnail_generator/) | 썸네일을 생성하여 별도의 출력 컨테이너에 기록하는 Event Grid 기반 블롭 처리기. |
| [Blob Upload Processor](examples/blob-and-file-triggers/blob_upload_processor/) | `uploads/{name}`에서 업로드된 파일을 처리하는 블롭 트리거 Azure Function. |

### Async APIs and Jobs

| 레시피 | 설명 |
| --- | --- |
| [Async HTTP 202 Polling](examples/async-apis-and-jobs/async_http_polling/) | `202 Accepted`와 클라이언트 폴링용 `statusQueryGetUri`를 반환하는 HTTP 트리거 Durable Functions 예제. |
| [Callback Completion](examples/async-apis-and-jobs/callback_completion/) | `/api/tasks`에서 작업을 수락하고 백그라운드 처리가 끝나면 HTTP 콜백을 보내는 HTTP + Queue 예제. |
| [Queue-Backed Job](examples/async-apis-and-jobs/queue_backed_job/) | 작업을 수락하고 `202 Accepted`를 반환한 뒤 저장된 상태 레코드를 폴링하는 HTTP + Storage Queue 레시피. |

### Messaging and Pub/Sub

| 레시피 | 설명 |
| --- | --- |
| [Claim Check Pattern](examples/messaging-and-pubsub/claim_check_pattern/) | 페이로드를 Blob Storage에 저장하고 큐에는 참조만 전달하는 대용량 메시지 패턴. |
| [Event Grid Domain Events](examples/messaging-and-pubsub/eventgrid_domain_events/) | 사용자 지정 주문 도메인 이벤트를 Event Grid 사용자 지정 토픽에 게시하는 HTTP 트리거 Azure Function과, 그 결과 이벤트를 로깅하는 Event Grid 트리거 구독자. |
| [Event Grid Event Router](examples/messaging-and-pubsub/eventgrid_router/) | 이벤트 유형 및 제목 필터를 사용하여 이벤트를 서로 다른 핸들러로 라우팅하는 Event Grid 트리거 Azure Function. |
| [Queue Consumer](examples/messaging-and-pubsub/queue_consumer/) | 작업 메시지를 파싱하고 처리하는 큐 트리거 Azure Function. |
| [Queue Producer](examples/messaging-and-pubsub/queue_producer/) | JSON을 검증하고 작업을 Storage Queue에 큐잉하는 HTTP 트리거 Azure Function. |
| [Service Bus DLQ Replay](examples/messaging-and-pubsub/servicebus_dlq_replay/) | 검사 및 교정 후 데드레터된 Service Bus 큐 메시지를 메인 큐로 다시 재생. |
| [Service Bus Sessions](examples/messaging-and-pubsub/servicebus_sessions/) | Azure Service Bus 세션을 사용한 순서 보장 메시지 처리를 보여주는 Azure Functions 예제. |
| [Service Bus Topic Fan-out](examples/messaging-and-pubsub/servicebus_topic_fanout/) | 세 개의 독립적인 구독 핸들러로 Service Bus 토픽 팬아웃을 보여주는 Azure Functions 예제. |
| [Service Bus Worker](examples/messaging-and-pubsub/servicebus_worker/) | 안정적인 백그라운드 작업 소비를 위한 Service Bus 큐 트리거 Azure Function. |

### Streams and Telemetry

| 레시피 | 설명 |
| --- | --- |
| [Event Hub Batch Window](examples/streams-and-telemetry/eventhub_batch_window/) | 배치 윈도우를 처리하고 집계 텔레메트리 합계를 로깅하는 Event Hub 트리거 Azure Function. |
| [Event Hub Checkpoint Replay](examples/streams-and-telemetry/eventhub_checkpoint_replay/) | 오프셋 추적 및 멱등 처리로 재생 인식 Event Hub 소비를 보여주는 Azure Functions 예제. |
| [Event Hub Consumer](examples/streams-and-telemetry/eventhub_consumer/) | 준실시간 텔레메트리 스트림 처리를 위한 Event Hub 트리거 Azure Function. |

### Data and Pipelines

| 레시피 | 설명 |
| --- | --- |
| [CQRS Read Projection](examples/data-and-pipelines/cqrs_read_projection/) | 다음과 같은 특징을 가진 Azure Functions Python용 CQRS 샘플: |
| [Change Feed Processor](examples/data-and-pipelines/change_feed_processor/) | 다운스트림 동기화를 위한 Cosmos DB 변경 피드 트리거 Azure Function. |
| [DB Input and Output Bindings](examples/data-and-pipelines/db_input_output/) | SQLAlchemy 기반 저장소와 함께 `azure-functions-db-python` 입출력 바인딩을 `azure-functions-validation-python` 및 `azure-functions-openapi-python`과 결합하여 보여줍니다. |
| [ETL Enrichment](examples/data-and-pipelines/etl_enrichment/) | 원시 JSON 고객 레코드를 읽어 조회 데이터로 보강하고 보강된 행을 데이터베이스에 기록하는 블롭 트리거 ETL 예제. |
| [File Processing Pipeline](examples/data-and-pipelines/file_processing_pipeline/) | 업로드된 CSV 또는 JSON 파일을 검증하고 레코드를 변환하여 처리 결과를 데이터베이스에 저장하는 블롭 트리거 Azure Function. |
| [SQLAlchemy REST Pagination](examples/data-and-pipelines/sqlalchemy_rest_pagination/) | 다음을 결합한 HTTP API 예제: |

### Orchestration and Workflows

| 레시피 | 설명 |
| --- | --- |
| [Async Job Lifecycle](examples/orchestration-and-workflows/async_job_lifecycle/) | 생성, 상태, 취소, 정리를 포함한 완전한 비동기 작업 수명 주기 관리를 위한 Durable Functions 레시피. |
| [Durable Determinism Gotchas](examples/orchestration-and-workflows/durable_determinism_gotchas/) | 결정적 코딩 패턴을 보여주는 Durable Functions 오케스트레이터. |
| [Durable Entity Counter](examples/orchestration-and-workflows/durable_entity_counter/) | 카운터 상태를 관리하는 Durable Entity 예제. |
| [Durable Fan-Out Fan-In](examples/orchestration-and-workflows/durable_fan_out_fan_in/) | 병렬 액티비티를 사용한 Durable Functions 팬아웃/팬인 오케스트레이션. |
| [Durable Graph Fan Out](examples/orchestration-and-workflows/durable_graph_fan_out/) | 선언적 ManifestBuilder 그래프로 구동되는 azure-functions-durable-graph 기반 팬아웃/팬인 DAG 오케스트레이션. |
| [Durable Hello Sequence](examples/orchestration-and-workflows/durable_hello_sequence/) | 액티비티를 순차적으로 연결하는 Durable Functions 오케스트레이터. |
| [Durable Human Interaction](examples/orchestration-and-workflows/durable_human_interaction/) | 타임아웃과 함께 외부 승인 이벤트를 기다리는 Durable Functions 워크플로. |
| [Durable Retry Pattern](examples/orchestration-and-workflows/durable_retry_pattern/) | 불안정한 액티비티를 재시도하는 Durable Functions 오케스트레이션. |
| [Durable Singleton Monitor](examples/orchestration-and-workflows/durable_singleton_monitor/) | 외부 종속성을 지속적으로 폴링하고 변경 시 알림을 방출하는 Durable Functions 싱글톤 오케스트레이션. |
| [Durable Unit Testing](examples/orchestration-and-workflows/durable_unit_testing/) | 모의 기반 오케스트레이터 단위 테스트에 초점을 맞춘 Durable Functions 샘플. |
| [Saga Compensation](examples/orchestration-and-workflows/saga_compensation/) | 실패 시 이전에 완료된 단계를 보상하는 Durable Functions 사가 오케스트레이션. |
| [Sub-Orchestration](examples/orchestration-and-workflows/sub_orchestration/) | 두 개의 자식 하위 오케스트레이터에게 작업을 위임하는 Durable Functions 부모 오케스트레이션. |

### Reliability

| 레시피 | 설명 |
| --- | --- |
| [Circuit Breaker](examples/reliability/circuit_breaker/) | 이 레시피는 간단한 인메모리 서킷 브레이커로 다운스트림 API를 보호하는 HTTP 트리거 Azure Function을 보여줍니다. |
| [Outbox Pattern](examples/reliability/outbox_pattern/) | 다음과 같은 특징을 가진 Azure Functions Python용 트랜잭션 아웃박스 샘플: |
| [Poison Message Handling](examples/reliability/poison_message_handling/) | 반복 실패가 자동으로 포이즌 큐로 이동하도록 하고 실패한 페이로드를 로깅하여 운영자 후속 조치를 돕는 큐 트리거 Azure Functions 레시피. |
| [Rate Limiting / Throttle](examples/reliability/rate_limiting/) | 이 레시피는 인메모리 토큰 버킷을 사용하여 요청을 조절하고 로컬 버킷이 비면 `429 Too Many Requests`를 반환하는 HTTP 트리거 Azure Function을 보여줍니다. |
| [Retry and Idempotency](examples/reliability/retry_and_idempotency/) | 이 레시피는 관련된 두 가지 복원력 패턴을 보여줍니다: |

### Security and Tenancy

| 레시피 | 설명 |
| --- | --- |
| [Managed Identity Service Bus](examples/security-and-tenancy/managed_identity_servicebus/) | 이 레시피는 `connection="ServiceBusConnection"`을 사용하는 Service Bus 큐 트리거를 보여줍니다. |
| [Managed Identity Storage](examples/security-and-tenancy/managed_identity_storage/) | 이 레시피는 `connection="StorageConnection"`을 사용하는 Azure Storage Queue 트리거를 보여줍니다. 해당 설정은 연결 문자열 또는 관리 ID 설정으로 뒷받침할 수 있습니다. |
| [Secretless Key Vault](examples/security-and-tenancy/secretless_keyvault/) | Azure Key Vault 참조로 채워진 환경 변수에서 비밀을 읽는 HTTP 트리거 Azure Function. 이 함수는 표준 환경 접근과 `azure_functions_logging`만 사용합니다. |
| [Tenant Isolation](examples/security-and-tenancy/tenant_isolation/) | `X-Tenant-ID` 또는 Bearer 토큰 클레임에서 테넌트 컨텍스트를 확인한 뒤 `azure-functions-db-python`으로 테넌트별 데이터베이스를 쿼리하는 HTTP 레시피. |

### Runtime and Ops

| 레시피 | 설명 |
| --- | --- |
| [Blueprint Modular App](examples/runtime-and-ops/blueprint_modular_app/) | 이 레시피는 `func.Blueprint`를 사용한 모듈식 Azure Functions 앱을 보여줍니다. |
| [Cold Start Mitigation](examples/runtime-and-ops/cold_start_mitigation/) | 이 레시피는 Azure Functions Python의 실용적인 콜드 스타트 완화를 보여줍니다: |
| [Concurrency Tuning](examples/runtime-and-ops/concurrency_tuning/) | 이 레시피는 호스트 수준의 동적 동시성을 보여줍니다: |
| [Doctor Diagnostics Endpoint](examples/runtime-and-ops/doctor_diagnostics_endpoint/) | [`azure-functions-doctor`](https://github.com/yeongseon/azure-functions-doctor-python) 진단을 인증된 HTTP 엔드포인트로 노출하여 운영자가 컨테이너에 접속하지 않고 배포 후 배포 상태를 쿼리할 수 있게 합니다. |
| [Observability Tracing](examples/runtime-and-ops/observability_tracing/) | 상관관계 ID 전파, 구조화된 로깅, Application Insights 친화적 추적 컨텍스트를 보여주는 HTTP 트리거 추적 레시피. |
| [Output Binding vs SDK](examples/runtime-and-ops/output_binding_vs_sdk/) | 이 레시피는 동일한 큐 메시지를 보내는 두 가지 방법을 비교합니다: |
| [host.json Tuning](examples/runtime-and-ops/host_json_tuning/) | 이 레시피는 타이머 트리거와 풍부하게 구성된 `host.json`을 사용한 호스트 수준 튜닝에 초점을 맞춥니다. |

### Realtime

| 레시피 | 설명 |
| --- | --- |
| [WebSocket Proxy](examples/realtime/websocket_proxy/) | 클라이언트 토큰을 협상하고 게시 요청을 전달하는 Azure Web PubSub용 Azure Functions 프런트 도어. |

### AI and Agents

| 레시피 | 설명 |
| --- | --- |
| [AI Image Generation](examples/ai-and-agents/ai_image_generation/) | Azure OpenAI 이미지 생성에 프롬프트를 보내고 생성된 이미지 URL을 반환하는 HTTP 트리거 샘플. |
| [Azure OpenAI Direct Chat](examples/ai-and-agents/openai_direct_chat/) | `openai` Python SDK로 Azure OpenAI에 메시지 하나를 보내는 최소한의 HTTP 트리거 Azure Functions 샘플. |
| [Durable AI Pipeline](examples/ai-and-agents/durable_ai_pipeline/) | 임베딩, 벡터 검색, 답변 생성의 세 가지 AI 단계를 오케스트레이션하는 Durable Functions 샘플. |
| [Embedding Vector Search](examples/ai-and-agents/embedding_vector_search/) | Azure OpenAI 임베딩을 생성하고 이를 사용하여 Azure AI Search에 대해 벡터 쿼리를 실행하는 HTTP 트리거 샘플. |
| [Knowledge Notion Search](examples/ai-and-agents/knowledge_notion_search/) | azure-functions-knowledge KnowledgeBindings input/inject_client 데코레이터를 사용한 Notion 기반 지식 검색. |
| [LangGraph Agent](examples/ai-and-agents/langgraph_agent/) | `azure-functions-langgraph-python` 어댑터를 `azure-functions-logging-python`, `azure-functions-validation-python`, `azure-functions-openapi-python`과 함께 보여줍니다. |
| [LangGraph RAG Agent](examples/ai-and-agents/langgraph_rag_agent/) | 이 예제는 다음을 결합하는 방법을 보여줍니다: |
| [Langgraph Tool Use](examples/ai-and-agents/langgraph_tool_use/) | 추론 노드와 호출 가능한 도구 사이를 라우팅하는 azure-functions-langgraph 기반 도구 사용 LangGraph 에이전트. |
| [MCP Server Example](examples/ai-and-agents/mcp_server_example/) | 이 예제는 표준 HTTP 트리거와 JSON-RPC 2.0 메시지를 사용하여 Azure Functions에서 수동 Model Context Protocol(MCP) 서버를 호스팅합니다. |
| [RAG Knowledge API](examples/ai-and-agents/rag_knowledge_api/) | Azure AI Search와 Azure OpenAI를 사용하고 `azure-functions-validation-python`, `azure-functions-openapi-python`, `azure-functions-logging-python`을 결합한 최소 RAG API를 보여줍니다. |
| [Streaming AI Response](examples/ai-and-agents/streaming_ai_response/) | Azure OpenAI 스트리밍 채팅 완성을 Server-Sent Events로 변환하는 HTTP 트리거 샘플. |

### Guides

| 레시피 | 설명 |
| --- | --- |
| [Local Run and Direct Invoke](examples/guides/local_run_and_direct_invoke/) | 이 예제는 Azure Functions Python 앱을 위한 두 가지 로컬 테스트 워크플로를 보여줍니다: |

_80개 레시피. 레시피별 난이도 라벨은 [#117](https://github.com/yeongseon/azure-functions-cookbook-python/issues/117)에서 추적됩니다._

각 패턴 페이지는 `docs/patterns/` 아래에 있으며 `examples/`에 대응하는 실행 가능한 프로젝트가 함께 있습니다.

## Running Examples

모든 레시피는 Azure Functions Core Tools로 로컬에서 실행됩니다. 대부분의 트리거는
[Azurite](https://learn.microsoft.com/azure/storage/common/storage-use-azurite)로 에뮬레이션할 수 있으며,
일부는 실제 클라우드 서비스나 API 키가 필요합니다. 아래 표는 카테고리별 외부
종속성과 라이브 서비스 없이 실행하는 방법을 나열합니다.

<details>
<summary><strong>Local emulation cheat sheet</strong> — 카테고리별 외부 종속성 및 로컬 실행 방법</summary>

| 카테고리 | 외부 서비스 | 로컬 실행 방법 |
| --- | --- | --- |
| APIs and Ingress | 없음(순수 HTTP) | `func start` — 에뮬레이터 불필요 |
| Scheduled and Background | Storage(타이머/큐 상태) | Azurite (`AzureWebJobsStorage=UseDevelopmentStorage=true`) |
| Blob and File Triggers | Azure Storage / Event Grid | 블롭은 Azurite; Event Grid 트리거는 실제 구독 또는 재생된 페이로드 필요 |
| Async APIs and Jobs | Storage Queue | Azurite |
| Messaging and Pub/Sub | Service Bus / Event Grid / Storage Queue | Storage Queue는 Azurite; Service Bus 및 Event Grid는 실제 네임스페이스 필요 |
| Streams and Telemetry | Event Hubs | 실제 Event Hubs 네임스페이스(로컬 에뮬레이터 없음) |
| Data and Pipelines | Cosmos DB / SQL / Storage | DB 레시피는 Azurite 또는 SQLite; Cosmos 변경 피드는 실제 계정 필요 |
| Orchestration and Workflows | Durable Functions(Storage) | Azurite(Durable 태스크 허브) |
| Reliability | Storage Queue | Azurite |
| Security and Tenancy | Managed Identity / Key Vault / Service Bus | 로컬 개발은 연결 문자열 사용; ID 경로는 Azure 필요 |
| Runtime and Ops | 없음 / Storage | `func start`; 일부는 Azurite 사용 |
| Realtime | Web PubSub / SignalR | 실제 Web PubSub 서비스 |
| AI and Agents | Azure OpenAI / Azure AI Search | 기본적으로 로컬 스텁으로 실행; 실제 서비스는 엔드포인트/키 환경 변수 설정 |
| Guides | 없음 | `func start` |

</details>

각 예제의 `README.md`는 해당 예제의 구체적인 `local.settings.json` 값을 문서화합니다.
AI 예제는 자격 증명 없이 실행되도록 로컬 폴백 스텁을 제공합니다 — 실제 서비스를
켜는 환경 변수는 각 레시피의 README를 참조하세요.

### Test tiers

테스트는 pytest 마커로 분리되어 있어 기본적으로 빠른 계층을 실행하고
더 무거운 계층은 명시적으로 선택할 수 있습니다:

- **unit**(기본) — `make test`; 외부 서비스 없음, 에뮬레이터 없음.
- **smoke** — `hatch run smoke`; 에뮬레이션 불가능한 트리거에 대한 모듈 임포트 검사.
- **e2e** — `hatch run e2e`; Azurite와 실행 중인 `func` 호스트 필요.

## Repository Layout

```text
docs/              게시된 문서
  patterns/        큐레이팅된 패턴 문서
examples/          카테고리별로 구성된 실행 가능한 예제 프로젝트
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
| [azure-functions-openapi-python](https://github.com/yeongseon/azure-functions-openapi-python) | OpenAPI 스펙 생성 및 Swagger UI | Dogfooded ([예제 24개](https://github.com/search?q=repo%3Ayeongseon%2Fazure-functions-cookbook-python+azure_functions_openapi+path%3Aexamples&type=code)) |
| [azure-functions-validation-python](https://github.com/yeongseon/azure-functions-validation-python) | 요청/응답 검증 및 직렬화 | Dogfooded ([예제 23개](https://github.com/search?q=repo%3Ayeongseon%2Fazure-functions-cookbook-python+azure_functions_validation+path%3Aexamples&type=code)) |
| [azure-functions-logging-python](https://github.com/yeongseon/azure-functions-logging-python) | 구조화된 로깅 및 관측성 | Dogfooded ([예제 41개](https://github.com/search?q=repo%3Ayeongseon%2Fazure-functions-cookbook-python+azure_functions_logging+path%3Aexamples&type=code)) |
| [azure-functions-db-python](https://github.com/yeongseon/azure-functions-db-python) | SQLAlchemy 기반 DB 통합 헬퍼(폴링 기반 의사 트리거, 입력/출력/클라이언트 주입) | Dogfooded ([예제 9개](https://github.com/search?q=repo%3Ayeongseon%2Fazure-functions-cookbook-python+azure_functions_db+path%3Aexamples&type=code)) |
| [azure-functions-langgraph-python](https://github.com/yeongseon/azure-functions-langgraph-python) | Azure Functions용 LangGraph 배포 어댑터 | Dogfooded ([예제 3개](https://github.com/search?q=repo%3Ayeongseon%2Fazure-functions-cookbook-python+azure_functions_langgraph+path%3Aexamples&type=code)) |
| [azure-functions-scaffold-python](https://github.com/yeongseon/azure-functions-scaffold-python) | 프로젝트 스캐폴딩 CLI | Dogfooded ([예제 1개, CLI 생성](examples/apis-and-ingress/scaffold_walkthrough_app/)) |
| [azure-functions-doctor-python](https://github.com/yeongseon/azure-functions-doctor-python) | 배포 전 진단 CLI | Dogfooded ([예제 1개](https://github.com/search?q=repo%3Ayeongseon%2Fazure-functions-cookbook-python+azure_functions_doctor+path%3Aexamples&type=code)) |
| [azure-functions-durable-graph-python](https://github.com/yeongseon/azure-functions-durable-graph-python) | Durable Functions 기반 매니페스트 우선 그래프 런타임 *(실험적)* | Dogfooded ([예제 1개](examples/orchestration-and-workflows/durable_graph_fan_out/) — `durable_graph_fan_out`) |
| [azure-functions-knowledge-python](https://github.com/yeongseon/azure-functions-knowledge-python) | 지식 검색(RAG) 데코레이터 | Dogfooded ([예제 1개](examples/ai-and-agents/knowledge_notion_search/) — `knowledge_notion_search`가 실제 `KnowledgeBindings` API 사용) |
| **azure-functions-cookbook-python** *(이 저장소)* | 전체 툴킷을 위한 도그푸드 예제 | 예제 80개 |

## For AI Coding Assistants

이 저장소에는 루트 디렉터리에 `llms.txt`와 `llms-full.txt`가 포함되어 있습니다 — LLM 컨텍스트 윈도우에 최적화된 빠른 참조 및 전체 참조입니다. AI 지원 코딩 환경에서 이러한 레시피를 다룰 때 더 나은 컨텍스트를 위해 사용하세요.

## Disclaimer

이 프로젝트는 독립적인 커뮤니티 프로젝트이며 Microsoft와 제휴하거나
Microsoft가 보증하거나 유지 관리하지 않습니다.

Azure 및 Azure Functions는 Microsoft Corporation의 상표입니다.

## License

MIT
