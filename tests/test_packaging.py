from pathlib import Path
import subprocess
import zipfile


def test_wheel_contains_cookbook_package(tmp_path: Path) -> None:
    config = Path("pyproject.toml").read_text()
    assert 'packages = ["src/azure_functions_python_cookbook"]' in config

    subprocess.run(["uv", "build", "--out-dir", str(tmp_path)], check=True)
    wheel_path = next(tmp_path.glob("*.whl"))

    with zipfile.ZipFile(wheel_path) as wheel:
        names = wheel.namelist()

    assert "azure_functions_python_cookbook/__init__.py" in names
    assert "azure_functions_python_cookbook/recipes.py" in names
