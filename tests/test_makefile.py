from pathlib import Path
import subprocess


def test_doctor_recipe_preserves_failed_check_status() -> None:
    recipe = next(
        line.strip().removeprefix("@").replace("$(MAKE) check-all", "false")
        for line in Path("Makefile").read_text().splitlines()
        if "Some checks failed." in line
    )

    result = subprocess.run(["sh", "-c", recipe], check=False, capture_output=True, text=True)

    assert result.returncode != 0
    assert "Some checks failed." in result.stdout
