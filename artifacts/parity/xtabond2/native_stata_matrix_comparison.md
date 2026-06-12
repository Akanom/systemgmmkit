# Native vs Stata Matrix Comparison

This report checks whether Stata matrix exports are available and summarizes their dimensions/norms.

| object        |   native_nobs |   native_n_instruments |   native_n_params | native_params   | native_instruments                                                  | status   | shape   |   frobenius_norm |          min |          max |
|:--------------|--------------:|-----------------------:|------------------:|:----------------|:--------------------------------------------------------------------|:---------|:--------|-----------------:|-------------:|-------------:|
| native_result |          1248 |                      8 |                 4 | L1.y;x;w;_con   | D:y:L2;D:y:L3;D:x:L2;D:x:L3;IV:w;L:diff:y:L1;L:diff:x:L1;L:constant | nan      | nan     |      nan         | nan          | nan          |
| stata_A1      |           nan |                    nan |               nan | nan             | nan                                                                 | loaded   | (8, 8)  |        0.0116105 |  -0.0006739  |   0.00551289 |
| stata_A2      |           nan |                    nan |               nan | nan             | nan                                                                 | loaded   | (8, 8)  |        0.0106323 |  -0.00126325 |   0.00510437 |
| stata_b       |           nan |                    nan |               nan | nan             | nan                                                                 | loaded   | (1, 4)  |        1.98497   |  -0.402523   |   1.8413     |
| stata_V       |           nan |                    nan |               nan | nan             | nan                                                                 | loaded   | (4, 4)  |        0.38682   |  -0.0128988  |   0.384168   |
| stata_Ze      |           nan |                    nan |               nan | nan             | nan                                                                 | loaded   | (8, 1)  |      117.341     | -75.4341     |  68.5811     |

## Interpretation

- `stata_A2` is the key matrix for two-step weighting comparison.
- `stata_Ze` is useful for checking moment aggregation scale.
- Native does not yet expose its full W/Z matrices, so direct matrix parity is pending.
- Next patch should expose native W, Z shape, and optionally Z matrix under a debug flag.