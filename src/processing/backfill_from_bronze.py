from __future__ import annotations

from pathlib import Path

from src.common.config import BRONZE_DIR
from src.common.logger import get_logger
from src.enrichment.gemini_enricher import run as enrich_run
from src.processing.bronze_to_silver import run as silver_run
from src.processing.silver_to_gold import run as gold_run

LOGGER = get_logger(__name__)


def run(include_enrichment: bool = False) -> None:
    bronze_files = sorted(BRONZE_DIR.glob("weather_ingestion_*.jsonl"))
    if not bronze_files:
        raise FileNotFoundError("No bronze files found.")

    for bronze_file in bronze_files:
        silver_file: Path = silver_run(bronze_file)
        gold_run(str(silver_file))
        if include_enrichment:
            enrich_run(str(silver_file))
        LOGGER.info("Backfill completed for %s", bronze_file.name)


if __name__ == "__main__":
    run()

