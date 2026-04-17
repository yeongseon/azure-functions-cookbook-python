# Reliability

Use this category for patterns that harden function apps against duplicate delivery, transient failure, and partial completion. These recipes focus on operational correctness more than transport choice.

| Recipe | Trigger | Difficulty |
| --- | --- | --- |
| [Retry and Idempotency](./retry-and-idempotency.md) | Cross-trigger reliability pattern | Intermediate |
| [Circuit Breaker](./circuit-breaker.md) | HTTP + state management | Advanced |
| [Poison Message Handling](./poison-message-handling.md) | Queue / Service Bus DLQ | Intermediate |
| [Outbox Pattern](./outbox-pattern.md) | DB + Queue transactional | Advanced |
| [Rate Limiting Throttle](./rate-limiting-throttle.md) | HTTP + Redis/state | Intermediate |
