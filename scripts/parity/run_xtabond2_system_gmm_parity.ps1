$ErrorActionPreference = "Stop"

$env:PYTHONPATH = "$PWD\src"

python .\scripts\parity\build_xtabond2_system_gmm_do.py
python .\scripts\parity\run_native_system_gmm_benchmark.py
python .\scripts\parity\compare_xtabond2_native_system_gmm.py

Write-Host ""
Write-Host "Generated xtabond2 parity package:"
Write-Host "artifacts\parity\xtabond2"
Write-Host ""
Write-Host "Next manual step:"
Write-Host "Open Stata and run:"
Write-Host "do artifacts/parity/xtabond2/system_gmm_xtabond2_parity.do"
Write-Host ""
Write-Host "Then rerun:"
Write-Host ".\scripts\parity\run_xtabond2_system_gmm_parity.ps1"
