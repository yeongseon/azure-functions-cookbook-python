# pyright: reportMissingImports=false, reportUnknownVariableType=false
import re

from azure_functions_python_cookbook import __version__


def test_version_is_present() -> None:
    assert isinstance(__version__, str)
    assert re.fullmatch(r"\d+\.\d+\.\d+([-.].+)?", __version__), (
        f"__version__ is not a valid version string: {__version__!r}"
    )
