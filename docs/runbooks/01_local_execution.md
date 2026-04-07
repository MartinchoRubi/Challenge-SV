# Ejecución local

## Objetivo

Correr el flujo completo sin depender de AWS para validar que el repo está sano.

## Paso 1

```bash
cp .env.example .env
bash scripts/bootstrap_local.sh
```

En Windows (PowerShell):

```powershell
Copy-Item .env.example .env
powershell -ExecutionPolicy Bypass -File scripts/bootstrap_local.ps1
```

## Paso 2

```bash
bash scripts/local_run.sh
```

En Windows (PowerShell):

```powershell
powershell -ExecutionPolicy Bypass -File scripts/local_run.ps1
```

## Backfill historico (opcional)

Si ya tenemos varios Bronze y queremos generar Silver/Gold por cada corrida:

```bash
bash scripts/backfill.sh
```

En Windows (PowerShell):

```powershell
powershell -ExecutionPolicy Bypass -File scripts/backfill.ps1
```

## Qué ejecuta ese script

1. Ingesta datos desde Open-Meteo.
2. Escribe Bronze en `local_data/bronze/`.
3. Genera Silver en `local_data/silver/`.
4. Genera Gold en `local_data/gold/`.
5. Ejecuta enriquecimiento en `local_data/enriched/`.

## Validación mínima

```bash
ls -R local_data
```

Deberías ver archivos `.jsonl` y `.parquet`.

## API local

```bash
source .venv/bin/activate
uvicorn src.serving.app:app --reload --port 8080
```

En Windows (PowerShell):

```powershell
.\.venv\Scripts\Activate.ps1
uvicorn src.serving.app:app --reload --port 8080
```

Probar en otra terminal:

```bash
curl http://127.0.0.1:8080/health
curl http://127.0.0.1:8080/latest
```

En PowerShell:

```powershell
Invoke-RestMethod http://127.0.0.1:8080/health
Invoke-RestMethod http://127.0.0.1:8080/latest
```

## LLM (requerido)

Que hace en concreto el LLM:
- Lee cada fila curada de Silver (ciudad, temperatura, humedad, viento).
- Genera `operational_summary` (resumen operativo corto en ingles, en lenguaje natural).
- Guarda el resultado en `local_data/enriched/weather_curated_enriched*.parquet`.

Configuración recomendada (OpenRouter):
1. Crear API key en OpenRouter.
2. Guardarla en `.env`:

```bash
OPENROUTER_API_KEY=
OPENROUTER_MODEL=google/gemma-3-4b-it:free
```

3. Volver a correr enrichment:

```bash
python -m src.enrichment.gemini_enricher
```
