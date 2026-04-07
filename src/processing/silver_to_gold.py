from __future__ import annotations

import pandas as pd

from src.common.config import GOLD_DIR, SILVER_DIR
from src.common.io import write_parquet
from src.common.logger import get_logger

LOGGER = get_logger(__name__)
INPUT_FILE = SILVER_DIR / "weather_curated.parquet"
OUTPUT_FILE = GOLD_DIR / "weather_operational_mart.parquet"


def run(input_file: str | None = None) -> str:
    source_file = input_file or str(INPUT_FILE)
    df = pd.read_parquet(source_file)
    run_id = str(df["run_id"].iloc[0]) if "run_id" in df.columns else str(df["ingestion_ts_utc"].max())
    latest_ts = df["ingestion_ts_utc"].max()
    latest_df = df[df["ingestion_ts_utc"] == latest_ts].copy()

    gold = pd.DataFrame([
        {
            "run_ts_utc": latest_ts,
            "city_count": int(latest_df["city"].nunique()),
            "avg_temperature_2m": round(float(latest_df["temperature_2m"].mean()), 2),
            "avg_relative_humidity_2m": round(float(latest_df["relative_humidity_2m"].mean()), 2),
            "avg_wind_speed_10m": round(float(latest_df["wind_speed_10m"].mean()), 2),
            "run_id": run_id,
            "run_hour_utc": pd.to_datetime(latest_ts, utc=True).strftime("%H:%M:%S"),
        }
    ])
    historical_output = GOLD_DIR / f"weather_operational_mart_{run_id}.parquet"
    write_parquet(gold, historical_output)
    write_parquet(gold, OUTPUT_FILE)
    LOGGER.info("Gold files created at %s and %s", historical_output, OUTPUT_FILE)
    return str(historical_output)


if __name__ == "__main__":
    run()
