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
- Sargan diagnostic parity against `xtabond2`;
- signed Arellano-Bond AR(1)/AR(2) diagnostic parity against `xtabond2`;
- two-step Windmeijer-corrected standard-error parity against `xtabond2`.

The complete diagnostic claim applies to the maintained baseline only. Expanded
specifications retain their separately guarded coefficient and standard-error evidence;
they do not inherit baseline diagnostic certification.

## Certified specifications

| Spec ID | Model type | Coefficients | Windmeijer SEs | Hansen / Sargan | Signed AR(1) / AR(2) | Counts | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `difference_gmm_baseline_controls` | Difference GMM | Certified | Separate path | Existing guard | Separate path | Certified | Certified benchmark |
| `system_gmm_baseline_controls` | System GMM | Certified | Certified | Certified | Certified | Certified | Fully certified baseline |
| `system_gmm_no_controls` | System GMM | Certified | Certified | Not certified | Not certified | Sample and instrument counts guarded | Partial expanded-spec evidence |
| `system_gmm_three_way_controls` | System GMM | Certified | Certified | Not certified | Not certified | Sample count guarded; exact instrument-count parity excluded | Partial expanded-spec evidence |
| `system_gmm_decomposition_controls` | System GMM | Certified | Certified | Not certified | Not certified | Sample count guarded; exact instrument-count parity excluded | Partial expanded-spec evidence |

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
| Sargan p-value | Maintained baseline declared tolerance |
| Signed AR diagnostic statistics / p-values | Maintained baseline declared tolerances |
| Instrument count | Exact match |
| Observation count | Exact match |
| Group count | Exact match where reported |

## Current limitations

- Full System GMM diagnostic certification currently targets the maintained balanced-panel baseline.
- Expanded specifications certify only the quantities explicitly shown in the matrix.
- Additional unbalanced-panel, missing-data, alternative-lag-window, and alternative-instrument-layout tests remain future work.
- Claims remain benchmark-specific and conservative.
