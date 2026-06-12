$ErrorActionPreference = "Stop"

$env:PYTHONPATH = "$PWD\src"

Write-Host "Running conformance suite..."
python -m pytest tests/conformance -q

Write-Host "Running static estimator certification..."
python -m pytest tests/parity/static -q

Write-Host "Running Difference GMM expanded certification..."
python -m pytest tests/parity/gmm/test_difference_gmm_expanded_certification.py -q

Write-Host "Running System GMM certification..."
python -m pytest tests/parity/gmm/test_system_gmm_certification.py -q

Write-Host "Building aggregate certification report..."
python .\scripts\parity\build_certification_report.py

Write-Host ""
Write-Host "Certification complete:"
Write-Host "artifacts\parity\panel_econometrics_certification_report.md"
