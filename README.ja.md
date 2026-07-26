# Azure Functions Python Cookbook

[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue)](https://github.com/yeongseon/azure-functions-cookbook-python)
[![CI](https://github.com/yeongseon/azure-functions-cookbook-python/actions/workflows/ci-smoke.yml/badge.svg)](https://github.com/yeongseon/azure-functions-cookbook-python/actions/workflows/ci-smoke.yml)
[![Docs](https://github.com/yeongseon/azure-functions-cookbook-python/actions/workflows/docs.yml/badge.svg)](https://github.com/yeongseon/azure-functions-cookbook-python/actions/workflows/docs.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

他の言語: [English](README.md) | [한국어](README.ko.md) | [简体中文](README.zh-CN.md)

Pythonを使用して実用的なAzure Functionsを構築するためのレシピ集です。

## Why Use It

新しいAzure Functionsプロジェクトを開始する際、散在するドキュメント、ブログ記事、サンプルコードを繋ぎ合わせるのは時間がかかります。このクックブックでは、以下のような疑問に応える、厳選された実行可能なレシピを提供します。

- このシナリオでは何を構築すべきか？
- アーキテクチャはどのような構成にすべきか？
- どのようにして動作するベースラインから開始できるか？

## Scope

- Azure Functions Python **v2 プログラミングモデル**
- デコレータベースの `func.FunctionApp()` アプリケーション
- 実行可能な例を含む実用的なレシピ
- アーキテクチャの解説と本番環境での注意点

本リポジトリはコンテンツを重視しており、CLIツールではありません。

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

各パターンページは `docs/patterns/` 配下にあり、対応する実行可能プロジェクトが `examples/` にあります。

## Repository Layout

```text
docs/              公開ドキュメント
  patterns/        厳選されたパターンドキュメント（67レシピ）
examples/          カテゴリ別実行可能プロジェクト
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

このクックブックは **Azure Functions Python DX Toolkit** の **ドッグフード** です — すべての例は、本番に近いシナリオでツールキットのライブラリを使用する実際に実行可能な Azure Function です。クックブックで動作するライブラリは、実運用でも動作します。

**Status** 列は、各パッケージがこのリポジトリで現在どのように活用されているかを示します：**Dogfooded**（実際の例でインポートされ実行される）、**Experimental**（紹介されているがまだどの例でも活用されていない）、**Planned**（統合が追跡されているがまだ開始されていない）。件数は、そのパッケージをインポートする例プロジェクトの数であり、CLI ツール（例：スキャフォールドジェネレーター）の場合は、直接インポートではなく CLI によって生成または駆動される例の数を反映します。

| パッケージ | 役割 | Status |
|---------|------|--------|
| [azure-functions-openapi-python](https://github.com/yeongseon/azure-functions-openapi-python) | OpenAPI スペック生成と Swagger UI | Dogfooded（例 24 件） |
| [azure-functions-validation-python](https://github.com/yeongseon/azure-functions-validation-python) | リクエスト/レスポンスのバリデーションとシリアライズ | Dogfooded（例 23 件） |
| [azure-functions-logging-python](https://github.com/yeongseon/azure-functions-logging-python) | 構造化ロギングと可観測性 | Dogfooded（例 41 件） |
| [azure-functions-db-python](https://github.com/yeongseon/azure-functions-db-python) | SQLAlchemy ベースの DB 統合ヘルパー（ポーリングベースの擬似トリガー、入力/出力/クライアント注入） | Dogfooded（例 9 件） |
| [azure-functions-langgraph-python](https://github.com/yeongseon/azure-functions-langgraph-python) | Azure Functions 向け LangGraph デプロイアダプター | Dogfooded（例 2 件） |
| [azure-functions-scaffold-python](https://github.com/yeongseon/azure-functions-scaffold-python) | プロジェクトスキャフォールディング CLI | Dogfooded（例 1 件、CLI 生成） |
| [azure-functions-doctor-python](https://github.com/yeongseon/azure-functions-doctor-python) | デプロイ前診断 CLI | Dogfooded（例 1 件） |
| [azure-functions-durable-graph-python](https://github.com/yeongseon/azure-functions-durable-graph-python) | Durable Functions によるマニフェストファーストのグラフランタイム *(実験的)* | Experimental — まだドッグフードされていません ([#76](https://github.com/yeongseon/azure-functions-cookbook-python/issues/76)) |
| [azure-functions-knowledge-python](https://github.com/yeongseon/azure-functions-knowledge-python) | 知識検索（RAG）デコレーター | Experimental — `rag_knowledge_api` は実際のライブラリではなくローカルスタブを使用します ([#76](https://github.com/yeongseon/azure-functions-cookbook-python/issues/76)) |
| **azure-functions-cookbook-python** *(このリポジトリ)* | ツールキット全体のためのドッグフード例 | 例 77 件 |

## Disclaimer

本プロジェクトは独立したコミュニティプロジェクトであり、Microsoftと提携、承認、または保守されているものではありません。

AzureおよびAzure Functionsは、Microsoft Corporationの商標です。

## License

MIT
