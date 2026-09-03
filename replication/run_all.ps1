$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

python .\replication\run_all.py --mode open @args
if ($LASTEXITCODE -ne 0) {
    throw "JSS replication failed with exit code $LASTEXITCODE."
}

Write-Host "JSS replication completed successfully."
