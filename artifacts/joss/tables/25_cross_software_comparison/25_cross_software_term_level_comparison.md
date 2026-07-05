# Artifact 25: Term-Level Cross-Software Result Comparison

## Coefficients

| model          | term_norm   |   Stata xtabond2 |   plm::pgmm |   pydynpd |   systemgmmkit |
|:---------------|:------------|-----------------:|------------:|----------:|---------------:|
| Difference GMM | L1_y        |        0.733183  |    0.711989 |  0.712171 |      0.71138   |
| Difference GMM | x_pred      |        0.248676  |    0.316246 |  0.316516 |      0.265653  |
| Difference GMM | x_exog      |        0.253523  |    0.249024 |  0.255129 |      0.251     |
| System GMM     | L1_y        |        0.929211  |    0.916725 |  0.900837 |      0.929211  |
| System GMM     | x_pred      |        0.0558769 |    0.198238 |  0.120436 |      0.0558768 |
| System GMM     | x_exog      |        0.242354  |    0.282099 |  0.273109 |      0.242354  |
| System GMM     | const       |        0.129496  |  nan        |  0.145447 |      0.129496  |

## Standard Errors

| model          | term_norm   |   Stata xtabond2 |   plm::pgmm |   pydynpd |   systemgmmkit |
|:---------------|:------------|-----------------:|------------:|----------:|---------------:|
| Difference GMM | L1_y        |        0.311135  |   0.226993  | 0.210474  |      0.264949  |
| Difference GMM | x_pred      |        0.25464   |   0.165331  | 0.155692  |      0.223165  |
| Difference GMM | x_exog      |        0.0519268 |   0.028834  | 0.0412421 |      0.0447061 |
| System GMM     | L1_y        |        0.0422931 |   0.027751  | 0.0268457 |      0.0422932 |
| System GMM     | x_pred      |        0.137906  |   0.0929676 | 0.100145  |      0.137907  |
| System GMM     | x_exog      |        0.0196909 |   0.0277367 | 0.0201395 |      0.019691  |
| System GMM     | const       |        0.0350864 | nan         | 0.0339087 |      0.0350866 |

## Differences Relative to systemgmmkit

| model          | term   | comparison_software   |   systemgmmkit_coef |   comparison_coef |    coef_diff |   abs_coef_diff |   systemgmmkit_se |   comparison_se |      se_diff |   abs_se_diff |
|:---------------|:-------|:----------------------|--------------------:|------------------:|-------------:|----------------:|------------------:|----------------:|-------------:|--------------:|
| Difference GMM | L1_y   | Stata xtabond2        |           0.71138   |         0.733183  | -0.021803    |     0.021803    |         0.264949  |       0.311135  | -0.0461864   |   0.0461864   |
| Difference GMM | x_pred | Stata xtabond2        |           0.265653  |         0.248676  |  0.0169768   |     0.0169768   |         0.223165  |       0.25464   | -0.0314751   |   0.0314751   |
| Difference GMM | x_exog | Stata xtabond2        |           0.251     |         0.253523  | -0.0025235   |     0.0025235   |         0.0447061 |       0.0519268 | -0.00722074  |   0.00722074  |
| Difference GMM | L1_y   | pydynpd               |           0.71138   |         0.712171  | -0.000790615 |     0.000790615 |         0.264949  |       0.210474  |  0.0544743   |   0.0544743   |
| Difference GMM | x_pred | pydynpd               |           0.265653  |         0.316516  | -0.0508635   |     0.0508635   |         0.223165  |       0.155692  |  0.0674724   |   0.0674724   |
| Difference GMM | x_exog | pydynpd               |           0.251     |         0.255129  | -0.0041294   |     0.0041294   |         0.0447061 |       0.0412421 |  0.00346394  |   0.00346394  |
| Difference GMM | L1_y   | plm::pgmm             |           0.71138   |         0.711989  | -0.000608685 |     0.000608685 |         0.264949  |       0.226993  |  0.0379555   |   0.0379555   |
| Difference GMM | x_pred | plm::pgmm             |           0.265653  |         0.316246  | -0.0505934   |     0.0505934   |         0.223165  |       0.165331  |  0.0578331   |   0.0578331   |
| Difference GMM | x_exog | plm::pgmm             |           0.251     |         0.249024  |  0.00197574  |     0.00197574  |         0.0447061 |       0.028834  |  0.0158721   |   0.0158721   |
| System GMM     | L1_y   | Stata xtabond2        |           0.929211  |         0.929211  |  2.31096e-09 |     2.31096e-09 |         0.0422932 |       0.0422931 |  1.74551e-07 |   1.74551e-07 |
| System GMM     | x_pred | Stata xtabond2        |           0.0558768 |         0.0558769 | -2.49213e-08 |     2.49213e-08 |         0.137907  |       0.137906  |  5.71535e-07 |   5.71535e-07 |
| System GMM     | x_exog | Stata xtabond2        |           0.242354  |         0.242354  |  1.95913e-09 |     1.95913e-09 |         0.019691  |       0.0196909 |  8.12429e-08 |   8.12429e-08 |
| System GMM     | const  | Stata xtabond2        |           0.129496  |         0.129496  | -1.99104e-09 |     1.99104e-09 |         0.0350866 |       0.0350864 |  1.44225e-07 |   1.44225e-07 |
| System GMM     | L1_y   | pydynpd               |           0.929211  |         0.900837  |  0.0283736   |     0.0283736   |         0.0422932 |       0.0268457 |  0.0154475   |   0.0154475   |
| System GMM     | x_pred | pydynpd               |           0.0558768 |         0.120436  | -0.0645595   |     0.0645595   |         0.137907  |       0.100145  |  0.0377615   |   0.0377615   |
| System GMM     | x_exog | pydynpd               |           0.242354  |         0.273109  | -0.0307548   |     0.0307548   |         0.019691  |       0.0201395 | -0.000448537 |   0.000448537 |
| System GMM     | const  | pydynpd               |           0.129496  |         0.145447  | -0.015951    |     0.015951    |         0.0350866 |       0.0339087 |  0.00117789  |   0.00117789  |
| System GMM     | L1_y   | plm::pgmm             |           0.929211  |         0.916725  |  0.0124861   |     0.0124861   |         0.0422932 |       0.027751  |  0.0145423   |   0.0145423   |
| System GMM     | x_pred | plm::pgmm             |           0.0558768 |         0.198238  | -0.142361    |     0.142361    |         0.137907  |       0.0929676 |  0.0449389   |   0.0449389   |
| System GMM     | x_exog | plm::pgmm             |           0.242354  |         0.282099  | -0.039745    |     0.039745    |         0.019691  |       0.0277367 | -0.00804571  |   0.00804571  |

## Interpretation

Stata xtabond2 is the closest numerical comparator. For System GMM, systemgmmkit and Stata xtabond2 agree at numerical precision across all reported terms. For Difference GMM, the Stata comparison falls within the predefined tolerant auxiliary band.

The pydynpd and plm::pgmm results are retained as ecosystem comparison outputs. Their estimates are directionally comparable, especially for the lagged dependent variable and the exogenous regressor, but they differ beyond the auxiliary tolerance band for some coefficients and standard errors, particularly for x_pred. These rows are therefore classified as REVIEW rather than parity failures.

The pydynpd Difference GMM run reported 960 observations, while the aligned Stata/systemgmmkit Difference GMM comparison uses 840 observations. This suggests that part of the cross-software difference may come from effective-sample construction. More generally, dynamic-panel GMM comparisons are sensitive to instrument construction, sample trimming, level-equation treatment, finite-sample correction, and covariance scaling.

Formal parity claims in the paper should rely on Artifact 24 and the Stata-based validation results. Artifact 25 supports ecosystem positioning and demonstrates that systemgmmkit produces comparable dynamic-panel GMM outputs relative to established Python and R packages, but it is not used as the primary parity certificate.
