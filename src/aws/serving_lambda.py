from __future__ import annotations

import json
import os

import boto3


def _response(status_code: int, body: dict) -> dict:
    return {
        "statusCode": status_code,
        "headers": {"content-type": "application/json"},
        "body": json.dumps(body),
    }


def handler(event, context):  # noqa: ANN001
    path = ((event or {}).get("rawPath") or (event or {}).get("path") or "").rstrip("/") or "/"
    if path == "/health":
        return _response(200, {"status": "ok"})

    # Expected env vars from IaC
    curated_bucket = os.getenv("CURATED_BUCKET", "")
    curated_key = os.getenv("GOLD_KEY", "gold/weather_operational_mart.json")

    if not curated_bucket:
        return _response(500, {"error": "Missing CURATED_BUCKET env var"})

    s3 = boto3.client("s3")
    try:
        obj = s3.get_object(Bucket=curated_bucket, Key=curated_key)
        payload = obj["Body"].read().decode("utf-8")
        return _response(200, json.loads(payload))
    except s3.exceptions.NoSuchKey:
        return _response(404, {"error": "Gold dataset not found", "key": curated_key})
    except Exception as exc:  # pragma: no cover
        return _response(500, {"error": str(exc)})

