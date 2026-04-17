from app.services import idempotency_service


def test_dedup_logic() -> None:
    idempotency_service._seen_ids.clear()

    assert idempotency_service.is_duplicate("order-1") is False
    idempotency_service.mark_processed("order-1")
    assert idempotency_service.is_duplicate("order-1") is True
