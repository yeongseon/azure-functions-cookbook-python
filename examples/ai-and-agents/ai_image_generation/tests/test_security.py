import importlib.util
import sys
from pathlib import Path

import azure.functions as func


def test_default_binding_and_offline_budget(monkeypatch):
    monkeypatch.delenv("COOKBOOK_PUBLIC_DEMO", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_KEY", raising=False)
    spec = importlib.util.spec_from_file_location(
        "function_app", Path(__file__).parents[1] / "function_app.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    assert (
        module.app.get_functions()[0].get_trigger().get_dict_repr()["authLevel"]
        == func.AuthLevel.FUNCTION
    )
    assert module.MAX_IMAGES == 1
    assert module._generate_image("hello", "1024x1024").image_url.endswith("fallback-image.png")
