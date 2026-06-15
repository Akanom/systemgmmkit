# FOD Difference GMM xtdpdgmm Parity Certification

## Status

Native `systemgmmkit` FOD Difference GMM coefficients are certified against Stata `xtdpdgmm model(fodev)` for collapsed one-step and two-step specifications.

## Certified

- Forward orthogonal deviations (`transformation="fod"`)
- Difference GMM only (`system=False`)
- Collapsed GMM-style instruments
- Endogenous `x`: `gmm(x, lag(1 2))`
- Predetermined `x`: `gmm(x, lag(0 1))`
- One-step and two-step coefficient parity
- IV-style transformed-equation instruments under FOD use current level values, matching `xtdpdgmm model(fodev)` behavior

## Not yet certified

- Exact robust covariance parity for endogenous-x two-step FOD
- Windmeijer correction for FOD Difference GMM

## Key result

| spec                      | status   |   matched_terms |   max_abs_coef_diff |   mean_abs_coef_diff |   max_abs_se_diff |   mean_abs_se_diff | message   |
|:--------------------------|:---------|----------------:|--------------------:|---------------------:|------------------:|-------------------:|:----------|
| fod_diff_endog_x_onestep  | COMPARED |               3 |         6.23289e-08 |          2.51433e-08 |       0.00247358  |        0.000948032 |           |
| fod_diff_endog_x_twostep  | COMPARED |               3 |         1.1819e-07  |          4.68984e-08 |       0.0734502   |        0.032786    |           |
| fod_diff_predet_x_onestep | COMPARED |               3 |         4.69298e-09 |          3.1645e-09  |       0.000100256 |        8.96907e-05 |           |
| fod_diff_predet_x_twostep | COMPARED |               3 |         4.50738e-09 |          2.96234e-09 |       0.00219863  |        0.00171256  |           |

## Interpretation

The maximum absolute coefficient differences are effectively at numerical precision for all four FOD Difference GMM specifications. This certifies the native point-estimate construction against the `xtdpdgmm model(fodev)` oracle for both endogenous and predetermined GMM-style timing.

Remaining differences are concentrated in robust standard errors, especially the endogenous-x two-step covariance path. These are treated as a separate covariance-certification task and are not included in the coefficient-parity claim.

## Implementation notes

Two implementation corrections were required:

1. FOD transformed-equation row construction must not use the same two-period burn-in as first-difference GMM.
2. Under FOD, IV-style instruments in transformed equations must be entered as current level values, not FOD-transformed values.

## Reviewer-facing claim

`systemgmmkit` provides coefficient-level parity with Stata `xtdpdgmm model(fodev)` for collapsed FOD Difference GMM under endogenous and predetermined instrument timing. Robust covariance and Windmeijer correction for this FOD path remain separate certification layers.