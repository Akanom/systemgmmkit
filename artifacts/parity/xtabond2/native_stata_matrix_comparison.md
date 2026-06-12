# Native vs Stata Matrix Comparison

This report compares native GMM internal diagnostics with exported xtabond2 matrices.

| object        |   native_nobs |   native_n_instruments |   native_n_params | native_params   | native_instruments                                                  | native_z_shape   | native_w_shape   |   native_j_stat |   native_ztu_norm |   native_w_norm |   native_hansen_p |   native_ar1_p |   native_ar2_p | status   | shape   |   frobenius_norm |          min |          max |
|:--------------|--------------:|-----------------------:|------------------:|:----------------|:--------------------------------------------------------------------|:-----------------|:-----------------|----------------:|------------------:|----------------:|------------------:|---------------:|---------------:|:---------|:--------|-----------------:|-------------:|-------------:|
| native_result |          1248 |                      8 |                 4 | L1.y;x;w;_con   | D:y:L2;D:y:L3;D:x:L2;D:x:L3;IV:w;L:diff:y:L1;L:diff:x:L1;L:constant | (2400, 8)        | (8, 8)           |         147.838 |           87.2232 |        0.783581 |       5.91396e-31 |    1.64592e-58 |       0.980515 | nan      | nan     |      nan         | nan          | nan          |
| stata_A1      |           nan |                    nan |               nan | nan             | nan                                                                 | nan              | nan              |         nan     |          nan      |      nan        |     nan           |  nan           |     nan        | loaded   | (8, 8)  |        0.0116105 |  -0.0006739  |   0.00551289 |
| stata_A2      |           nan |                    nan |               nan | nan             | nan                                                                 | nan              | nan              |         nan     |          nan      |      nan        |     nan           |  nan           |     nan        | loaded   | (8, 8)  |        0.0106323 |  -0.00126325 |   0.00510437 |
| stata_b       |           nan |                    nan |               nan | nan             | nan                                                                 | nan              | nan              |         nan     |          nan      |      nan        |     nan           |  nan           |     nan        | loaded   | (1, 4)  |        1.98497   |  -0.402523   |   1.8413     |
| stata_V       |           nan |                    nan |               nan | nan             | nan                                                                 | nan              | nan              |         nan     |          nan      |      nan        |     nan           |  nan           |     nan        | loaded   | (4, 4)  |        0.38682   |  -0.0128988  |   0.384168   |
| stata_Ze      |           nan |                    nan |               nan | nan             | nan                                                                 | nan              | nan              |         nan     |          nan      |      nan        |     nan           |  nan           |     nan        | loaded   | (8, 1)  |      117.341     | -75.4341     |  68.5811     |

## Key Interpretation

- Native and xtabond2 now match on N and instrument count.
- Native J-stat remains much larger than xtabond2 Hansen statistic.
- Stata A2 norm is far smaller than native W norm, indicating weighting-scale/normalization mismatch.
- Next step: test native W rescalings against xtabond2 A2 and recompute J-stat.