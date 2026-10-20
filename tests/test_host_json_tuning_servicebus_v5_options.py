"""Regression coverage for #378: update Service Bus tuning to extension 5
settings.

host_json_tuning selects extension bundle [4.*, 5.0.0), whose Service Bus
extension (WebJobs.Extensions.ServiceBus 5.x) exposes maxConcurrentCalls
and maxAutoLockRenewalDuration directly under extensions.serviceBus; it has
no messageHandlerOptions property. The checked-in host.json nested both
settings under the obsolete v4 messageHandlerOptions block, so the
selected v5 extension never read them -- a readable JSON file and the
recipe's own passing timer trigger could not reveal this, since the timer
trigger never exercises Service Bus options binding.

Reads only the checked-in host.json; no host process or Azure service is
started.
"""

from __future__ import annotations

import json
from pathlib import Path

EXAMPLE_DIR = (
    Path(__file__).resolve().parents[1] / "examples" / "runtime-and-ops" / "host_json_tuning"
)


def _service_bus_options() -> dict[str, object]:
    host_json = json.loads((EXAMPLE_DIR / "host.json").read_text())
    service_bus: dict[str, object] = host_json["extensions"]["serviceBus"]
    return service_bus


def test_service_bus_options_use_the_v5_flat_schema() -> None:
    service_bus = _service_bus_options()

    assert "messageHandlerOptions" not in service_bus
    assert service_bus["maxConcurrentCalls"] == 32
    assert service_bus["maxAutoLockRenewalDuration"] == "00:05:00"
    assert service_bus["prefetchCount"] == 100


def test_extension_bundle_range_matches_the_documented_v5_tuning_contract() -> None:
    host_json = json.loads((EXAMPLE_DIR / "host.json").read_text())

    # The checked-in options above are only correct for the selected
    # bundle range's major Service Bus extension version (5.x); pinning
    # this assertion prevents a bundle-range bump from silently
    # invalidating the flat-schema fix without updating host.json.
    assert host_json["extensionBundle"]["version"] == "[4.*, 5.0.0)"


def test_readme_and_docs_page_no_longer_teach_the_obsolete_v4_option_name() -> None:
    readme = (EXAMPLE_DIR / "README.md").read_text()
    docs_page = (
        EXAMPLE_DIR.parents[2] / "docs" / "patterns" / "runtime-and-ops" / "host-json-tuning.md"
    ).read_text()

    assert "messageHandlerOptions" not in readme
    assert "maxAutoRenewDuration" not in readme
    assert "messageHandlerOptions" not in docs_page
