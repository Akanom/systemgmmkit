$ErrorActionPreference = "Stop"

python .\scripts\parity\build_xtabond2_system_gmm_decomposition_controls_do.py
python .\scripts\parity\run_native_system_gmm_decomposition_controls.py
python .\scripts\parity\compare_xtabond2_system_gmm_decomposition_controls.py

Write-Host ""
Write-Host "Generated decomposition controls parity package:"
Write-Host "artifacts\parity\xtabond2\specs\system_gmm_decomposition_controls"
Write-Host ""
Write-Host "To complete Stata-side artifacts, run in Stata from the repo root:"
Write-Host "do artifacts/parity/xtabond2/specs/system_gmm_decomposition_controls/system_gmm_decomposition_controls.do"
Write-Host ""
Write-Host "Then rerun:"
Write-Host "python .\scripts\parity\compare_xtabond2_system_gmm_decomposition_controls.py"
