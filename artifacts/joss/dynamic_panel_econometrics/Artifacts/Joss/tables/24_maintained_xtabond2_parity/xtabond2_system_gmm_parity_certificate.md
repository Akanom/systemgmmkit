# xtabond2 System GMM Parity Certificate

## Status

`PASS_XTABOND2_PARITY`

## Compared terms

| param   |   native_coef |   stata_coef |   abs_coef_diff |   abs_se_diff |
|:--------|--------------:|-------------:|----------------:|--------------:|
| L1.y    |      0.61774  |     0.61774  |     1.67459e-08 |   3.19246e-08 |
| w       |     -0.402523 |    -0.402523 |     1.91192e-08 |   1.98404e-08 |
| x       |      1.8413   |     1.8413   |     2.14464e-07 |   2.84447e-07 |

## Native-only terms

| param   |   native_coef |
|:--------|--------------:|
| _con    |      0.078261 |

## Interpretation

The maintained xtabond2 System GMM benchmark matches native systemgmmkit on the compared structural coefficients and Windmeijer-corrected standard errors within numerical tolerance. Native-only terms, currently `_con`, are reported separately and are not included in the strict xtabond2 comparison metric.
