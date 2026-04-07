# Despliegue en AWS

## Qué despliega este repo

El template SAM despliega una demo funcional en AWS:
- bucket raw (Bronze);
- bucket curated (Silver/Gold);
- Lambda `pipeline` (ingesta + curado + gold en S3);
- HTTP API Gateway + Lambda `operational-serving` (`/health` y `/latest`);
- scheduler (EventBridge Scheduler) para correr la pipeline periódicamente;
- IAM mínimo para S3.

Nota: Glue/Step Functions quedan como **arquitectura objetivo** (ver `docs/architecture/*` y ADR). Para el challenge, esta demo prioriza reproducibilidad y costo/tiempo de ejecución bajos.

## Antes de desplegar

Tener configurado:
- AWS CLI;
- credenciales activas;
- región correcta;
- permisos para CloudFormation, IAM, S3, Lambda, API Gateway y EventBridge Scheduler.
- AWS SAM CLI (comando `sam`).

## Comando

```bash
bash scripts/deploy.sh
```

En Windows (PowerShell):

```powershell
powershell -ExecutionPolicy Bypass -File scripts/deploy.ps1
```

## Opcion modular por stacks (sin romper la actual)

Para separar por dominios operativos, tambien hay una variante modular:
- `templates/sam/modular_core_data.yaml` (storage base: raw/curated);
- `templates/sam/modular_pipeline.yaml` (ingesta y procesamiento);
- `templates/sam/modular_serving.yaml` (API de consumo).

Comandos:

```bash
bash scripts/deploy_modular.sh
```

```powershell
powershell -ExecutionPolicy Bypass -File scripts/deploy_modular.ps1
```

## adaptar

En `.env`:
- `AWS_REGION`
- `STACK_NAME`
- `RAW_BUCKET`
- `CURATED_BUCKET`
- `ARTIFACTS_BUCKET` (bucket para empaquetar el build de SAM)
- `GEMINI_API_KEY` (requerida para enrichment)

## Después del deploy

1. Confirmar que el stack terminó en `CREATE_COMPLETE`.
2. Revisar outputs del stack.
3. Esperar una ejecución del scheduler (o invocar manualmente la Lambda `pipeline`) para que se escriba `gold/weather_operational_mart.json` en `CURATED_BUCKET`.
4. Probar el endpoint `GET /latest`.
5. Verificar ejecucion correcta de Gemini en la Lambda `pipeline` (si falta key, falla con error explicito).


