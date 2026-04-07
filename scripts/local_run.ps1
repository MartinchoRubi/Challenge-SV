$ErrorActionPreference = "Stop"

function Run-Step {
    param([string]$Module)
    & ".\.venv\Scripts\python.exe" -m $Module
    if ($LASTEXITCODE -ne 0) {
        throw "Fallo el paso: $Module"
    }
}

Run-Step "src.ingestion.public_api_ingestor"
Run-Step "src.processing.bronze_to_silver"
Run-Step "src.processing.silver_to_gold"
Run-Step "src.enrichment.gemini_enricher"

Write-Host "Proceso completo. Revisa local_data/."

