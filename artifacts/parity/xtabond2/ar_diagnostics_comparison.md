# xtabond2 vs Native System GMM AR Diagnostics

This report compares signed Arellano-Bond AR statistics and p-values.
The signed AR statistic is the primary parity object; p-values are checked as derived diagnostics.

| spec                              | same_nobs   | same_instrument_count   |   native_ar1 |   stata_ar1 |   abs_ar1_diff |   native_ar1_p |   stata_ar1_p |   abs_ar1_p_diff |   native_ar2 |   stata_ar2 |   abs_ar2_diff |   native_ar2_p |   stata_ar2_p |   abs_ar2_p_diff | status         |
|:----------------------------------|:------------|:------------------------|-------------:|------------:|---------------:|---------------:|--------------:|-----------------:|-------------:|------------:|---------------:|---------------:|--------------:|-----------------:|:---------------|
| system_gmm_baseline_controls      | True        | True                    |     -1.74791 |    -1.75156 |     0.00364469 |    0.0804793   |   0.0798501   |      0.000629189 |   -0.166705  |  -0.166599  |    0.000105507 |       0.867602 |      0.867685 |      8.3046e-05  | PASS_AR_PARITY |
| system_gmm_no_controls            | True        | True                    |     -1.48423 |    -1.48902 |     0.00478791 |    0.137747    |   0.136482    |      0.00126527  |   -0.101405  |  -0.0998827 |    0.00152184  |       0.919229 |      0.920437 |      0.0012081   | PASS_AR_PARITY |
| system_gmm_three_way_controls     | True        | True                    |     -7.1623  |    -7.21956 |     0.0572656  |    7.93374e-13 |   5.21558e-13 |      2.71816e-13 |   -0.0120136 |  -0.0127805 |    0.000766925 |       0.990415 |      0.989803 |      0.000611891 | PASS_AR_PARITY |
| system_gmm_decomposition_controls | True        | True                    |     -1.86029 |    -1.84924 |     0.0110506  |    0.0628449   |   0.0644236   |      0.00157875  |   -1.34064   |  -1.43146   |    0.0908164   |       0.180037 |      0.1523   |      0.0277379   | PASS_AR_PARITY |

## Thresholds

- `abs_ar1_diff <= 0.10`
- `abs_ar2_diff <= 0.10`
- `abs_ar1_p_diff <= 0.03`
- `abs_ar2_p_diff <= 0.03`
