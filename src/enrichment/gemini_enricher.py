from __future__ import annotations

import time

import pandas as pd
import requests

from src.common.config import ENRICHED_DIR, SILVER_DIR, settings
from src.common.io import write_parquet
from src.common.logger import get_logger

LOGGER = get_logger(__name__)
INPUT_FILE = SILVER_DIR / "weather_curated.parquet"
OUTPUT_FILE = ENRICHED_DIR / "weather_curated_enriched.parquet"
MAX_LLM_RETRIES = 3


def gemini_summary(prompt: str) -> str:
    api_key = settings.openrouter_api_key or settings.gemini_api_key
    if not api_key:
        raise ValueError("Missing OPENROUTER_API_KEY or GEMINI_API_KEY.")
    payload = {
        "model": settings.openrouter_model,
        "messages": [{"role": "user", "content": prompt[:600]}],
        "temperature": 0.2,
        "max_tokens": 80,
    }
    last_error: Exception | None = None
    for attempt in range(1, MAX_LLM_RETRIES + 1):
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            usage = data.get("usage") or {}
            if usage:
                LOGGER.info(
                    "LLM usage model=%s prompt_tokens=%s completion_tokens=%s total_tokens=%s",
                    settings.openrouter_model,
                    usage.get("prompt_tokens"),
                    usage.get("completion_tokens"),
                    usage.get("total_tokens"),
                )
            return data["choices"][0]["message"]["content"].strip()
        except Exception as exc:
            last_error = exc
            LOGGER.warning("LLM call failed. attempt=%s/%s error=%s", attempt, MAX_LLM_RETRIES, exc)
            time.sleep(attempt)
    raise RuntimeError("LLM enrichment failed after retries") from last_error


def run(input_file: str | None = None) -> str:
    if not (settings.openrouter_api_key or settings.gemini_api_key):
        raise ValueError("Missing OPENROUTER_API_KEY or GEMINI_API_KEY. LLM is required for enrichment.")

    source_file = input_file or str(INPUT_FILE)
    df = pd.read_parquet(source_file)
    summaries: list[str] = []

    for _, row in df.iterrows():
        prompt = (
            "Write one short operational weather summary in English for a data product. "
            "Be concrete, no marketing tone. "
            f"City={row['city']}, temperature={row['temperature_2m']}, "
            f"humidity={row['relative_humidity_2m']}, wind={row['wind_speed_10m']}."
        )
        summaries.append(gemini_summary(prompt))

    df["operational_summary"] = summaries
    run_id = str(df["run_id"].iloc[0]) if "run_id" in df.columns else "no_run_id"
    historical_output = ENRICHED_DIR / f"weather_curated_enriched_{run_id}.parquet"
    write_parquet(df, historical_output)
    write_parquet(df, OUTPUT_FILE)
    LOGGER.info("Enriched files created at %s and %s", historical_output, OUTPUT_FILE)
    return str(historical_output)


if __name__ == "__main__":
    run()
