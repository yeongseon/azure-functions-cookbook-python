# pyright: reportMissingImports=false, reportUnknownMemberType=false, reportUnknownArgumentType=false
"""Tests for the public API surface of azure-functions-cookbook-python."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import azure_functions_python_cookbook


class TestAPISurface:
    """Verify __all__ matches exactly the declared public names."""

    def test_all_exports(self) -> None:
        assert set(azure_functions_python_cookbook.__all__) == {"__version__"}

    def test_version_matches_distribution_metadata(self) -> None:
        from importlib.metadata import version

        expected = version("azure-functions-cookbook-python")
        assert azure_functions_python_cookbook.__version__ == expected

    def test_version_is_string(self) -> None:
        assert isinstance(azure_functions_python_cookbook.__version__, str)
