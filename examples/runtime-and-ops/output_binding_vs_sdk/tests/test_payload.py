from app.services.payload_service import build_payload


class _RequestStub:
    def __init__(
        self, payload: dict[str, str] | None = None, raise_value_error: bool = False
    ) -> None:
        self.payload = payload or {}
        self.raise_value_error = raise_value_error

    def get_json(self) -> dict[str, str]:
        if self.raise_value_error:
            raise ValueError
        return self.payload


def test_build_payload_uses_task() -> None:
    payload = build_payload(_RequestStub(payload={"task": "process-report"}))
    assert payload == {"task": "process-report", "source": "recipe"}


def test_build_payload_uses_default_when_json_invalid() -> None:
    payload = build_payload(_RequestStub(raise_value_error=True))
    assert payload == {"task": "demo-task", "source": "recipe"}
