$ErrorActionPreference = "Stop"

if (Test-Path ".env") {
    Get-Content ".env" | ForEach-Object {
        if ($_ -match "^\s*#") { return }
        if ($_ -match "^\s*$") { return }
        $kv = $_ -split "=", 2
        if ($kv.Length -eq 2) {
            [System.Environment]::SetEnvironmentVariable($kv[0].Trim(), $kv[1].Trim(), "Process")
        }
    }
}

$required = @("AWS_REGION", "STACK_NAME", "RAW_BUCKET", "CURATED_BUCKET", "ARTIFACTS_BUCKET", "GEMINI_API_KEY")
foreach ($name in $required) {
    $value = (Get-Item -Path "Env:$name" -ErrorAction SilentlyContinue).Value
    if ([string]::IsNullOrWhiteSpace($value)) {
        throw "Falta variable $name en .env"
    }
}

if (-not (Get-Command sam -ErrorAction SilentlyContinue)) {
    throw "Falta AWS SAM CLI ('sam')."
}

try {
    aws s3api head-bucket --bucket $env:ARTIFACTS_BUCKET | Out-Null
} catch {
    Write-Host "Creando bucket de artefactos: $($env:ARTIFACTS_BUCKET)"
    if ($env:AWS_REGION -eq "us-east-1") {
        aws s3api create-bucket --bucket $env:ARTIFACTS_BUCKET --region $env:AWS_REGION | Out-Null
    } else {
        aws s3api create-bucket --bucket $env:ARTIFACTS_BUCKET --region $env:AWS_REGION --create-bucket-configuration "LocationConstraint=$($env:AWS_REGION)" | Out-Null
    }
}

sam build --template-file templates/sam/modular_core_data.yaml
sam deploy --template-file .aws-sam/build/modular_core_data.yaml --stack-name "$($env:STACK_NAME)-core-data" --region $env:AWS_REGION --capabilities CAPABILITY_NAMED_IAM --s3-bucket $env:ARTIFACTS_BUCKET --parameter-overrides "RawBucketName=$($env:RAW_BUCKET)" "CuratedBucketName=$($env:CURATED_BUCKET)" --no-fail-on-empty-changeset

sam build --template-file templates/sam/modular_pipeline.yaml
sam deploy --template-file .aws-sam/build/modular_pipeline.yaml --stack-name "$($env:STACK_NAME)-pipeline" --region $env:AWS_REGION --capabilities CAPABILITY_NAMED_IAM --s3-bucket $env:ARTIFACTS_BUCKET --parameter-overrides "RawBucketName=$($env:RAW_BUCKET)" "CuratedBucketName=$($env:CURATED_BUCKET)" "GeminiApiKey=$($env:GEMINI_API_KEY)" --no-fail-on-empty-changeset

sam build --template-file templates/sam/modular_serving.yaml
sam deploy --template-file .aws-sam/build/modular_serving.yaml --stack-name "$($env:STACK_NAME)-serving" --region $env:AWS_REGION --capabilities CAPABILITY_NAMED_IAM --s3-bucket $env:ARTIFACTS_BUCKET --parameter-overrides "CuratedBucketName=$($env:CURATED_BUCKET)" --no-fail-on-empty-changeset

Write-Host "Deploy modular completo."
