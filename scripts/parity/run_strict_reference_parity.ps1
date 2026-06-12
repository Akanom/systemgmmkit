$ErrorActionPreference = "Stop"

$env:PYTHONPATH = "$PWD\src"

python -m pytest tests/conformance tests/parity -q
python .\scripts\parity\build_strict_parity_report.py

Write-Host ""
Write-Host "Strict parity report written to:"
Write-Host "artifacts\parity\strict_parity_results.csv"
Write-Host "artifacts\parity\strict_parity_results.md"
