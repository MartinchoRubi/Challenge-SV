$ErrorActionPreference = "Stop"

& ".\.venv\Scripts\python.exe" -m src.processing.backfill_from_bronze
if ($LASTEXITCODE -ne 0) { throw "Backfill fallo." }

Write-Host "Backfill Bronze->Silver->Gold completado."

