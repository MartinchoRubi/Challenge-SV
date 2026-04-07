# ADR 001 - Decisiones principales

## S3 como Lakehouse base
Se eligió S3 por costo, durabilidad, particionamiento simple y buena integración con Glue y Athena.

## Medallion architecture
Se eligió Bronze/Silver/Gold para separar crudo, curado y consumo final. Esto simplifica trazabilidad y reproceso.

## Step Functions para orquestación
Se eligió Step Functions para tener flujos visibles, auditables y desacoplados del código Python.

## Glue para batch
Se eligió Glue porque resuelve transformaciones serverless y se integra natural con el catálogo del Lakehouse.

## Event-driven complementario
Se deja EventBridge/SQS para desacoplar propagación y consumo near real-time.

## Contenedor para enriquecimiento
Se eligió contenerizar el enriquecedor porque el uso de SDKs de LLM, dependencias o librerías de NLP suele crecer más que una Lambda simple.
