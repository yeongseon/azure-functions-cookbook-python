# Azure Functions Python Cookbook

[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue)](https://github.com/yeongseon/azure-functions-cookbook-python)
[![CI](https://github.com/yeongseon/azure-functions-cookbook-python/actions/workflows/ci-smoke.yml/badge.svg)](https://github.com/yeongseon/azure-functions-cookbook-python/actions/workflows/ci-smoke.yml)
[![codecov](https://codecov.io/gh/yeongseon/azure-functions-cookbook-python/branch/main/graph/badge.svg)](https://codecov.io/gh/yeongseon/azure-functions-cookbook-python)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://pre-commit.com/)
[![Docs](https://github.com/yeongseon/azure-functions-cookbook-python/actions/workflows/docs.yml/badge.svg)](https://github.com/yeongseon/azure-functions-cookbook-python/actions/workflows/docs.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

他の言語で読む: [한국어](README.ko.md) | [日本語](README.ja.md) | [简体中文](README.zh-CN.md)

Python で実運用レベルの Azure Functions を構築するための実践的なレシピ集です。

## Why Use It

新しい Azure Functions プロジェクトを始めるには、散在するドキュメント、
ブログ記事、サンプルコードをつなぎ合わせる必要があることがよくあります。このクックブックは、次の問いに答える、キュレーションされた実行可能なレシピを提供します:

- このシナリオでは何を作るべきか?
- アーキテクチャはどう構成すべきか?
- 動作するベースラインからどう始めるか?

## Scope

- Azure Functions Python **v2 プログラミングモデル**
- デコレーターベースの `func.FunctionApp()` アプリケーション
- 実行可能な例を備えた実践的なレシピ
- アーキテクチャの説明と本番向けの注意点

このリポジトリはコンテンツ中心です。CLI ツールではありません。

## Quick Index

カテゴリへ移動: [APIs and Ingress](#apis-and-ingress) · [Scheduled and Background](#scheduled-and-background) · [Blob and File Triggers](#blob-and-file-triggers) · [Async APIs and Jobs](#async-apis-and-jobs) · [Messaging and Pub/Sub](#messaging-and-pubsub) · [Streams and Telemetry](#streams-and-telemetry) · [Data and Pipelines](#data-and-pipelines) · [Orchestration and Workflows](#orchestration-and-workflows) · [Reliability](#reliability) · [Security and Tenancy](#security-and-tenancy) · [Runtime and Ops](#runtime-and-ops) · [Realtime](#realtime) · [AI and Agents](#ai-and-agents) · [Guides](#guides)
プログラムで検索したいですか？すべてのレシピの機械可読インデックス
(slug, title, category, example_path, tags) が [`recipes.json`](recipes.json) にあり、
`python scripts/gen_recipe_index.py` で再生成できます。`find_recipe` ヘルパーで
キーワードやタグからレシピを検索できます:

```python
from azure_functions_python_cookbook.recipes import find_recipe

# slug・title・category・description・tags を横断する自由テキスト検索
for recipe in find_recipe("durable retry"):
    print(recipe.title, "->", recipe.example_path)

# 正確なタグでフィルタリング
durable = find_recipe(tag="durable")
```

---

## Recipes

### APIs and Ingress

| レシピ | 説明 |
| --- | --- |
| [APIM Function Backend](examples/apis-and-ingress/apim_function_backend/) | 認証、レート制限、キャッシュのために Azure API Management ポリシーの背後に配置するよう設計された HTTP トリガー Azure Functions バックエンド。 |
| [BFF Facade API](examples/apis-and-ingress/bff_facade_api/) | 複数のバックエンドサービス呼び出しを 1 つのクライアント向けレスポンスに集約する HTTP Backend-for-Frontend ファサード。 |
| [EasyAuth Claims Extraction](examples/apis-and-ingress/auth_easyauth/) | Azure Functions 向けのロールベースアクセス制御を備えた EasyAuth プリンシパル抽出。 |
| [Full Stack CRUD API](examples/apis-and-ingress/full_stack_crud_api/) | 単一の `items` リソースを中心に Azure Functions Python DX Toolkit を連携させるショーケース HTTP API。 |
| [HTTP Auth Levels](examples/apis-and-ingress/http_auth_levels/) | 匿名、関数キー、管理者キーのエンドポイントを示す HTTP トリガーの例。 |
| [HTTP Routing Query Body](examples/apis-and-ingress/http_routing_query_body/) | ルートパラメーター、クエリ文字列、JSON ボディ解析、ステータスコードを示す HTTP CRUD および検索の例。 |
| [Hello HTTP Minimal](examples/apis-and-ingress/hello_http_minimal/) | 挨拶を返す最小限の HTTP トリガー Azure Function。 |
| [JWT Bearer Validation](examples/apis-and-ingress/auth_jwt_validation/) | Azure Functions 向けのクレームベースアクセス制御を備えた JWT Bearer トークン検証。 |
| [Multi-Tenant Auth](examples/apis-and-ingress/auth_multitenant/) | Azure Functions 向けのテナント許可リストを使用したマルチテナントアクセス制御。 |
| [Scaffold Walkthrough — from afs new to a running HTTP API](examples/apis-and-ingress/scaffold_walkthrough_app/) | このレシピは、デフォルトの `strict` プリセットを使用した **`azure-functions-scaffold` のコミット済み出力**です。スキャフォールド CLI が新しい Azure Functions Python v2 HTTP プロジェクトに対して正確に何を生成するかを確認し、推奨のローカル開発ループを学ぶために使用してください。 |
| [Webhook GitHub](examples/apis-and-ingress/webhook_github/) | HMAC-SHA256 署名検証を備えた GitHub Webhook レシーバーの例。 |

### Scheduled and Background

| レシピ | 説明 |
| --- | --- |
| [Durable Timer Reminder](examples/scheduled-and-background/durable_timer_reminder/) | 長い遅延を待った後にリマインダーのコールバックアクティビティを実行する Durable Functions オーケストレーション。 |
| [Queue Scheduled Dispatch](examples/scheduled-and-background/queue_scheduled_dispatch/) | 期限が来た作業を下流ワーカー向けに Azure Storage Queue へ放出するタイマー駆動のスケジュール済みディスパッチパターン。 |
| [Timer Cron Job](examples/scheduled-and-background/timer_cron_job/) | 5 分ごとにスケジュールされたメンテナンスジョブを実行するタイマートリガー Azure Function。 |

### Blob and File Triggers

| レシピ | 説明 |
| --- | --- |
| [Blob CSV to Table](examples/blob-and-file-triggers/blob_csv_to_table/) | アップロードされた CSV Blob を読み取り、正規化された行を Azure Table Storage に書き込む Event Grid 駆動の取り込みパターン。 |
| [Blob Event Grid Trigger](examples/blob-and-file-triggers/blob_eventgrid_trigger/) | Event Grid ソース通知向けに構成された Blob トリガー Azure Function。 |
| [Blob Thumbnail Generator](examples/blob-and-file-triggers/blob_thumbnail_generator/) | サムネイルを生成して別の出力コンテナーに書き込む Event Grid 駆動の Blob プロセッサー。 |
| [Blob Upload Processor](examples/blob-and-file-triggers/blob_upload_processor/) | `uploads/{name}` からアップロードされたファイルを処理する Blob トリガー Azure Function。 |

### Async APIs and Jobs

| レシピ | 説明 |
| --- | --- |
| [Async HTTP 202 Polling](examples/async-apis-and-jobs/async_http_polling/) | `202 Accepted` とクライアントポーリング用の `statusQueryGetUri` を返す HTTP トリガー Durable Functions の例。 |
| [Callback Completion](examples/async-apis-and-jobs/callback_completion/) | `/api/tasks` で作業を受け付け、バックグラウンド処理が完了すると HTTP コールバックを送信する HTTP + Queue の例。 |
| [Queue-Backed Job](examples/async-apis-and-jobs/queue_backed_job/) | ジョブを受け付けて `202 Accepted` を返し、保存された状態レコードをポーリングする HTTP + Storage Queue レシピ。 |

### Messaging and Pub/Sub

| レシピ | 説明 |
| --- | --- |
| [Claim Check Pattern](examples/messaging-and-pubsub/claim_check_pattern/) | ペイロードを Blob Storage に保存し、キューには参照のみを渡す大容量メッセージパターン。 |
| [Event Grid Domain Events](examples/messaging-and-pubsub/eventgrid_domain_events/) | カスタム注文ドメインイベントを Event Grid カスタムトピックに発行する HTTP トリガー Azure Function と、その結果のイベントをログ記録する Event Grid トリガーのサブスクライバー。 |
| [Event Grid Event Router](examples/messaging-and-pubsub/eventgrid_router/) | イベントの種類とサブジェクトのフィルターを使用してイベントを異なるハンドラーにルーティングする Event Grid トリガー Azure Function。 |
| [Queue Consumer](examples/messaging-and-pubsub/queue_consumer/) | タスクメッセージを解析して処理するキュートリガー Azure Function。 |
| [Queue Producer](examples/messaging-and-pubsub/queue_producer/) | JSON を検証し、タスクを Storage Queue にキューイングする HTTP トリガー Azure Function。 |
| [Service Bus DLQ Replay](examples/messaging-and-pubsub/servicebus_dlq_replay/) | 検査と修正の後、デッドレター化された Service Bus キューメッセージをメインキューへ再送。 |
| [Service Bus Sessions](examples/messaging-and-pubsub/servicebus_sessions/) | Azure Service Bus セッションを使用した順序付きメッセージ処理を示す Azure Functions の例。 |
| [Service Bus Topic Fan-out](examples/messaging-and-pubsub/servicebus_topic_fanout/) | 3 つの独立したサブスクリプションハンドラーによる Service Bus トピックのファンアウトを示す Azure Functions の例。 |
| [Service Bus Worker](examples/messaging-and-pubsub/servicebus_worker/) | 信頼性の高いバックグラウンド作業の消費のための Service Bus キュートリガー Azure Function。 |

### Streams and Telemetry

| レシピ | 説明 |
| --- | --- |
| [Event Hub Batch Window](examples/streams-and-telemetry/eventhub_batch_window/) | バッチウィンドウを処理し、集計テレメトリの合計をログ記録する Event Hub トリガー Azure Function。 |
| [Event Hub Checkpoint Replay](examples/streams-and-telemetry/eventhub_checkpoint_replay/) | オフセット追跡と冪等処理によるリプレイ対応の Event Hub 消費を示す Azure Functions の例。 |
| [Event Hub Consumer](examples/streams-and-telemetry/eventhub_consumer/) | ほぼリアルタイムのテレメトリストリーム処理のための Event Hub トリガー Azure Function。 |

### Data and Pipelines

| レシピ | 説明 |
| --- | --- |
| [CQRS Read Projection](examples/data-and-pipelines/cqrs_read_projection/) | 次のような Azure Functions Python 向け CQRS サンプル: |
| [Change Feed Processor](examples/data-and-pipelines/change_feed_processor/) | 下流同期のための Cosmos DB 変更フィードトリガー Azure Function。 |
| [DB Input and Output Bindings](examples/data-and-pipelines/db_input_output/) | SQLAlchemy を基盤としたストレージと組み合わせた `azure-functions-db-python` の入出力バインディングを、`azure-functions-validation-python` および `azure-functions-openapi-python` とともに示します。 |
| [ETL Enrichment](examples/data-and-pipelines/etl_enrichment/) | 生の JSON 顧客レコードを読み取り、ルックアップデータで拡充し、拡充された行をデータベースに書き込む Blob トリガー ETL の例。 |
| [File Processing Pipeline](examples/data-and-pipelines/file_processing_pipeline/) | アップロードされた CSV または JSON ファイルを検証し、レコードを変換して、処理結果をデータベースに永続化する Blob トリガー Azure Function。 |
| [SQLAlchemy REST Pagination](examples/data-and-pipelines/sqlalchemy_rest_pagination/) | 次を組み合わせた HTTP API の例: |

### Orchestration and Workflows

| レシピ | 説明 |
| --- | --- |
| [Async Job Lifecycle](examples/orchestration-and-workflows/async_job_lifecycle/) | 作成、状態、キャンセル、パージを含む完全な非同期ジョブライフサイクル管理のための Durable Functions レシピ。 |
| [Durable Determinism Gotchas](examples/orchestration-and-workflows/durable_determinism_gotchas/) | 決定論的なコーディングパターンを示す Durable Functions オーケストレーター。 |
| [Durable Entity Counter](examples/orchestration-and-workflows/durable_entity_counter/) | カウンター状態を管理する Durable Entity の例。 |
| [Durable Fan-Out Fan-In](examples/orchestration-and-workflows/durable_fan_out_fan_in/) | 並列アクティビティを使用した Durable Functions のファンアウト/ファンインオーケストレーション。 |
| [Durable Graph Fan Out](examples/orchestration-and-workflows/durable_graph_fan_out/) | 宣言的な ManifestBuilder グラフで駆動される azure-functions-durable-graph によるファンアウト/ファンイン DAG オーケストレーション。 |
| [Durable Hello Sequence](examples/orchestration-and-workflows/durable_hello_sequence/) | アクティビティを順番に連結する Durable Functions オーケストレーター。 |
| [Durable Human Interaction](examples/orchestration-and-workflows/durable_human_interaction/) | タイムアウト付きで外部承認イベントを待つ Durable Functions ワークフロー。 |
| [Durable Retry Pattern](examples/orchestration-and-workflows/durable_retry_pattern/) | 不安定なアクティビティを再試行する Durable Functions オーケストレーション。 |
| [Durable Singleton Monitor](examples/orchestration-and-workflows/durable_singleton_monitor/) | 外部依存を継続的にポーリングし、変更時にアラートを発する Durable Functions シングルトンオーケストレーション。 |
| [Durable Unit Testing](examples/orchestration-and-workflows/durable_unit_testing/) | モックベースのオーケストレーター単体テストに焦点を当てた Durable Functions サンプル。 |
| [Saga Compensation](examples/orchestration-and-workflows/saga_compensation/) | 失敗時に以前完了したステップを補償する Durable Functions のサガオーケストレーション。 |
| [Sub-Orchestration](examples/orchestration-and-workflows/sub_orchestration/) | 2 つの子サブオーケストレーターに作業を委任する Durable Functions の親オーケストレーション。 |

### Reliability

| レシピ | 説明 |
| --- | --- |
| [Circuit Breaker](examples/reliability/circuit_breaker/) | このレシピは、シンプルなインメモリのサーキットブレーカーで下流 API を保護する HTTP トリガー Azure Function を示します。 |
| [Outbox Pattern](examples/reliability/outbox_pattern/) | 次のような Azure Functions Python 向けのトランザクショナルアウトボックスサンプル: |
| [Poison Message Handling](examples/reliability/poison_message_handling/) | 繰り返される失敗が自動的にポイズンキューへ移動するようにし、失敗したペイロードをログ記録して運用者のフォローアップを支援するキュートリガー Azure Functions レシピ。 |
| [Rate Limiting / Throttle](examples/reliability/rate_limiting/) | このレシピは、インメモリのトークンバケットを使用してリクエストをスロットリングし、ローカルバケットが空のときに `429 Too Many Requests` を返す HTTP トリガー Azure Function を示します。 |
| [Retry and Idempotency](examples/reliability/retry_and_idempotency/) | このレシピは、関連する 2 つの回復性パターンを示します: |

### Security and Tenancy

| レシピ | 説明 |
| --- | --- |
| [Managed Identity Service Bus](examples/security-and-tenancy/managed_identity_servicebus/) | このレシピは、`connection="ServiceBusConnection"` を使用する Service Bus キュートリガーを示します。 |
| [Managed Identity Storage](examples/security-and-tenancy/managed_identity_storage/) | このレシピは、`connection="StorageConnection"` を使用する Azure Storage Queue トリガーを示します。その設定は接続文字列またはマネージド ID 設定のいずれかで裏付けることができます。 |
| [Secretless Key Vault](examples/security-and-tenancy/secretless_keyvault/) | Azure Key Vault 参照によって設定された環境変数からシークレットを読み取る HTTP トリガー Azure Function。この関数は標準的な環境アクセスと `azure_functions_logging` のみを使用します。 |
| [Tenant Isolation](examples/security-and-tenancy/tenant_isolation/) | `X-Tenant-ID` または Bearer トークンのクレームからテナントコンテキストを解決し、`azure-functions-db-python` でテナント固有のデータベースをクエリする HTTP レシピ。 |

### Runtime and Ops

| レシピ | 説明 |
| --- | --- |
| [Blueprint Modular App](examples/runtime-and-ops/blueprint_modular_app/) | このレシピは、`func.Blueprint` を使用したモジュラー Azure Functions アプリを示します。 |
| [Cold Start Mitigation](examples/runtime-and-ops/cold_start_mitigation/) | このレシピは、Azure Functions Python の実践的なコールドスタート緩和を示します: |
| [Concurrency Tuning](examples/runtime-and-ops/concurrency_tuning/) | このレシピは、ホストレベルの動的同時実行を示します: |
| [Doctor Diagnostics Endpoint](examples/runtime-and-ops/doctor_diagnostics_endpoint/) | [`azure-functions-doctor`](https://github.com/yeongseon/azure-functions-doctor-python) の診断を認証済み HTTP エンドポイントとして公開し、運用者がコンテナーにシェルインすることなくデプロイ後のデプロイ状態をクエリできるようにします。 |
| [Observability Tracing](examples/runtime-and-ops/observability_tracing/) | 相関 ID の伝播、構造化ログ、Application Insights に適したトレースコンテキストを示す HTTP トリガーのトレースレシピ。 |
| [Output Binding vs SDK](examples/runtime-and-ops/output_binding_vs_sdk/) | このレシピは、同じキューメッセージを送信する 2 つの方法を比較します: |
| [host.json Tuning](examples/runtime-and-ops/host_json_tuning/) | このレシピは、タイマートリガーと豊富に構成された `host.json` を使用したホストレベルのチューニングに焦点を当てます。 |

### Realtime

| レシピ | 説明 |
| --- | --- |
| [WebSocket Proxy](examples/realtime/websocket_proxy/) | クライアントトークンをネゴシエートし、発行リクエストを転送する Azure Web PubSub 向けの Azure Functions フロントドア。 |

### AI and Agents

| レシピ | 説明 |
| --- | --- |
| [AI Image Generation](examples/ai-and-agents/ai_image_generation/) | Azure OpenAI の画像生成にプロンプトを送信し、生成された画像 URL を返す HTTP トリガーサンプル。 |
| [Azure OpenAI Direct Chat](examples/ai-and-agents/openai_direct_chat/) | `openai` Python SDK で Azure OpenAI に 1 つのメッセージを送信する最小限の HTTP トリガー Azure Functions サンプル。 |
| [Durable AI Pipeline](examples/ai-and-agents/durable_ai_pipeline/) | 埋め込み、ベクトル検索、回答生成の 3 つの AI ステップをオーケストレーションする Durable Functions サンプル。 |
| [Embedding Vector Search](examples/ai-and-agents/embedding_vector_search/) | Azure OpenAI の埋め込みを作成し、それを使用して Azure AI Search に対してベクトルクエリを実行する HTTP トリガーサンプル。 |
| [Knowledge Notion Search](examples/ai-and-agents/knowledge_notion_search/) | azure-functions-knowledge の KnowledgeBindings input/inject_client デコレーターを使用した Notion 基盤のナレッジ検索。 |
| [LangGraph Agent](examples/ai-and-agents/langgraph_agent/) | `azure-functions-langgraph-python` アダプターを `azure-functions-logging-python`、`azure-functions-validation-python`、`azure-functions-openapi-python` とともに示します。 |
| [LangGraph RAG Agent](examples/ai-and-agents/langgraph_rag_agent/) | この例は、次を組み合わせる方法を示します: |
| [Langgraph Tool Use](examples/ai-and-agents/langgraph_tool_use/) | 推論ノードと呼び出し可能なツールの間をルーティングする azure-functions-langgraph によるツール使用 LangGraph エージェント。 |
| [MCP Server Example](examples/ai-and-agents/mcp_server_example/) | この例は、標準的な HTTP トリガーと JSON-RPC 2.0 メッセージを使用して、Azure Functions 上で手動の Model Context Protocol (MCP) サーバーをホストします。 |
| [RAG Knowledge API](examples/ai-and-agents/rag_knowledge_api/) | Azure AI Search と Azure OpenAI を使用し、`azure-functions-validation-python`、`azure-functions-openapi-python`、`azure-functions-logging-python` を組み合わせた最小限の RAG API を示します。 |
| [Streaming AI Response](examples/ai-and-agents/streaming_ai_response/) | Azure OpenAI のストリーミングチャット補完を Server-Sent Events に変換する HTTP トリガーサンプル。 |

### Guides

| レシピ | 説明 |
| --- | --- |
| [Local Run and Direct Invoke](examples/guides/local_run_and_direct_invoke/) | この例は、Azure Functions Python アプリ向けの 2 つのローカルテストワークフローを示します: |

_80 レシピ。レシピごとの難易度ラベルは [#117](https://github.com/yeongseon/azure-functions-cookbook-python/issues/117) で追跡されています。_

各パターンページは `docs/patterns/` の下にあり、`examples/` に対応する実行可能なプロジェクトがあります。

## Running Examples

すべてのレシピは Azure Functions Core Tools でローカルに実行できます。ほとんどのトリガーは
[Azurite](https://learn.microsoft.com/azure/storage/common/storage-use-azurite) でエミュレートでき、
一部は実際のクラウドサービスや API キーが必要です。以下の表は、カテゴリごとの外部
依存とライブサービスなしで実行する方法を示します。

<details>
<summary><strong>Local emulation cheat sheet</strong> — カテゴリごとの外部依存とローカル実行方法</summary>

| カテゴリ | 外部サービス | ローカル実行方法 |
| --- | --- | --- |
| APIs and Ingress | なし(プレーン HTTP) | `func start` — エミュレーター不要 |
| Scheduled and Background | Storage(タイマー/キュー状態) | Azurite (`AzureWebJobsStorage=UseDevelopmentStorage=true`) |
| Blob and File Triggers | Azure Storage / Event Grid | Blob は Azurite; Event Grid トリガーは実際のサブスクリプションまたは再生されたペイロードが必要 |
| Async APIs and Jobs | Storage Queue | Azurite |
| Messaging and Pub/Sub | Service Bus / Event Grid / Storage Queue | Storage Queue は Azurite; Service Bus と Event Grid は実際の名前空間が必要 |
| Streams and Telemetry | Event Hubs | 実際の Event Hubs 名前空間(ローカルエミュレーターなし) |
| Data and Pipelines | Cosmos DB / SQL / Storage | DB レシピは Azurite または SQLite; Cosmos の変更フィードは実際のアカウントが必要 |
| Orchestration and Workflows | Durable Functions(Storage) | Azurite(Durable タスクハブ) |
| Reliability | Storage Queue | Azurite |
| Security and Tenancy | Managed Identity / Key Vault / Service Bus | ローカル開発は接続文字列を使用; ID パスは Azure が必要 |
| Runtime and Ops | なし / Storage | `func start`; 一部は Azurite を使用 |
| Realtime | Web PubSub / SignalR | 実際の Web PubSub サービス |
| AI and Agents | Azure OpenAI / Azure AI Search | 既定ではローカルスタブに対して実行; 実サービスにはエンドポイント/キーの環境変数を設定 |
| Guides | なし | `func start` |

</details>

各例の `README.md` は、その例に固有の `local.settings.json` の値を文書化しています。
AI の例は、資格情報なしで実行できるローカルフォールバックスタブを同梱しています — 実際の
サービスを有効にする環境変数については、各レシピの README を参照してください。

### Test tiers

テストは pytest マーカーで分離されているため、既定で高速なティアを実行し、
より重いティアは明示的に選択できます:

- **unit**(既定) — `make test`; 外部サービスなし、エミュレーターなし。
- **smoke** — `hatch run smoke`; エミュレート不可能なトリガーのモジュールインポートチェック。
- **e2e** — `hatch run e2e`; Azurite と実行中の `func` ホストが必要。

## Repository Layout

```text
docs/              公開ドキュメント
  patterns/        キュレーションされたパターンドキュメント
examples/          カテゴリ別に整理された実行可能な例のプロジェクト
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

- 製品要件: `PRD.md`
- 設計原則: `DESIGN.md`
- コントリビューションガイド: `CONTRIBUTING.md`

## Ecosystem

このクックブックは **Azure Functions Python DX Toolkit** の **ドッグフード**です — すべての例は、本番に近いシナリオでツールキットライブラリを使用する実際に実行可能な Azure Function です。ライブラリがクックブックで動作すれば、実環境でも動作します。

**Status** 列は、各パッケージがこのリポジトリで現在どのように活用されているかを示します: **Dogfooded**(実際の例でインポートされ実行される)、**Experimental**(紹介されているがまだどの例でも活用されていない)、**Planned**(統合が追跡されているがまだ開始されていない)。件数は、そのパッケージをインポートする例プロジェクトの数であり、CLI ツール(例: スキャフォールドジェネレーター)の場合は直接インポートではなく、CLI によって生成または駆動される例の数を反映します。

| パッケージ | 役割 | Status |
|---------|------|--------|
| [azure-functions-openapi-python](https://github.com/yeongseon/azure-functions-openapi-python) | OpenAPI スペック生成と Swagger UI | Dogfooded ([24 例](https://github.com/search?q=repo%3Ayeongseon%2Fazure-functions-cookbook-python+azure_functions_openapi+path%3Aexamples&type=code)) |
| [azure-functions-validation-python](https://github.com/yeongseon/azure-functions-validation-python) | リクエスト/レスポンスの検証とシリアライズ | Dogfooded ([21 例](https://github.com/search?q=repo%3Ayeongseon%2Fazure-functions-cookbook-python+azure_functions_validation+path%3Aexamples&type=code)) |
| [azure-functions-logging-python](https://github.com/yeongseon/azure-functions-logging-python) | 構造化ロギングと可観測性 | Dogfooded ([41 例](https://github.com/search?q=repo%3Ayeongseon%2Fazure-functions-cookbook-python+azure_functions_logging+path%3Aexamples&type=code)) |
| [azure-functions-db-python](https://github.com/yeongseon/azure-functions-db-python) | SQLAlchemy を活用した DB 統合ヘルパー(ポーリングベースの疑似トリガー、入力/出力/クライアント注入) | Dogfooded ([9 例](https://github.com/search?q=repo%3Ayeongseon%2Fazure-functions-cookbook-python+azure_functions_db+path%3Aexamples&type=code)) |
| [azure-functions-langgraph-python](https://github.com/yeongseon/azure-functions-langgraph-python) | Azure Functions 向け LangGraph デプロイアダプター | Dogfooded ([3 例](https://github.com/search?q=repo%3Ayeongseon%2Fazure-functions-cookbook-python+azure_functions_langgraph+path%3Aexamples&type=code)) |
| [azure-functions-scaffold-python](https://github.com/yeongseon/azure-functions-scaffold-python) | プロジェクトスキャフォールディング CLI | Dogfooded ([1 例、CLI 生成](examples/apis-and-ingress/scaffold_walkthrough_app/)) |
| [azure-functions-doctor-python](https://github.com/yeongseon/azure-functions-doctor-python) | デプロイ前診断 CLI | Dogfooded ([1 例](https://github.com/search?q=repo%3Ayeongseon%2Fazure-functions-cookbook-python+azure_functions_doctor+path%3Aexamples&type=code)) |
| [azure-functions-durable-graph-python](https://github.com/yeongseon/azure-functions-durable-graph-python) | Durable Functions によるマニフェストファーストのグラフランタイム *(実験的)* | Dogfooded ([1 例](examples/orchestration-and-workflows/durable_graph_fan_out/) — `durable_graph_fan_out`) |
| [azure-functions-knowledge-python](https://github.com/yeongseon/azure-functions-knowledge-python) | ナレッジ検索(RAG)デコレーター | Dogfooded ([1 例](examples/ai-and-agents/knowledge_notion_search/) — `knowledge_notion_search` が実際の `KnowledgeBindings` API を使用) |
| **azure-functions-cookbook-python** *(このリポジトリ)* | 全ツールキットのドッグフード例 | 80 例 |

## For AI Coding Assistants

このリポジトリには、ルートディレクトリに `llms.txt` と `llms-full.txt` が含まれています — LLM のコンテキストウィンドウ向けに最適化されたクイックリファレンスと完全リファレンスです。AI 支援コーディング環境でこれらのレシピを扱う際に、より良いコンテキストのために使用してください。

## Disclaimer

このプロジェクトは独立したコミュニティプロジェクトであり、Microsoft と提携、
承認、または Microsoft によって維持されているものではありません。

Azure および Azure Functions は Microsoft Corporation の商標です。

## License

MIT
