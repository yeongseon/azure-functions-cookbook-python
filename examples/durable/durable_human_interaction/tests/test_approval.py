from app.services.approval_service import APPROVAL_EVENT_NAME, APPROVED_STATUS, TIMED_OUT_STATUS


def test_approval_constants_are_stable() -> None:
    assert APPROVAL_EVENT_NAME == "ApprovalEvent"
    assert APPROVED_STATUS == "Approved"
    assert TIMED_OUT_STATUS == "Timed out"
