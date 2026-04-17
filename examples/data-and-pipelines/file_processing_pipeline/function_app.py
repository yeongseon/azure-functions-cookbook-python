from __future__ import annotations

import csv
import io
import json
import uuid
from datetime import datetime, timezone
from pathlib import PurePosixPath
from typing import TypedDict

import azure.functions as func
from azure_functions_db import DbBindings, DbOut
from azure_functions_logging import get_logger, setup_logging

setup_logging(format="json")
logger = get_logger(__name__)

db = DbBindings()
app = func.FunctionApp()

REQUIRED_FIELDS = {"id", "category", "amount"}


class ValidatedRecord(TypedDict):
    id: str
    category: str
    amount: float


class TransformedRecord(TypedDict):
    record_id: str
    category: str
    amount: float
    status: str


RawRecord = dict[str, object]


@app.blob_trigger(
    arg_name="myblob",
    path="incoming/{name}",
    connection="AzureWebJobsStorage",
    source=func.BlobSource.EVENT_GRID,
)
@db.output("out", url="%DB_URL%", table="processed_files")
def process_uploaded_file(myblob: func.InputStream, out: DbOut) -> None:
    blob_name = myblob.name or "unknown"
    payload = myblob.read()

    logger.info(
        "Blob pipeline started",
        extra={"blob_name": blob_name, "size_bytes": len(payload)},
    )

    records, source_format = _load_records(blob_name=blob_name, payload=payload)
    validated_records = _validate_records(records, blob_name=blob_name)
    transformed_records = _transform_records(validated_records)
    persistence_record = _build_persistence_record(
        blob_name=blob_name,
        source_format=source_format,
        transformed_records=transformed_records,
    )

    out.set(persistence_record)

    logger.info(
        "Blob pipeline completed",
        extra={
            "blob_name": blob_name,
            "persisted_id": persistence_record["id"],
            "record_count": persistence_record["record_count"],
        },
    )


def _load_records(blob_name: str, payload: bytes) -> tuple[list[RawRecord], str]:
    if not payload:
        raise ValueError(f"Blob {blob_name} is empty.")

    extension = PurePosixPath(blob_name).suffix.lower()
    text = payload.decode("utf-8-sig").strip()

    if extension == ".json":
        records = _load_json_records(text)
        return records, "json"

    if extension == ".csv":
        records = _load_csv_records(text)
        return records, "csv"

    raise ValueError(f"Unsupported file type for {blob_name}. Expected .csv or .json.")


def _load_json_records(text: str) -> list[RawRecord]:
    payload = json.loads(text)

    if isinstance(payload, dict) and isinstance(payload.get("records"), list):
        payload = payload["records"]

    if not isinstance(payload, list) or not all(isinstance(item, dict) for item in payload):
        raise ValueError("JSON input must be a list of objects or an object with a 'records' list.")

    return [dict(item) for item in payload]


def _load_csv_records(text: str) -> list[RawRecord]:
    reader = csv.DictReader(io.StringIO(text))
    return [dict(row) for row in reader]


def _validate_records(records: list[RawRecord], blob_name: str) -> list[ValidatedRecord]:
    if not records:
        raise ValueError(f"Blob {blob_name} did not contain any records.")

    validated_records: list[ValidatedRecord] = []
    invalid_rows: list[int] = []

    for index, record in enumerate(records, start=1):
        if not REQUIRED_FIELDS.issubset(record):
            invalid_rows.append(index)
            continue

        if not str(record.get("id", "")).strip() or not str(record.get("category", "")).strip():
            invalid_rows.append(index)
            continue

        amount_value = record.get("amount", 0)
        if not isinstance(amount_value, (str, int, float)):
            invalid_rows.append(index)
            continue

        try:
            amount = float(amount_value)
        except (TypeError, ValueError):
            invalid_rows.append(index)
            continue

        validated_records.append(
            {
                "id": str(record.get("id", "")).strip(),
                "category": str(record.get("category", "")).strip(),
                "amount": amount,
            }
        )

    if invalid_rows:
        raise ValueError(f"Validation failed for rows {invalid_rows} in {blob_name}.")

    logger.info(
        "File validated",
        extra={"blob_name": blob_name, "record_count": len(validated_records)},
    )
    return validated_records


def _transform_records(records: list[ValidatedRecord]) -> list[TransformedRecord]:
    transformed_records: list[TransformedRecord] = [
        {
            "record_id": record["id"],
            "category": record["category"].lower().replace(" ", "-"),
            "amount": round(record["amount"], 2),
            "status": "ready",
        }
        for record in records
    ]

    logger.info(
        "File transformed",
        extra={
            "normalized_count": len(transformed_records),
            "total_amount": round(sum(item["amount"] for item in transformed_records), 2),
        },
    )
    return transformed_records


def _build_persistence_record(
    blob_name: str,
    source_format: str,
    transformed_records: list[TransformedRecord],
) -> dict[str, object]:
    total_amount = round(sum(item["amount"] for item in transformed_records), 2)
    return {
        "id": str(uuid.uuid4()),
        "blob_name": blob_name,
        "source_format": source_format,
        "record_count": len(transformed_records),
        "total_amount": total_amount,
        "processed_at": datetime.now(timezone.utc).isoformat(),
        "items": transformed_records,
    }
