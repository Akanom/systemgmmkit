$ErrorActionPreference = "Stop"

if (!(Test-Path "artifacts")) {
    New-Item -ItemType Directory -Path "artifacts" | Out-Null
}

python -m pytest tests/conformance -q `
    --tb=short `
    --disable-warnings `
    --junitxml=artifacts/conformance_junit.xml
