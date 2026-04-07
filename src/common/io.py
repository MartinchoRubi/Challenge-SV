from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

import pandas as pd


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_jsonl(records: Iterable[dict], output_file: Path) -> None:
    ensure_dir(output_file.parent)
    with output_file.open("w", encoding="utf-8") as fh:
        for record in records:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def read_jsonl(input_file: Path) -> list[dict]:
    rows: list[dict] = []
    with input_file.open("r", encoding="utf-8") as fh:
        for line in fh:
            rows.append(json.loads(line))
    return rows


def write_parquet(df: pd.DataFrame, output_file: Path) -> None:
    ensure_dir(output_file.parent)
    df.to_parquet(output_file, index=False)
