#!/usr/bin/env bash
set -euo pipefail

source .venv/bin/activate
python -m src.processing.backfill_from_bronze

echo "Backfill Bronze->Silver->Gold completado."

