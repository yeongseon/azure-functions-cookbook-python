from __future__ import annotations

import pytest
from conftest import make_message, request

from app.contract import (
    MAX_BODY_BYTES,
    MAX_QUESTION_CHARS,
    InvalidMessageError,
    map_input,
    parse_request,
    thread_id_for,
)


def test_parse_valid_request() -> None:
    parsed = parse_request(request("req-7", "  Where is A-1001?  ", conversation_id="conv-9"))

    assert (parsed.request_id, parsed.question, parsed.conversation_id) == (
        "req-7",
        "Where is A-1001?",
        "conv-9",
    )


def test_map_input_derives_a_stable_message_id_from_request_id() -> None:
    graph_input = map_input(request("req-7"))

    (human,) = graph_input["messages"]
    assert graph_input["request_id"] == "req-7"
    assert human.type == "human"
    assert human.id == "req-7:question"
    assert human.content == "Where is order A-1001?"


@pytest.mark.parametrize(
    ("body", "reason"),
    [
        (b"not json", "valid UTF-8 JSON"),
        (b"\xff\xfe", "valid UTF-8 JSON"),
        (b"[1, 2]", "JSON object"),
        (b'{"question": "hi"}', "'request_id' is required"),
        (b'{"request_id": "bad id!", "question": "hi"}', "'request_id' must be"),
        (b'{"request_id": 7, "question": "hi"}', "'request_id' must be"),
        (b'{"request_id": "r"}', "'question' must be a non-empty string"),
        (b'{"request_id": "r", "question": "   "}', "'question' must be a non-empty string"),
        (b'{"request_id": "r", "question": "q", "conversation_id": "a b"}', "'conversation_id'"),
        (b"{" + b" " * MAX_BODY_BYTES + b"}", "body exceeds"),
    ],
)
def test_malformed_bodies_are_rejected(body: bytes, reason: str) -> None:
    with pytest.raises(InvalidMessageError, match=reason):
        parse_request(make_message(body))


def test_overlong_question_is_rejected() -> None:
    with pytest.raises(InvalidMessageError, match="exceeds"):
        parse_request(request(question="x" * (MAX_QUESTION_CHARS + 1)))


def test_rejection_never_echoes_producer_content() -> None:
    secret = "sk-very-secret-value"
    with pytest.raises(InvalidMessageError) as error:
        parse_request(make_message(f'{{"request_id": "{secret} !", "question": "q"}}'.encode()))

    assert secret not in str(error.value)


def test_thread_id_is_namespaced_and_defaults_to_one_thread_per_request() -> None:
    assert thread_id_for(request(conversation_id="conv-9")) == "sb:conversation:conv-9"
    assert thread_id_for(request("req-5")) == "sb:request:req-5"
