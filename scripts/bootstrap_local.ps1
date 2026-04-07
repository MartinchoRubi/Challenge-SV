$ErrorActionPreference = "Stop"

if (-not (Test-Path ".venv")) {
    if (Get-Command python -ErrorAction SilentlyContinue) {
        python -m venv .venv
    } elseif (Get-Command py -ErrorAction SilentlyContinue) {
        try {
            py -3.11 -m venv .venv
        } catch {
            py -3 -m venv .venv
        }
    } else {
        throw "No se encontro Python. Instala Python 3.11+ y vuelve a ejecutar."
    }
}

if (-not (Test-Path ".venv\\Scripts\\python.exe")) {
    throw "No se pudo crear el virtual environment en .venv"
}

& ".\.venv\Scripts\python.exe" -m pip install --upgrade pip
& ".\.venv\Scripts\python.exe" -m pip install -r requirements.txt

Write-Host "Entorno local listo."

