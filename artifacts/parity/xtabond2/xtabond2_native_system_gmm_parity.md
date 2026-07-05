# xtabond2 vs Native System GMM Parity

## Status

Stata xtabond2 outputs detected. Comparison generated.

## Artifact Sources

- Native parameters: `artifacts/parity/xtabond2/specs/system_gmm_baseline_controls/windmeijer/native_params.csv`
- Native diagnostics: `artifacts/parity/xtabond2/specs/system_gmm_baseline_controls/windmeijer/native_diagnostics.csv`
- Stata parameters: `artifacts/parity/xtabond2/xtabond2_system_gmm_params.csv`
- Stata diagnostics: `artifacts/parity/xtabond2/xtabond2_system_gmm_diagnostics.csv`

## Generated Files

- `system_gmm_benchmark.csv`
- `system_gmm_xtabond2_parity.do`
- `xtabond2_native_system_gmm_coef_comparison.csv`
- `xtabond2_native_system_gmm_diagnostics_comparison.csv`
- `xtabond2_native_system_gmm_parity.md`

## Notes

This comparator prefers the isolated baseline Windmeijer native artifacts and falls back to the legacy top-level native artifacts only when required.
