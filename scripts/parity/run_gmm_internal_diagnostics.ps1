$ErrorActionPreference = "Stop"

$env:PYTHONPATH = "$PWD\src"

python .\scripts\parity\inspect_native_gmm_internals.py
python .\scripts\parity\compare_gmm_internal_diagnostics.py

Write-Host ""
Write-Host "Native internal diagnostics written."
Write-Host "Manual Stata step:"
Write-Host "Run in Stata:"
Write-Host "do artifacts/parity/xtabond2/export_xtabond2_internals.do"
Write-Host ""
Write-Host "Then rerun:"
Write-Host ".\scripts\parity\run_gmm_internal_diagnostics.ps1"
