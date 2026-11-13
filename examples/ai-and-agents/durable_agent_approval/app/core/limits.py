"""Every bound the workflow enforces, in one place.

These are sample defaults chosen for a readable demo, not Azure limits. The one documented Azure
limit that shapes them: Python Durable timers are limited to six days, so the approval timeout
stays below that.
"""

from __future__ import annotations

MAX_PROMPT_CHARS = 2_000
MAX_DRAFT_CHARS = 2_000
MAX_REQUEST_BYTES = 8_192
MAX_MODEL_OUTPUT_TOKENS = 256
MODEL_TIMEOUT_SECONDS = 30.0
# LangGraph raises GraphRecursionError when a run takes more supersteps than this.
GRAPH_RECURSION_LIMIT = 6

DEFAULT_APPROVAL_TIMEOUT_SECONDS = 24 * 60 * 60
MIN_APPROVAL_TIMEOUT_SECONDS = 60
MAX_APPROVAL_TIMEOUT_SECONDS = 5 * 24 * 60 * 60

DRAFT_RETRY_INTERVAL_MS = 5_000
DRAFT_MAX_ATTEMPTS = 3

APPROVAL_EVENT_NAME = "ApprovalDecision"
STAGE_DRAFTING = "drafting"
STAGE_AWAITING_APPROVAL = "awaiting_approval"
STAGE_PUBLISHING = "publishing"
