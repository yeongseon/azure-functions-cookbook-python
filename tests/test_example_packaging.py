from pathlib import Path
import subprocess
import zipfile


def test_full_stack_crud_wheel_contains_flat_modules(tmp_path: Path) -> None:
    example = Path("examples/apis-and-ingress/full_stack_crud_api")

    subprocess.run(["uv", "build", "--out-dir", str(tmp_path)], cwd=example, check=True)
    wheel_path = next(tmp_path.glob("*.whl"))

    with zipfile.ZipFile(wheel_path) as wheel:
        names = wheel.namelist()

    assert "function_app.py" in names
    assert "models.py" in names
