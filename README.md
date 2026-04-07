# SPV DataOps Challenge

Solucion de datos operativos con arquitectura Lakehouse (Bronze/Silver/Gold), enriquecimiento con LLM via OpenRouter (Gemma/Gemini) y despliegue en AWS con IaC.

## Arquitectura

Diagrama:
- `docs/architecture/architecture.svg`
- `docs/architecture/architecture.drawio`

Servicios AWS propuestos:
- EventBridge Scheduler (ingesta periodica)
- Lambda pipeline (ingesta + transformaciones)
- S3 (Bronze, Silver, Gold)
- API Gateway + Lambda serving (`/health`, `/latest`)
- CloudWatch (logs/metricas)

Arquitectura objetivo de escalado: SQS + Step Functions + Glue + ECS Fargate.

## Decisiones tecnicas

- API publica: Open-Meteo (estable, sin bloqueo por credenciales para la demo).
- Lakehouse Medallion: separa crudo, curado y consumo.
- Formato: Parquet en Silver/Gold local para optimizar lectura analitica.
- Particionamiento sugerido: `ingestion_date` (y opcional `city`) para reducir scan en consultas operativas por ventana temporal.
- Enriquecimiento: LLM obligatorio para el campo `operational_summary` (OpenRouter recomendado).
- IaC: template SAM en `templates/sam/template.yaml`.
- Componente contenerizado: serving (`Dockerfile` + FastAPI).

## Flujo punta a punta

1. Ingesta consulta Open-Meteo y escribe NDJSON en Bronze.
2. Bronze -> Silver (normalizacion y tipado).
3. Silver -> Gold (metricas operativas agregadas).
4. Enrichment usa OpenRouter (Gemma/Gemini) y agrega `operational_summary`.
5. Serving expone el ultimo snapshot operacional.

## Ejecutar local

Linux/macOS:
```bash
cp .env.example .env
bash scripts/bootstrap_local.sh
bash scripts/local_run.sh
bash scripts/backfill.sh
bash scripts/run_tests.sh
```

Windows (PowerShell):
```powershell
Copy-Item .env.example .env
powershell -ExecutionPolicy Bypass -File scripts/bootstrap_local.ps1
powershell -ExecutionPolicy Bypass -File scripts/local_run.ps1
powershell -ExecutionPolicy Bypass -File scripts/backfill.ps1
powershell -ExecutionPolicy Bypass -File scripts/run_tests.ps1
```

API local:
- `uvicorn src.serving.app:app --reload --port 8080`
- `http://127.0.0.1:8080/health`
- `http://127.0.0.1:8080/latest`

## Despliegue AWS

- Completar `.env` (`AWS_REGION`, `STACK_NAME`, `RAW_BUCKET`, `CURATED_BUCKET`, `ARTIFACTS_BUCKET`, `OPENROUTER_API_KEY`).
- Ejecutar `scripts/deploy.sh` (o `scripts/deploy.ps1` en Windows).
- Revisar outputs del stack y probar endpoint.
- Opcion modular sin romper la actual: `scripts/deploy_modular.sh` o `scripts/deploy_modular.ps1`
  (stacks separados: core-data, pipeline, serving).

## LLM (obligatorio)

Este repo requiere `OPENROUTER_API_KEY` (o `GEMINI_API_KEY`) para ejecutar `src/enrichment/gemini_enricher.py`.
Sin key, enrichment falla con error explicito.
Modelo por defecto validado: `google/gemma-3-4b-it:free` via OpenRouter.

## Agentes de IA utilizados

- LLM de enriquecimiento: OpenRouter (modelo por defecto `google/gemma-3-4b-it:free`), usado para generar `operational_summary`.
- Asistencia de desarrollo: Cursor AI para acelerar iteraciones de codigo, runbooks y verificacion tecnica.

## Resultados esperados

- En `local_data/bronze`: archivos `weather_ingestion_*.jsonl` con datos crudos.
- En `local_data/silver`: `weather_curated*.parquet` con tipado/normalizacion.
- En `local_data/gold`: `weather_operational_mart*.parquet` con KPIs agregados.
- En `local_data/enriched`: `weather_curated_enriched*.parquet` con `operational_summary`.
- En AWS (demo): endpoint `/latest` devolviendo el snapshot operacional mas reciente.

## Evidencia versionada para evaluacion

Para mantener el repo liviano, `local_data/` se ignora en Git. Igual, se incluyen muestras reproducibles en:
- `docs/samples/bronze_sample.jsonl`
- `docs/samples/silver_sample.csv`
- `docs/samples/gold_sample.csv`
- `docs/samples/enriched_sample.csv`

Estas muestras permiten validar visualmente el resultado del pipeline y del enriquecimiento LLM sin depender de archivos runtime.

## Entregables en el repo

- `/docs`: diagramas y runbooks
- `/src`: componentes de ingestion, processing, enrichment, serving y handlers AWS
- `/scripts`: ejecucion local, tests y deploy
- `/templates`: IaC en SAM

