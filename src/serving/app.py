from __future__ import annotations

from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException

from src.common.config import GOLD_DIR

app = FastAPI(title="SPV Operational Data API", version="1.0.0")
GOLD_FILE = GOLD_DIR / "weather_operational_mart.parquet"


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/latest")
def latest() -> dict:
    if not GOLD_FILE.exists():
        raise HTTPException(status_code=404, detail="Gold dataset not found. Run the pipeline first.")
    df = pd.read_parquet(GOLD_FILE)
    row = df.iloc[-1].to_dict()
    row["run_ts_utc"] = str(row["run_ts_utc"])
    return row
