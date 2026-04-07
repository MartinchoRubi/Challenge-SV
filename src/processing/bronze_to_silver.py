from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.common.config import BRONZE_DIR, SILVER_DIR
from src.common.io import read_jsonl, write_parquet
from src.common.logger import get_logger

LOGGER = get_logger(__name__)
OUTPUT_FILE = SILVER_DIR / "weather_curated.parquet"


def latest_bronze_file() -> Path:
    files = sorted(BRONZE_DIR.glob("*.jsonl"))
    if not files:
        raise FileNotFoundError("No bronze files found. Run ingestion first.")
    return files[-1]


def run_id_from_bronze(input_file: Path) -> str:
    # expected: weather_ingestion_YYYYMMDDTHHMMSSZ.jsonl
    stem = input_file.stem
    return stem.replace("weather_ingestion_", "")


def run(input_file: Path | None = None) -> Path:
    input_file = input_file or latest_bronze_file()
    run_id = run_id_from_bronze(input_file)
    rows = read_jsonl(input_file)
    df = pd.DataFrame(rows)
    df["ingestion_ts_utc"] = pd.to_datetime(df["ingestion_ts_utc"], utc=True)
    df["ingestion_date"] = df["ingestion_ts_utc"].dt.date.astype(str)
    df["ingestion_hour_utc"] = df["ingestion_ts_utc"].dt.strftime("%H:%M:%S")
    df["run_id"] = run_id
    df = df.sort_values(["city", "ingestion_ts_utc"]).reset_index(drop=True)
    historical_output = SILVER_DIR / f"weather_curated_{run_id}.parquet"
    write_parquet(df, historical_output)
    write_parquet(df, OUTPUT_FILE)
    LOGGER.info("Silver files created at %s and %s", historical_output, OUTPUT_FILE)
    return historical_output


if __name__ == "__main__":
    run()
