# GMM Internal Diagnostics Comparison

## Native

| spec                         |   nobs |   n_instruments |   n_params |   overid_df |   residual_norm |   residual_ss | params        | instrument_names                                                    |    hansen_p |    sargan_p |       ar1_p |    ar2_p |
|:-----------------------------|-------:|----------------:|-----------:|------------:|----------------:|--------------:|:--------------|:--------------------------------------------------------------------|------------:|------------:|------------:|---------:|
| system_gmm_baseline_controls |   1248 |               8 |          4 |           4 |         98.1971 |       9642.67 | L1.y;x;w;_con | D:y:L2;D:y:L3;D:x:L2;D:x:L3;IV:w;L:diff:y:L1;L:diff:x:L1;L:constant | 5.91396e-31 | 5.91396e-31 | 1.64592e-58 | 0.980515 |

## xtabond2

| spec                         |   stata_nobs |   stata_n_groups |   stata_n_instruments |   stata_hansen |   stata_hansen_df |   stata_hansen_p |   stata_sargan |   stata_sargan_df |   stata_sargan_p |   stata_ar1 |   stata_ar1_p |   stata_ar2 |   stata_ar2_p |
|:-----------------------------|-------------:|-----------------:|----------------------:|---------------:|------------------:|-----------------:|---------------:|------------------:|-----------------:|------------:|--------------:|------------:|--------------:|
| system_gmm_baseline_controls |         1248 |               96 |                     8 |        6.57737 |                 4 |          0.15998 |        8.10191 |                 4 |        0.0879155 |    -1.75156 |     0.0798501 |   -0.166599 |      0.867685 |