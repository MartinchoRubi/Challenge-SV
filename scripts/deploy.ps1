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
    throw "Falta AWS SAM CLI ('sam'). Instalar: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html"
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

sam build --template-file templates/sam/template.yaml

sam deploy `
  --template-file .aws-sam/build/template.yaml `
  --stack-name $env:STACK_NAME `
  --region $env:AWS_REGION `
  --capabilities CAPABILITY_NAMED_IAM `
  --s3-bucket $env:ARTIFACTS_BUCKET `
  --parameter-overrides "RawBucketName=$($env:RAW_BUCKET)" "CuratedBucketName=$($env:CURATED_BUCKET)" "GeminiApiKey=$($env:GEMINI_API_KEY)" `
  --no-fail-on-empty-changeset

Write-Host "Deploy completo."

