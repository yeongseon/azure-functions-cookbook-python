from __future__ import annotations

from app.services.eventgrid_service import process_blob_event


def test_process_blob_event_returns_summary() -> None:
    assert (
        process_blob_event(name="events/photo.png", size=2048)
        == "Blob processing (Event Grid) complete for events/photo.png (2048 bytes)"
    )
