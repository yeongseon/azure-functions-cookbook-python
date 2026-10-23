from datetime import UTC, datetime, timedelta, timezone
import json
from pathlib import Path
from unittest.mock import patch

from tools.security_exceptions import apply_policy
from tools.security_report import Check, Finding, Status


def test_exception_dates_use_utc_at_kst_midnight(tmp_path: Path) -> None:
    instant = datetime(2026, 10, 22, 15, 30, tzinfo=UTC)
    assert instant.astimezone(timezone(timedelta(hours=9))).day == 23
    policy = tmp_path / "policy.json"
    policy.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "exceptions": [
                    {
                        "id": "CVE-2099-0001",
                        "package": "demo",
                        "reason": "reviewed",
                        "owner": "maintainer",
                        "added": "2026-10-21",
                        "expires": "2026-10-22",
                    }
                ],
            }
        )
    )
    check = Check("audit", Status.FAIL, findings=(Finding("CVE-2099-0001", package="demo"),))
    with (
        patch("tools.security_exceptions.datetime", create=True) as clock,
        patch("tools.security_exceptions.date") as local_date,
    ):
        clock.now.return_value = instant
        local_date.today.return_value = instant.astimezone(timezone(timedelta(hours=9))).date()
        local_date.fromisoformat.side_effect = __import__("datetime").date.fromisoformat
        assert apply_policy(check, policy).status == Status.PASS
        clock.now.assert_called_once_with(UTC)
