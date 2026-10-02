"""Azure Functions Python Cookbook package metadata."""

import sys
import warnings

__all__ = ["__version__"]

__version__ = "0.3.1"  # x-release-please-version


if sys.version_info < (3, 11):
    warnings.warn(
        "azure-functions-cookbook-python will drop support for Python 3.10 "
        "in its next minor release. "
        "Python 3.10 reaches end of life in October 2026; upgrade to Python 3.11 "
        "or newer to keep receiving updates.",
        FutureWarning,
        stacklevel=2,
    )
