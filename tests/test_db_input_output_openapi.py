from __future__ import annotations

import json
from typing import cast

from azure_functions_openapi import clear_openapi_registry, get_openapi_json, scan_endpoint_metadata

from tests._isolation import load_example_module

EXAMPLE = "data-and-pipelines/db_input_output"


def _generate_spec() -> dict[str, object]:
    clear_openapi_registry()
    module = load_example_module(EXAMPLE)
    db_available = cast(bool, getattr(module, "_db_available"))
    assert db_available is True, "db_input_output regression test requires azure-functions-db"
    app = cast(object, getattr(module, "app"))
    scan_endpoint_metadata(app)
    return cast(dict[str, object], json.loads(get_openapi_json()))


def test_db_input_output_list_response_stays_a_bare_item_array() -> None:
    spec = _generate_spec()

    paths = cast(dict[str, object], spec["paths"])
    path_item = cast(dict[str, object], paths["/api/items"])

    operation = cast(dict[str, object], path_item["get"])
    responses = cast(dict[str, object], operation["responses"])
    response_200 = cast(dict[str, object], responses["200"])
    content = cast(dict[str, object], response_200["content"])
    application_json = cast(dict[str, object], content["application/json"])
    schema = cast(dict[str, object], application_json["schema"])

    assert schema["type"] == "array"
    items = cast(dict[str, object], schema["items"])
    assert items["type"] == "object"
    assert items["title"] == "ItemResponse"
    assert items["required"] == ["id", "name", "category", "price"]
    assert items["properties"] == {
        "id": {"title": "Id", "type": "string"},
        "name": {"title": "Name", "type": "string"},
        "category": {"title": "Category", "type": "string"},
        "price": {"title": "Price", "type": "number"},
    }
