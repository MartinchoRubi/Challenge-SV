from __future__ import annotations

import json
from datetime import datetime, timezone

import boto3

from src.common.config import settings
from src.ingestion.public_api_ingestor import fetch_weather


def handler(event, context):  # noqa: ANN001
    raw_bucket = (event or {}).get("raw_bucket") or (event or {}).get("RAW_BUCKET")
    raw_prefix = (event or {}).get("raw_prefix") or "bronze/"

    if not raw_bucket:
        raise ValueError("Missing raw_bucket. Provide {'raw_bucket': '<bucket>'} in the event.")

    records = [fetch_weather(city) for city in settings.target_cities]
    ndjson = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records)

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    key = f"{raw_prefix.rstrip('/')}/weather_ingestion_{ts}.jsonl"

    boto3.client("s3").put_object(
        Bucket=raw_bucket,
        Key=key,
        Body=ndjson.encode("utf-8"),
        ContentType="application/x-ndjson; charset=utf-8",
    )

    return {"statusCode": 200, "raw_bucket": raw_bucket, "raw_key": key, "record_count": len(records)}

