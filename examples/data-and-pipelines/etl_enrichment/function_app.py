from __future__ import annotations

# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUntypedFunctionDecorator=false, reportUnknownParameterType=false, reportUnknownArgumentType=false, reportAny=false

import json
from typing import TypedDict

import azure.functions as func
from azure_functions_db import DbBindings, DbOut
from azure_functions_logging import get_logger, setup_logging

setup_logging(format="json")
logger = get_logger(__name__)

db = DbBindings()
app = func.FunctionApp()


class RawRecord(TypedDict):
    customer_id: str
    city: str
    country_code: str


class LookupResult(TypedDict):
    region: str
    market_tier: str
    latitude: float
    longitude: float


REGION_LOOKUPS: dict[str, LookupResult] = {
    "US": {
        "region": "north-america",
        "market_tier": "tier-1",
        "latitude": 47.6062,
        "longitude": -122.3321,
    },
    "DE": {
        "region": "europe",
        "market_tier": "tier-1",
        "latitude": 52.52,
        "longitude": 13.405,
    },
    "JP": {
        "region": "asia-pacific",
        "market_tier": "tier-1",
        "latitude": 35.6764,
        "longitude": 139.65,
    },
}

FALLBACK_LOOKUP: LookupResult = {
    "region": "unknown",
    "market_tier": "tier-3",
    "latitude": 0.0,
    "longitude": 0.0,
}


@app.blob_trigger(
    arg_name="myblob",
    path="raw-data/{name}",
    connection="AzureWebJobsStorage",
)
@db.output("out", url="%DB_URL%", table="enriched_customers")
def etl_enrich_blob(myblob: func.InputStream, out: DbOut) -> None:
    blob_name = myblob.name or "unknown"
    payload = myblob.read()

    logger.info(
        "ETL extraction started",
        extra={"blob_name": blob_name, "size_bytes": len(payload)},
    )

    raw_records = _load_raw_records(payload)
    enriched_rows = [_enrich_record(record, blob_name=blob_name) for record in raw_records]

    out.set(enriched_rows)

    logger.info(
        "ETL enrichment completed",
        extra={
            "blob_name": blob_name,
            "input_count": len(raw_records),
            "enriched_count": len(enriched_rows),
        },
    )
    logger.info(
        "Loaded enriched rows",
        extra={"target_table": "enriched_customers", "count": len(enriched_rows)},
    )


def _load_raw_records(payload: bytes) -> list[RawRecord]:
    if not payload:
        raise ValueError("Input blob is empty.")

    loaded = json.loads(payload.decode("utf-8-sig"))
    if not isinstance(loaded, list):
        raise ValueError("Input blob must contain a JSON array of objects.")

    normalized: list[RawRecord] = []
    for index, item in enumerate(loaded, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Record {index} must be a JSON object.")
        normalized.append(_normalize_record(item, index=index))

    return normalized


def _normalize_record(item: dict[str, object], *, index: int) -> RawRecord:
    customer_id = str(item.get("customer_id", "")).strip()
    city = str(item.get("city", "")).strip()
    country_code = str(item.get("country_code", "")).strip().upper()

    if not customer_id or not city or not country_code:
        raise ValueError(
            f"Record {index} is missing one of required fields: customer_id, city, country_code."
        )

    return {
        "customer_id": customer_id,
        "city": city,
        "country_code": country_code,
    }


def _enrich_record(record: RawRecord, *, blob_name: str) -> dict[str, str | float]:
    lookup = _lookup_location(record["country_code"])
    enriched = {
        "customer_id": record["customer_id"],
        "source_blob": blob_name,
        "city": record["city"],
        "country_code": record["country_code"],
        "region": lookup["region"],
        "market_tier": lookup["market_tier"],
        "latitude": lookup["latitude"],
        "longitude": lookup["longitude"],
    }

    logger.info(
        "Record enriched",
        extra={
            "customer_id": enriched["customer_id"],
            "country_code": enriched["country_code"],
            "region": enriched["region"],
        },
    )
    return enriched


def _lookup_location(country_code: str) -> LookupResult:
    return REGION_LOOKUPS.get(country_code, FALLBACK_LOOKUP)
