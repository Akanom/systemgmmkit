# System GMM parity matrix

## Purpose

This document defines the next validation milestone for `systemgmmkit` native System GMM.

Version `0.5.0` certified native Windmeijer-corrected two-step standard errors against Stata `xtabond2` `e(V)` for the current collapsed two-step System GMM benchmark. The next milestone broadens coverage across multiple specifications while keeping claims benchmark-specific and auditable.

## Core principle

Parity is specification-specific.

A passing result for one System GMM benchmark does not imply universal Stata identity across all datasets, lag structures, instrument classifications, missing-data patterns, transformations, covariance assumptions, or finite-sample corrections.

## Candidate specifications

| Spec ID | Model type | Main purpose | Priority | Release blocking |
| --- | --- | --- | --- | --- |
| `system_gmm_baseline_controls` | System GMM | Preserve and extend current certified benchmark. | P0 | Yes |
| `system_gmm_no_controls` | System GMM | Validate minimal model construction and covariance behavior. | P0 | Yes |
| `system_gmm_three_way_controls` | System GMM | Validate interaction-heavy designs. | P1 | No |
| `system_gmm_decomposition_controls` | System GMM | Validate multi-regressor decomposition specifications. | P1 | No |
| `difference_gmm_baseline_controls` | Difference GMM | Preserve already certified Difference GMM guard. | P1 | No |

## Required comparison outputs

Each specification should produce:

- `native_params.csv`;
- `stata_params.csv`;
- `native_diagnostics.csv`;
- `stata_diagnostics.csv`;
- `native_vs_stata_coefficients.csv`;
- `native_vs_stata_standard_errors.csv`;
- `native_vs_stata_summary.csv`.

## Required metrics

| Metric | Required? | Notes |
| --- | --- | --- |
| Coefficients | Yes | Compare parameter names after mapping. |
| Standard errors | Yes | Separate uncorrected and Windmeijer paths where relevant. |
| Hansen J | Yes | Include statistic and p-value where available. |
| AR(1) | Yes | Include p-value where available. |
| AR(2) | Yes | Include p-value where available. |
| Instrument count | Yes | Must match or be explicitly explained. |
| Observation count | Yes | Must match or be explicitly explained. |
| Group count | Yes | Must match or be explicitly explained. |
| Covariance type | Yes | Must be recorded in every artifact. |
| Sample identity | Yes | Store or hash sample rows where feasible. |

## Initial tolerance policy

| Object | Suggested tolerance |
| --- | --- |
| Coefficients | `max_abs_diff <= 1e-6` for strict parity; relaxed threshold must be justified. |
| Standard errors | `max_rel_diff <= 0.001` for Windmeijer-certified benchmark; other specs may start exploratory. |
| Hansen J | `max_abs_diff <= 1e-6` where formula/scaling is identical. |
| Instrument count | Exact match required. |
| Observation count | Exact match required. |
| Group count | Exact match required. |

## Status matrix

| Spec ID | Coefs | SEs | Hansen J | AR tests | N / groups | Instruments | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `system_gmm_baseline_controls` | Passed on current benchmark | Windmeijer passed on current benchmark | Passed on current benchmark | Pending broader guard | Passed | Passed | Certified benchmark |
| `system_gmm_no_controls` | Pending | Pending | Pending | Pending | Pending | Pending | Not started |
| `system_gmm_three_way_controls` | Pending | Pending | Pending | Pending | Pending | Pending | Not started |
| `system_gmm_decomposition_controls` | Pending | Pending | Pending | Pending | Pending | Pending | Not started |
| `difference_gmm_baseline_controls` | Passed | Pending review | Pending review | Pending review | Passed | Passed | Existing guard |

## Definition of Done

A specification becomes certified only when:

1. Stata benchmark artifacts are committed.
2. Native benchmark artifacts are committed.
3. Comparison scripts run deterministically.
4. A pytest guard checks the comparison.
5. CI passes.
6. README wording remains conservative and benchmark-specific.
