# System GMM parity matrix

## Purpose

This document summarizes the current native `systemgmmkit` System GMM parity status against Stata `xtabond2`.

The certification claims are benchmark-specific. They should not be interpreted as universal Stata identity across all datasets, lag windows, instrument classifications, transformations, missing-data patterns, covariance assumptions, or finite-sample corrections.

## Certification scope

A System GMM specification is treated as certified when committed artifacts and pytest guards verify:

- matching parameter count;
- matching observation count;
- matching instrument count;
- coefficient parity against `xtabond2`;
- Hansen J / Hansen p-value parity against `xtabond2`;
- two-step Windmeijer-corrected standard-error parity against `xtabond2`.

Arellano-Bond AR(1)/AR(2) diagnostic parity is tracked separately and is **not yet certified**.

## Certified specifications

| Spec ID | Model type | Coefficients | Windmeijer SEs | Hansen p-value | N / groups | Instruments | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `difference_gmm_baseline_controls` | Difference GMM | Certified | Separate path | Existing guard | Certified | Certified | Certified benchmark |
| `system_gmm_baseline_controls` | System GMM | Certified | Certified | Certified | Certified | Certified | Certified benchmark |
| `system_gmm_no_controls` | System GMM | Certified | Certified | Certified | Certified | Certified | Certified benchmark |
| `system_gmm_three_way_controls` | System GMM | Certified | Certified | Certified | Certified | Certified | Certified benchmark |
| `system_gmm_decomposition_controls` | System GMM | Certified | Certified | Certified | Certified | Certified | Certified benchmark |

## Certified artifact locations

| Spec ID | Artifact path |
| --- | --- |
| `system_gmm_baseline_controls` | `artifacts/parity/xtabond2/specs/system_gmm_baseline_controls/` |
| `system_gmm_no_controls` | `artifacts/parity/xtabond2/specs/system_gmm_no_controls/` |
| `system_gmm_three_way_controls` | `artifacts/parity/xtabond2/specs/system_gmm_three_way_controls/` |
| `system_gmm_decomposition_controls` | `artifacts/parity/xtabond2/specs/system_gmm_decomposition_controls/` |

## Tolerance policy

| Object | Certification tolerance |
| --- | --- |
| Coefficients | `max_abs_diff <= 1e-6` |
| Windmeijer standard errors | `max_rel_diff <= 0.001` |
| Hansen p-value | `max_abs_diff <= 1e-6` |
| Instrument count | Exact match |
| Observation count | Exact match |
| Group count | Exact match where reported |

## Current limitations

- AR(1)/AR(2) diagnostic parity is not yet certified.
- Certification currently targets the committed balanced-panel parity harnesses.
- Additional unbalanced-panel, missing-data, alternative-lag-window, and alternative-instrument-layout tests remain future work.
- Claims remain benchmark-specific and conservative.
