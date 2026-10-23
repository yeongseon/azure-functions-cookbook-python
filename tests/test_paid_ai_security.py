"""Offline binding and data-boundary checks; these do not emulate host authorization."""

from __future__ import annotations

import json
import logging
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock

import azure.functions as func
import pytest

from tests._isolation import load_example_module

RECIPES = ("openai_direct_chat", "ai_image_generation", "streaming_ai_response")
CANARIES = ("fake-private-prompt-canary", "fake-api-key-canary", "fake-response-canary")


@pytest.fixture(params=RECIPES)
def recipe(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    monkeypatch.delenv("COOKBOOK_PUBLIC_DEMO", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_ENDPOINT", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_KEY", raising=False)
    return load_example_module(f"ai-and-agents/{request.param}")


def invoke(recipe: ModuleType, payload: bytes) -> func.HttpResponse:
    function = recipe.app.get_functions()[0].get_user_function()
    response = function(
        func.HttpRequest(
            method="POST",
            url="https://example.invalid/api/test",
            body=payload,
            headers={"Content-Type": "application/json", "Authorization": "fake-auth-canary"},
        ),
        context=None,
    )
    assert isinstance(response, func.HttpResponse)
    return response


def request_body(recipe: ModuleType, prompt: str) -> bytes:
    field = "prompt" if hasattr(recipe, "ImageRequest") else "message"
    return json.dumps({field: prompt}).encode()


def test_binding_requires_key_by_default(recipe: ModuleType) -> None:
    # Given the default environment; when the worker indexes the app;
    # then its HTTP binding is protected (not proof of Azure enforcement).
    trigger = recipe.app.get_functions()[0].get_trigger()
    assert trigger.get_dict_repr()["authLevel"] == func.AuthLevel.FUNCTION


@pytest.mark.parametrize(
    "setting,expected",
    [
        (value, "anonymous" if value == "true" else "function")
        for value in ("true", "True", "TRUE", "1", "yes", "false", "", " true ", "true\n")
    ],
)
@pytest.mark.parametrize("name", RECIPES)
def test_public_demo_requires_explicit_opt_in(
    name: str,
    setting: str,
    expected: str,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    # Given an explicit setting; when imported; then binding and warning agree.
    monkeypatch.setenv("COOKBOOK_PUBLIC_DEMO", setting)
    with caplog.at_level(logging.DEBUG):
        module = load_example_module(f"ai-and-agents/{name}")
    assert (
        module.app.get_functions()[0].get_trigger().get_dict_repr()["authLevel"].value == expected
    )
    assert any(record.levelno == logging.WARNING for record in caplog.records) == (
        setting == "true"
    )


@pytest.mark.parametrize("kind", ["body", "prompt", "system"])
def test_oversized_input_never_calls_provider(
    recipe: ModuleType,
    kind: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Given oversized input and a provider spy; when invoked; then no work is billed.
    client = MagicMock()
    monkeypatch.setattr(recipe, "AzureOpenAI", client)
    if kind == "body":
        payload = b" " * (recipe.MAX_REQUEST_BYTES + 1)
    elif kind == "system" and not hasattr(recipe, "ImageRequest"):
        payload = json.dumps({"message": "ok", "system_prompt": "x" * 4001}).encode()
    else:
        payload = request_body(recipe, "x" * 4001)
    response = invoke(recipe, payload)
    assert response.status_code == (413 if kind == "body" else 422)
    client.assert_not_called()


def test_malformed_json_returns_400(recipe: ModuleType) -> None:
    assert invoke(recipe, b"{invalid").status_code == 400


@pytest.mark.parametrize("failure", [False, True])
def test_budget_and_redaction_at_provider_boundary(
    recipe: ModuleType,
    failure: bool,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    # Given fake credentials and provider output/error; when called; then bounded,
    # sanitized results never leak request/credential/response canaries to logs.
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://example.invalid")
    monkeypatch.setenv("AZURE_OPENAI_KEY", CANARIES[1])
    factory = MagicMock()
    client = factory.return_value
    monkeypatch.setattr(recipe, "AzureOpenAI", factory)
    if hasattr(recipe, "ImageRequest"):
        operation = client.images.generate
        operation.return_value = SimpleNamespace(
            data=[
                SimpleNamespace(
                    url="https://example.invalid/image",
                    revised_prompt=CANARIES[2],
                )
            ]
        )
    else:
        operation = client.chat.completions.create
        operation.return_value = (
            [SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=CANARIES[2]))])]
            if hasattr(recipe, "StreamRequest")
            else SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content=CANARIES[2]))],
            )
        )
    if failure:
        operation.side_effect = recipe.OpenAIError(" ".join(CANARIES))
    with caplog.at_level(logging.DEBUG):
        response = invoke(recipe, request_body(recipe, CANARIES[0]))
    assert response.status_code == (502 if failure else 200)
    budget = operation.call_args.kwargs
    if hasattr(recipe, "ImageRequest"):
        assert budget["n"] == 1
        assert budget["quality"] == "standard"
    else:
        assert budget["max_tokens"] == 256
    if failure:
        assert all(value.encode() not in response.get_body() for value in CANARIES)
    assert all(value not in caplog.text for value in (*CANARIES, "fake-auth-canary"))


def test_missing_credentials_keeps_offline_fallback(recipe: ModuleType) -> None:
    # Given no credentials; when invoked; then the sample remains runnable offline.
    assert invoke(recipe, request_body(recipe, "hello")).status_code == 200
