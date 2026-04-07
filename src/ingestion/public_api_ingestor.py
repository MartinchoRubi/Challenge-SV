from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path

import requests

from src.common.config import BRONZE_DIR, settings
from src.common.io import write_jsonl
from src.common.logger import get_logger

LOGGER = get_logger(__name__)
TIMEOUT_SECONDS = 20
MAX_RETRIES = 3


def _request_with_retry(url: str, params: dict) -> dict:
    last_error: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(url, params=params, timeout=TIMEOUT_SECONDS)
            response.raise_for_status()
            return response.json()
        except Exception as exc:  # pragma: no cover - network branch
            last_error = exc
            LOGGER.warning("Request failed. attempt=%s url=%s error=%s", attempt, url, exc)
            time.sleep(attempt)
    raise RuntimeError(f"Request failed after retries: {url}") from last_error


def get_coordinates(city: str) -> tuple[float, float]:
    payload = _request_with_retry(
        f"{settings.geocoding_api_base_url}/search",
        {"name": city, "count": 1, "language": "en", "format": "json"},
    )
    results = payload.get("results") or []
    if not results:
        raise ValueError(f"No coordinates found for city={city}")
    return float(results[0]["latitude"]), float(results[0]["longitude"])


def fetch_weather(city: str) -> dict:
    latitude, longitude = get_coordinates(city)
    payload = _request_with_retry(
        f"{settings.public_api_base_url}/forecast",
        {
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code",
            "timezone": "auto",
        },
    )
    current = payload.get("current", {})
    return {
        "ingestion_ts_utc": datetime.now(timezone.utc).isoformat(),
        "city": city,
        "latitude": latitude,
        "longitude": longitude,
        "temperature_2m": current.get("temperature_2m"),
        "relative_humidity_2m": current.get("relative_humidity_2m"),
        "wind_speed_10m": current.get("wind_speed_10m"),
        "weather_code": current.get("weather_code"),
        "source": "open-meteo",
    }


def run() -> Path:
    records = [fetch_weather(city) for city in settings.target_cities]
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_file = BRONZE_DIR / f"weather_ingestion_{timestamp}.jsonl"
    write_jsonl(records, output_file)
    LOGGER.info("Bronze file created at %s", output_file)
    return output_file


if __name__ == "__main__":
    run()
