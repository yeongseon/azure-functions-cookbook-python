"""Result handler: record the outcome idempotently and log only safe correlation fields."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Protocol

from app.agent import final_answer
from app.contract import MessageLike, parse_request

logger = logging.getLogger("servicebus_langgraph_agent")


@dataclass(frozen=True, slots=True)
class Outcome:
    request_id: str
    answer: str


class OutcomeStore(Protocol):
    def put(self, outcome: Outcome) -> None:
        """Upsert by ``request_id``. Must be idempotent: the same request can arrive again."""
        ...


class InMemoryOutcomeStore:
    """Process-local stand-in for a durable, idempotent sink.

    Replace it with an upsert keyed by ``request_id`` (for example a Table Storage or Cosmos DB
    item). An append-only sink would record duplicates when Service Bus redelivers.
    """

    def __init__(self) -> None:
        self._outcomes: dict[str, Outcome] = {}

    def put(self, outcome: Outcome) -> None:
        self._outcomes[outcome.request_id] = outcome

    def get(self, request_id: str) -> Outcome | None:
        return self._outcomes.get(request_id)

    def __len__(self) -> int:
        return len(self._outcomes)


def make_result_handler(store: OutcomeStore) -> Any:
    """Build the adapter ``result_handler(result, message)``.

    An exception here fails the message, so Service Bus retries it and eventually dead-letters it.
    The log line carries IDs and sizes only: never the question, the answer, or the body.
    """

    def handle(result: Any, msg: MessageLike) -> None:
        request = parse_request(msg)
        answer = final_answer(result).text
        store.put(Outcome(request_id=request.request_id, answer=answer))
        logger.info(
            "agent outcome recorded request_id=%s message_id=%s delivery_count=%s answer_chars=%d",
            request.request_id,
            msg.message_id,
            getattr(msg, "delivery_count", None),
            len(answer),
        )

    return handle
