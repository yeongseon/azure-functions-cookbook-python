"""A scripted fake of the Durable orchestration context (no Durable host, no replay engine).

``drive`` runs an orchestrator generator the way the host would at the level this recipe cares
about: each yielded task is resolved from a scenario, and every context call is recorded so tests
can assert what was scheduled and in which order.
"""

from __future__ import annotations

from collections.abc import Generator
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


class FakeTask:
    def __init__(self, kind: str, name: str = "", children: list[FakeTask] | None = None) -> None:
        self.kind = kind
        self.name = name
        self.children = children or []
        self.is_completed = False
        self.result: Any = None
        self.cancelled = False

    def cancel(self) -> None:
        self.cancelled = True


class FakeContext:
    instance_id = "run-123"
    current_utc_datetime = datetime(2030, 1, 1, 12, 0, tzinfo=UTC)

    def __init__(self, input_: Any = None, *, replaying: bool = False) -> None:
        self._input = input_
        self.is_replaying = replaying
        self.calls: list[tuple[Any, ...]] = []
        self.statuses: list[Any] = []
        self.timers: list[FakeTask] = []
        self.events: list[FakeTask] = []

    def get_input(self) -> Any:
        return self._input

    def set_custom_status(self, value: Any) -> None:
        self.statuses.append(value)

    def call_activity(self, name: str, input_: Any = None) -> FakeTask:
        self.calls.append(("activity", name, input_))
        return FakeTask("activity", name)

    def call_activity_with_retry(
        self, name: str, retry_options: Any, input_: Any = None
    ) -> FakeTask:
        self.calls.append(
            (
                "activity_retry",
                name,
                input_,
                retry_options.first_retry_interval_in_milliseconds,
                retry_options.max_number_of_attempts,
            )
        )
        return FakeTask("activity", name)

    def wait_for_external_event(self, name: str) -> FakeTask:
        self.calls.append(("event", name))
        task = FakeTask("event", name)
        self.events.append(task)
        return task

    def create_timer(self, fire_at: datetime) -> FakeTask:
        self.calls.append(("timer", fire_at))
        task = FakeTask("timer")
        self.timers.append(task)
        return task

    def task_any(self, tasks: list[FakeTask]) -> FakeTask:
        self.calls.append(("any", tuple(t.kind for t in tasks)))
        return FakeTask("any", children=tasks)


@dataclass
class Scenario:
    draft: Any = field(default_factory=lambda: {"draft": "DRAFT"})  # dict, or an Exception
    race: tuple[str, Any] = ("approval", {"approved": True})  # ("approval", payload) | ("timeout",)
    publish: Any = field(default_factory=lambda: {"receipt": "r1", "chars": 5})


def drive(gen: Generator[Any, Any, Any], scenario: Scenario) -> Any:
    """Run the orchestrator to completion and return its result."""
    try:
        yielded = next(gen)
        while True:
            if yielded.kind == "any":
                kinds = {t.kind: t for t in yielded.children}
                if scenario.race[0] == "approval":
                    kinds["event"].result = scenario.race[1]
                    kinds["event"].is_completed = True
                    send: Any = kinds["event"]
                else:
                    kinds["timer"].is_completed = True
                    send = kinds["timer"]
                yielded = gen.send(send)
                continue
            outcome = scenario.draft if yielded.name == "run_agent_draft" else scenario.publish
            if isinstance(outcome, Exception):
                yielded = gen.throw(outcome)
            else:
                yielded = gen.send(outcome)
    except StopIteration as stop:
        return stop.value


def registered_functions() -> dict[str, Any]:
    """Registered Functions by name. ``get_functions()`` validates names and may only run once per
    app, so every test module shares this single call."""
    global _FUNCTIONS
    if _FUNCTIONS is None:
        from function_app import app

        _FUNCTIONS = {str(f.get_function_name()): f for f in app.get_functions()}
    return _FUNCTIONS


_FUNCTIONS: dict[str, Any] | None = None
