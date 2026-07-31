# xtabond2 System GMM Parity Certificate

## Status

`PASS_XTABOND2_PARITY`

## Compared terms

| param   |   native_coef |   stata_coef |   abs_coef_diff |   abs_se_diff |
|:--------|--------------:|-------------:|----------------:|--------------:|
| L1.y    |      0.61774  |     0.61774  |     1.44329e-15 |   3.78581e-08 |
| _con    |      0.078261 |     0.078261 |     4.02456e-16 |   4.69122e-08 |
| w       |     -0.402523 |    -0.402523 |     4.996e-16   |   2.24801e-08 |
| x       |      1.8413   |     1.8413   |     2.30926e-14 |   3.58303e-07 |

## Native-only terms

None

## Stata-only terms

None

## Interpretation

The maintained xtabond2 System GMM benchmark matches native systemgmmkit on the complete expected parameter set and Windmeijer-corrected standard errors within numerical tolerance. Any missing, native-only, or Stata-only parameter fails the strict comparison.
