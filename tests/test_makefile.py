from pathlib import Path
import subprocess
import sys


def test_doctor_recipe_preserves_failed_check_status(tmp_path: Path) -> None:
    environment = Path(sys.executable).parent
    result = subprocess.run(
        ["make", "doctor", "CI=1", f"PYTHON={environment / 'python'}"],
        env={"PATH": str(tmp_path), "VIRTUAL_ENV": str(environment.parent)},
        executable="/usr/bin/make",
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "INCOMPLETE" in result.stdout
    assert "pytest" not in result.args[0]
