#!/usr/bin/env bash
set -euo pipefail

source .venv/bin/activate

python -m src.ingestion.public_api_ingestor
python -m src.processing.bronze_to_silver
python -m src.processing.silver_to_gold
python -m src.enrichment.gemini_enricher

echo "Proceso completo. Revisá local_data/."
