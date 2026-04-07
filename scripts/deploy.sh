#!/usr/bin/env bash
set -euo pipefail

if [ -f .env ]; then
  set -a
  source .env
  set +a
fi

: "${AWS_REGION:?Falta AWS_REGION}"
: "${STACK_NAME:?Falta STACK_NAME}"
: "${RAW_BUCKET:?Falta RAW_BUCKET}"
: "${CURATED_BUCKET:?Falta CURATED_BUCKET}"
: "${ARTIFACTS_BUCKET:?Falta ARTIFACTS_BUCKET (bucket para empaquetar artefactos SAM)}"
: "${GEMINI_API_KEY:?Falta GEMINI_API_KEY}"

if ! command -v sam >/dev/null 2>&1; then
  echo "Falta AWS SAM CLI (comando 'sam'). Instalalo para poder empaquetar y desplegar Lambdas."
  echo "Doc: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html"
  exit 1
fi

if ! aws s3api head-bucket --bucket "$ARTIFACTS_BUCKET" 2>/dev/null; then
  echo "Creando bucket de artefactos: $ARTIFACTS_BUCKET"
  if [ "$AWS_REGION" = "us-east-1" ]; then
    aws s3api create-bucket --bucket "$ARTIFACTS_BUCKET" --region "$AWS_REGION"
  else
    aws s3api create-bucket --bucket "$ARTIFACTS_BUCKET" --region "$AWS_REGION" \
      --create-bucket-configuration "LocationConstraint=$AWS_REGION"
  fi
fi

sam build --template-file templates/sam/template.yaml

sam deploy \
  --template-file .aws-sam/build/template.yaml \
  --stack-name "$STACK_NAME" \
  --region "$AWS_REGION" \
  --capabilities CAPABILITY_NAMED_IAM \
  --s3-bucket "$ARTIFACTS_BUCKET" \
  --parameter-overrides RawBucketName="$RAW_BUCKET" CuratedBucketName="$CURATED_BUCKET" GeminiApiKey="$GEMINI_API_KEY" \
  --no-fail-on-empty-changeset

echo "Deploy completo. Revisá los Outputs del stack (endpoint HTTP API y buckets)."
