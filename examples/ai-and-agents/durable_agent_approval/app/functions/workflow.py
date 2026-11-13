"""HTTP starter, status, approval and cancel routes plus the orchestrator and its activities.

Division of labour: the orchestrator only sequences, waits and decides. Every call that touches a
model, a graph, a clock-free side effect or the network happens in an activity.
"""

from __future__ import annotations

import json
import logging
import uuid
from collections.abc import Generator
from datetime import timedelta
from functools import lru_cache
from typing import Any

import azure.durable_functions as df
import azure.functions as func

from app.core.limits import (
    APPROVAL_EVENT_NAME,
    DRAFT_MAX_ATTEMPTS,
    DRAFT_RETRY_INTERVAL_MS,
    STAGE_AWAITING_APPROVAL,
    STAGE_DRAFTING,
    STAGE_PUBLISHING,
)
from app.services.agent import ChatModel, build_model, run_agent
from app.services.workflow import (
    InMemorySink,
    RequestError,
    ResultSink,
    clamp_timeout,
    is_approval,
    is_terminal,
    normalize_status,
    parse_decision,
    parse_run_request,
    publish_approved,
)

bp = df.Blueprint()
logger = logging.getLogger(__name__)

ORCHESTRATOR_NAME = "agent_approval_orchestrator"


class AgentActivityError(RuntimeError):
    """Fixed-text failure. Durable stores an activity's exception text in orchestration history, so
    activities raise this instead of letting provider or prompt text reach the history."""


@lru_cache(maxsize=1)
def get_model() -> ChatModel:
    return build_model()


@lru_cache(maxsize=1)
def get_sink() -> ResultSink:
    return InMemorySink()


def _json(body: dict[str, Any], status_code: int = 200, **headers: str) -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps(body), status_code=status_code, mimetype="application/json", headers=headers
    )


def _runtime(status: Any) -> str | None:
    value = getattr(status, "runtime_status", None)
    return None if value is None else str(getattr(value, "value", value))


# --- HTTP surface ---------------------------------------------------------------------------
# The built-in Durable management URLs are authorised by the Durable system key, which grants
# access to every Durable HTTP API. These routes are narrow and use the function key instead.


@bp.route(route="agent-runs", methods=["POST"], auth_level=func.AuthLevel.FUNCTION)
@bp.durable_client_input(client_name="client")
async def start_run(
    req: func.HttpRequest, client: df.DurableOrchestrationClient, context: func.Context
) -> func.HttpResponse:
    """Start a run and return 202 at once; the request is never held open for the agent work."""
    try:
        run = parse_run_request(req.get_body())
    except RequestError as exc:
        return _json({"error": str(exc)}, 400)
    run_id = uuid.uuid4().hex
    try:
        await client.start_new(
            ORCHESTRATOR_NAME,
            instance_id=run_id,
            client_input={
                "prompt": run.prompt,
                "approval_timeout_seconds": run.approval_timeout_seconds,
            },
        )
    except Exception:
        logger.exception("Failed to start run invocation=%s", context.invocation_id)
        return _json({"error": "could not start the run"}, 502)
    logger.info("Started run_id=%s invocation=%s", run_id, context.invocation_id)
    base = f"/api/agent-runs/{run_id}"
    return _json(
        {
            "run_id": run_id,
            "status_url": base,
            "approval_url": f"{base}/approval",
            "cancel_url": f"{base}/cancel",
        },
        202,
        Location=base,
    )


@bp.route(route="agent-runs/{run_id}", methods=["GET"], auth_level=func.AuthLevel.FUNCTION)
@bp.durable_client_input(client_name="client")
async def get_run(
    req: func.HttpRequest, client: df.DurableOrchestrationClient
) -> func.HttpResponse:
    run_id = req.route_params["run_id"]
    status = await client.get_status(run_id)
    view = normalize_status(_runtime(status), status.custom_status, status.output)
    if view is None:
        # Right after a start the instance may not be visible yet, so 404 is "not found yet".
        return _json({"run_id": run_id, "error": "run not found"}, 404)
    return _json({"run_id": run_id, **view})


@bp.route(
    route="agent-runs/{run_id}/approval", methods=["POST"], auth_level=func.AuthLevel.FUNCTION
)
@bp.durable_client_input(client_name="client")
async def submit_approval(
    req: func.HttpRequest, client: df.DurableOrchestrationClient, context: func.Context
) -> func.HttpResponse:
    """Deliver the human decision. Only accepted while the run is waiting for it."""
    run_id = req.route_params["run_id"]
    try:
        approved = parse_decision(req.get_body())
    except RequestError as exc:
        return _json({"error": str(exc)}, 400)
    status = await client.get_status(run_id)
    view = normalize_status(_runtime(status), status.custom_status, status.output)
    if view is None:
        return _json({"run_id": run_id, "error": "run not found"}, 404)
    if view["status"] != "awaiting_approval":
        return _json({"run_id": run_id, "error": "run is not awaiting approval"}, 409)
    try:
        await client.raise_event(run_id, APPROVAL_EVENT_NAME, {"approved": approved})
    except Exception:
        logger.exception(
            "Failed to raise approval run_id=%s invocation=%s", run_id, context.invocation_id
        )
        return _json({"run_id": run_id, "error": "could not deliver the decision"}, 502)
    logger.info("Decision delivered run_id=%s approved=%s", run_id, approved)
    return _json({"run_id": run_id, "status": "decision_sent"}, 202)


@bp.route(route="agent-runs/{run_id}/cancel", methods=["POST"], auth_level=func.AuthLevel.FUNCTION)
@bp.durable_client_input(client_name="client")
async def cancel_run(
    req: func.HttpRequest, client: df.DurableOrchestrationClient, context: func.Context
) -> func.HttpResponse:
    """Ask Durable to terminate the orchestration; poll the status URL for the outcome.

    Termination ends the orchestration instance. This recipe does not claim it interrupts an
    activity that is already running, so ``cancel_requested`` is an acknowledgement, not a result.
    """
    run_id = req.route_params["run_id"]
    status = await client.get_status(run_id)
    runtime = _runtime(status)
    view = normalize_status(runtime, status.custom_status, status.output)
    if view is None:
        return _json({"run_id": run_id, "error": "run not found"}, 404)
    if is_terminal(runtime):
        return _json({"run_id": run_id, "status": view["status"]})
    try:
        await client.terminate(run_id, "cancelled by caller")
    except Exception:
        logger.exception(
            "Failed to terminate run_id=%s invocation=%s", run_id, context.invocation_id
        )
        return _json({"run_id": run_id, "error": "could not request cancellation"}, 502)
    logger.info("Cancel requested run_id=%s invocation=%s", run_id, context.invocation_id)
    return _json({"run_id": run_id, "status": "cancel_requested"}, 202)


# --- orchestrator ---------------------------------------------------------------------------


@bp.orchestration_trigger(context_name="context")
def agent_approval_orchestrator(
    context: df.DurableOrchestrationContext,
) -> Generator[Any, Any, dict[str, Any]]:
    """Draft -> wait for approval or timeout -> publish.

    Replay-safe by construction: it uses only ``context`` APIs for time and I/O, makes no model,
    network, random or clock calls, and logs only when ``context.is_replaying`` is false.
    """
    run_id = context.instance_id
    request = context.get_input() or {}
    timeout_seconds = clamp_timeout(request.get("approval_timeout_seconds"))

    context.set_custom_status({"stage": STAGE_DRAFTING})
    try:
        drafted = yield context.call_activity_with_retry(
            "run_agent_draft",
            df.RetryOptions(DRAFT_RETRY_INTERVAL_MS, DRAFT_MAX_ATTEMPTS),
            {"run_id": run_id, "prompt": request.get("prompt", "")},
        )
    except Exception:
        if not context.is_replaying:
            logger.warning("Draft stage failed run_id=%s", run_id)
        return {"outcome": "failed", "run_id": run_id, "stage": "draft"}
    draft = str(drafted["draft"])

    # The reviewer must see the draft, so it is placed in the (bounded) custom status.
    context.set_custom_status({"stage": STAGE_AWAITING_APPROVAL, "draft": draft})
    deadline = context.current_utc_datetime + timedelta(seconds=timeout_seconds)
    approval_task = context.wait_for_external_event(APPROVAL_EVENT_NAME)
    timeout_task = context.create_timer(deadline)
    winner = yield context.task_any([approval_task, timeout_task])

    if winner != approval_task:
        # Timeout never authorises the action.
        if not context.is_replaying:
            logger.info("Approval timed out run_id=%s", run_id)
        return {"outcome": "timed_out", "run_id": run_id}

    timeout_task.cancel()
    if not is_approval(approval_task.result):
        return {"outcome": "rejected", "run_id": run_id}

    context.set_custom_status({"stage": STAGE_PUBLISHING})
    try:
        published = yield context.call_activity(
            "publish_approved_result", {"run_id": run_id, "draft": draft}
        )
    except Exception:
        # The effect may or may not have happened: report that honestly.
        return {"outcome": "failed", "run_id": run_id, "stage": "publish", "effect_unknown": True}
    return {"outcome": "completed", "run_id": run_id, **published}


# --- activities -----------------------------------------------------------------------------


@bp.activity_trigger(input_name="payload")
def run_agent_draft(payload: dict[str, Any]) -> dict[str, str]:
    """Run the LangGraph draft. Read-only, so the orchestrator may retry it safely."""
    run_id = str(payload["run_id"])
    try:
        draft = run_agent(str(payload["prompt"]), run_id=run_id, model=get_model())
    except Exception:
        # Full detail stays in the host log; the exception Durable records has fixed text.
        logger.exception("Agent draft failed run_id=%s", run_id)
        raise AgentActivityError("agent_draft_failed") from None
    logger.info("Drafted run_id=%s draft_chars=%d", run_id, len(draft))
    return {"draft": draft}


@bp.activity_trigger(input_name="payload")
def publish_approved_result(payload: dict[str, Any]) -> dict[str, Any]:
    """The final action. Activities are at-least-once, so this is idempotent per ``run_id``."""
    run_id = str(payload["run_id"])
    try:
        result = publish_approved(run_id, str(payload["draft"]), get_sink())
    except Exception:
        logger.exception("Publish failed run_id=%s", run_id)
        raise AgentActivityError("publish_failed") from None
    logger.info("Published run_id=%s duplicate_delivery=%s", run_id, result["duplicate_delivery"])
    return result
