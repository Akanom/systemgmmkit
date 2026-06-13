# xtabond2 vs Native System GMM Parity

## Status

`PASS_STRICT_XTABOND2_SYSTEM_GMM_BASELINE`

## Certification Summary

| check                        |       native |        stata |    abs_diff | status   |
|:-----------------------------|-------------:|-------------:|------------:|:---------|
| Sample size                  | 1248         | 1248         | 0           | PASS     |
| Instrument count             |    8         |    8         | 0           | PASS     |
| Max coefficient difference   |              |              | 1.57399e-07 | PASS     |
| Max Windmeijer SE difference |              |              | 2.86137e-07 | PASS     |
| Hansen p-value               |    0.15998   |    0.15998   | 1.76539e-08 | PASS     |
| AR(1) statistic              |   -1.74791   |   -1.75156   | 0.00364469  | PASS     |
| AR(1) p-value                |    0.0804793 |    0.0798501 | 0.000629189 | PASS     |
| AR(2) statistic              |   -0.166705  |   -0.166599  | 0.000105507 | PASS     |
| AR(2) p-value                |    0.867602  |    0.867685  | 8.3046e-05  | PASS     |

## Coefficient Comparison

| param   | param_native_name   | param_stata_name   |   native_coef |   stata_coef |   abs_coef_diff |   native_std_err |   stata_std_err |   abs_se_diff |   rel_se_diff |   native_z |   native_p_value |   dof |          t |           p |     min95 |     max95 | covariance_type                      |
|:--------|:--------------------|:-------------------|--------------:|-------------:|----------------:|-----------------:|----------------:|--------------:|--------------:|-----------:|-----------------:|------:|-----------:|------------:|----------:|----------:|:-------------------------------------|
| L1.y    | L1.y                | L.y                |      0.61774  |     0.61774  |     1.04194e-08 |        0.0654891 |       0.0654891 |   3.29051e-08 |   5.02451e-07 |   9.43271  |      3.99618e-21 |    95 |   9.43272  | 2.69599e-15 |  0.487728 |  0.747753 | robust-clustered-two-step-windmeijer |
| _con    | _con                | _cons              |      0.078261 |     0.078261 |     5.43458e-09 |        0.0811515 |       0.0811515 |   4.65113e-08 |   5.73142e-07 |   0.964381 |      0.334855    |    95 |   0.964382 | 0.337303    | -0.082845 |  0.239367 | robust-clustered-two-step-windmeijer |
| w       | w                   | w                  |     -0.402523 |    -0.402523 |     8.37917e-09 |        0.0388874 |       0.0388874 |   1.96554e-08 |   5.05443e-07 | -10.351    |      4.14193e-25 |    95 | -10.351    | 2.94426e-17 | -0.479725 | -0.325322 | robust-clustered-two-step-windmeijer |
| x       | x                   | x                  |      1.8413   |     1.8413   |     1.57399e-07 |        0.619813  |       0.619813  |   2.86137e-07 |   4.61651e-07 |   2.97073  |      0.00297096  |    95 |   2.97073  | 0.00376238  |  0.610811 |  3.07178  | robust-clustered-two-step-windmeijer |

## Diagnostics Comparison

| native_file_spec             |   native_file_native_nobs |   native_file_native_n_instruments | native_file_native_backend   | native_file_native_covariance_type   | native_file_native_instrument_names                                 |   native_file_native_hansen_p |   native_file_native_ar1 |   native_file_native_ar1_p |   native_file_native_ar2 |   native_file_native_ar2_p |   native_file_native_j_stat | native_file_native_has_constant_param   | stata_file_spec              |   stata_file_stata_nobs |   stata_file_stata_n_groups |   stata_file_stata_n_instruments |   stata_file_stata_hansen_p |   stata_file_stata_sargan_p |   stata_file_stata_ar1 |   stata_file_stata_ar1_p |   stata_file_stata_ar2 |   stata_file_stata_ar2_p |
|:-----------------------------|--------------------------:|-----------------------------------:|:-----------------------------|:-------------------------------------|:--------------------------------------------------------------------|------------------------------:|-------------------------:|---------------------------:|-------------------------:|---------------------------:|----------------------------:|:----------------------------------------|:-----------------------------|------------------------:|----------------------------:|---------------------------------:|----------------------------:|----------------------------:|-----------------------:|-------------------------:|-----------------------:|-------------------------:|
| system_gmm_baseline_controls |                      1248 |                                  8 | native-gmm                   | robust-clustered-two-step-windmeijer | D:y:L2;D:y:L3;D:x:L2;D:x:L3;IV:w;L:diff:y:L1;L:diff:x:L1;L:constant |                       0.15998 |                 -1.74791 |                  0.0804793 |                -0.166705 |                   0.867602 |                     6.57737 | True                                    | system_gmm_baseline_controls |                    1248 |                          96 |                                8 |                     0.15998 |                   0.0879155 |               -1.75156 |                0.0798501 |              -0.166599 |                 0.867685 |

## Artifact Sources

- Native parameters: `artifacts\parity\xtabond2\specs\system_gmm_baseline_controls\windmeijer\native_params.csv`
- Native diagnostics: `artifacts\parity\xtabond2\specs\system_gmm_baseline_controls\windmeijer\native_diagnostics.csv`
- Stata parameters: `artifacts\parity\xtabond2\xtabond2_system_gmm_params.csv`
- Stata diagnostics: `artifacts\parity\xtabond2\xtabond2_system_gmm_diagnostics.csv`

## Generated Files

- `system_gmm_benchmark.csv`
- `system_gmm_xtabond2_parity.do`
- `xtabond2_native_system_gmm_coef_comparison.csv`
- `xtabond2_native_system_gmm_diagnostics_comparison.csv`
- `xtabond2_native_system_gmm_parity.md`

## Notes

Stata parameter aliases are normalized before comparison: `L.y` maps to `L1.y`, and `_cons` maps to `_con`.
The signed AR statistics are treated as the primary AR parity object; AR p-values are checked as derived diagnostics.
