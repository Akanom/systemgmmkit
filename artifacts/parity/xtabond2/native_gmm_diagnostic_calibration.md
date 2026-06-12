# Native GMM Diagnostic Calibration

This file compares native experimental diagnostic p-values against xtabond2 implied statistics.

## Calibration Table

| diagnostic   | source   |     p_value |   implied_stat_df1 |   implied_abs_z |
|:-------------|:---------|------------:|-------------------:|----------------:|
| hansen_p     | xtabond2 | 0.15998     |            1.97441 |     nan         |
| sargan_p     | xtabond2 | 0.0879155   |            2.91213 |     nan         |
| hansen_p     | native   | 5.91396e-31 |          133.843   |     nan         |
| ar1_p        | native   | 1.64592e-58 |          nan       |      16.1271    |
| ar1_p        | xtabond2 | 0.0798501   |          nan       |       1.75156   |
| ar2_p        | native   | 0.980515    |          nan       |       0.0244227 |
| ar2_p        | xtabond2 | 0.867685    |          nan       |       0.166599  |

## Interpretation

- Nobs and instrument-count parity are already achieved.
- Native AR(2) is directionally close to xtabond2.
- Native AR(1) and Hansen are not parity-calibrated.
- Coefficient and diagnostic parity should not be claimed until the weighting matrix and residual moment tests are aligned with xtabond2.