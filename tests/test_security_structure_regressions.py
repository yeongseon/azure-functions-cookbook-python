from pathlib import Path

import pytest

from tools.security_report import Status
from tools.security_structure import check_structure


@pytest.mark.parametrize("key", ["minTlsVersion", "scmMinTlsVersion", "minimumTlsVersion"])
@pytest.mark.parametrize("version", ["1.0", "1.1", "TLS1_0", "TLS1_1", "1.2", "TLS1_2"])
def test_transport_versions_fail_closed(tmp_path: Path, key: str, version: str) -> None:
    # Given a deployment declaration using either Azure TLS spelling.
    directory = tmp_path / "infra"
    directory.mkdir()
    (directory / "main.bicep").write_text(f"{key}: '{version}'\n")
    # When scanning structure, then only TLS 1.2 passes.
    result = check_structure(tmp_path)
    assert result.status == (Status.PASS if version in {"1.2", "TLS1_2"} else Status.FAIL)


def test_empty_deployment_inventory_is_incomplete(tmp_path: Path) -> None:
    # Given a checkout without deployment files, when scanned, then no clean claim is made.
    result = check_structure(tmp_path)
    assert result.status == Status.INCOMPLETE
    assert result.counts["files"] == 0
