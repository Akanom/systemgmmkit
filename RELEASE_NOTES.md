# systemgmmkit v0.5.0

This release adds native Windmeijer-corrected two-step covariance support for dynamic-panel GMM and documents benchmark-specific Stata `xtabond2` parity for native System GMM.

## Highlights

- Native System GMM now supports Windmeijer-corrected two-step standard errors.
- The certified benchmark matches Stata `xtabond2` `e(V)` standard errors within a maximum relative difference of approximately `0.000579`.
- Native System GMM benchmark documentation now covers coefficients, raw residual moments (`Z'u`), group-scaled two-step weighting matrix (`A2 / n_groups`), Hansen J, and Windmeijer-corrected standard errors.
- The old uncorrected two-step clustered covariance benchmark path is preserved through `SYSTEMGMMKIT_NATIVE_WINDMEIJER=0`.
- Repository hygiene was improved by removing tracked parity/debug Python snapshots and restoring a clean Ruff/pytest/CI gate.

## Validation status

The Windmeijer parity result is benchmark-specific. It should not be presented as universal Stata identity across all possible datasets, lag windows, missing-data patterns, instrument classifications, covariance assumptions, or finite-sample settings.

## Installation

    python -m pip install systemgmmkit==0.5.0

## Recommended extras

    python -m pip install "systemgmmkit[all]==0.5.0"
