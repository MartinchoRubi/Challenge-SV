from __future__ import annotations

import json
import os
from datetime import datetime, timezone

import boto3
import requests

from src.ingestion.public_api_ingestor import fetch_weather


def gemini_summary(api_key: str, city: str, temperature: float | None, humidity: float | None, wind: float | None) -> str:
    model = os.getenv("OPENROUTER_MODEL", "google/gemma-3-4b-it:free")
    prompt = (
        "Write one short operational weather summary in English for a data product. "
        "Be concrete, no marketing tone. "
        f"City={city}, temperature={temperature}, humidity={humidity}, wind={wind}."
    )
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "max_tokens": 80,
        },
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    return (payload["choices"][0]["message"]["content"] or "").strip()


def handler(event, context):  # noqa: ANN001
    """
    Minimal "cloud pipeline" for the challenge:
    - fetch records from Open-Meteo
    - write bronze NDJSON
    - write curated silver NDJSON
    - write gold metrics JSON (for simple serving)

    This keeps the AWS deploy functional without forcing Glue/StepFunctions wiring for the demo.
    """
    raw_bucket = os.getenv("RAW_BUCKET", "")
    curated_bucket = os.getenv("CURATED_BUCKET", "")
    llm_api_key = os.getenv("OPENROUTER_API_KEY", "") or os.getenv("GEMINI_API_KEY", "")
    target_cities = [c.strip() for c in os.getenv("TARGET_CITIES", "Buenos Aires,Cordoba,Rosario").split(",") if c.strip()]

    if not raw_bucket or not curated_bucket:
        raise ValueError("Missing RAW_BUCKET or CURATED_BUCKET env vars")
    if not llm_api_key:
        raise ValueError("Missing OPENROUTER_API_KEY or GEMINI_API_KEY env var")

    s3 = boto3.client("s3")

    records = [fetch_weather(city) for city in target_cities]
    ndjson = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records)

    ts = datetime.now(timezone.utc)
    ts_compact = ts.strftime("%Y%m%dT%H%M%SZ")
    bronze_key = f"bronze/weather_ingestion_{ts_compact}.jsonl"
    s3.put_object(
        Bucket=raw_bucket,
        Key=bronze_key,
        Body=ndjson.encode("utf-8"),
        ContentType="application/x-ndjson; charset=utf-8",
    )

    curated = []
    for r in records:
        summary = gemini_summary(
            llm_api_key,
            r.get("city", ""),
            r.get("temperature_2m"),
            r.get("relative_humidity_2m"),
            r.get("wind_speed_10m"),
        )
        curated.append(
            {
                **r,
                "ingestion_date": (r.get("ingestion_ts_utc") or "")[:10],
                "operational_summary": summary,
            }
        )
    silver_key = "silver/weather_curated.jsonl"
    curated_ndjson = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in curated)
    s3.put_object(
        Bucket=curated_bucket,
        Key=silver_key,
        Body=curated_ndjson.encode("utf-8"),
        ContentType="application/x-ndjson; charset=utf-8",
    )

    latest_ts = max(r["ingestion_ts_utc"] for r in curated)
    latest_records = [r for r in curated if r["ingestion_ts_utc"] == latest_ts]

    def _mean(values: list[float | None]) -> float:
        nums = [float(v) for v in values if v is not None]
        return sum(nums) / len(nums) if nums else 0.0

    gold = {
        "run_ts_utc": latest_ts,
        "city_count": int(len({r["city"] for r in latest_records})),
        "avg_temperature_2m": round(_mean([r.get("temperature_2m") for r in latest_records]), 2),
        "avg_relative_humidity_2m": round(_mean([r.get("relative_humidity_2m") for r in latest_records]), 2),
        "avg_wind_speed_10m": round(_mean([r.get("wind_speed_10m") for r in latest_records]), 2),
    }
    gold_key = "gold/weather_operational_mart.json"
    s3.put_object(
        Bucket=curated_bucket,
        Key=gold_key,
        Body=json.dumps(gold).encode("utf-8"),
        ContentType="application/json; charset=utf-8",
    )

    return {
        "statusCode": 200,
        "raw_bucket": raw_bucket,
        "curated_bucket": curated_bucket,
        "bronze_key": bronze_key,
        "silver_key": silver_key,
        "gold_key": gold_key,
        "enriched_rows": len(curated),
        "record_count": len(records),
    }

