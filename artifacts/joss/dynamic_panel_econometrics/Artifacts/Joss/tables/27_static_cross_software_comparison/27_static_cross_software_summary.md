# Artifact 27: Static Cross-Software Comparison

## Pairwise Summary Relative to systemgmmkit

| model          | reference    | comparison_software   |   common_terms |   reference_only_terms |   comparison_only_terms |   max_abs_coef_diff |   max_abs_se_diff | status            |
|:---------------|:-------------|:----------------------|---------------:|-----------------------:|------------------------:|--------------------:|------------------:|:------------------|
| OLS            | systemgmmkit | R lm                  |              4 |                      0 |                       0 |         1.22125e-15 |       1.00614e-16 | PASS_NUMERIC      |
| OLS            | systemgmmkit | Stata                 |              4 |                      0 |                       0 |         2.15841e-08 |       4.01439e-10 | PASS_COEFFICIENTS |
| OLS            | systemgmmkit | statsmodels           |              4 |                      0 |                       0 |         6.66134e-16 |       0           | PASS_NUMERIC      |
| Pooled OLS     | systemgmmkit | R plm                 |              4 |                      0 |                       0 |         1.22125e-15 |       1.00614e-16 | PASS_NUMERIC      |
| Pooled OLS     | systemgmmkit | Stata                 |              4 |                      0 |                       0 |         2.15841e-08 |       4.01439e-10 | PASS_COEFFICIENTS |
| Pooled OLS     | systemgmmkit | linearmodels          |              4 |                      0 |                       0 |         9.99201e-16 |       0           | PASS_NUMERIC      |
| Fixed Effects  | systemgmmkit | R plm                 |              3 |                      0 |                       0 |         7.77156e-16 |       1.00614e-16 | PASS_NUMERIC      |
| Fixed Effects  | systemgmmkit | Stata                 |              3 |                      0 |                       0 |         1.59922e-08 |       1.14431e-09 | PASS_COEFFICIENTS |
| Fixed Effects  | systemgmmkit | linearmodels          |              3 |                      0 |                       0 |         0           |       0           | PASS_NUMERIC      |
| Random Effects | systemgmmkit | R plm                 |              4 |                      0 |                       0 |         1.22125e-15 |       0.000657776 | PASS_COEFFICIENTS |
| Random Effects | systemgmmkit | Stata                 |              4 |                      0 |                       0 |         2.15841e-08 |       0.000657775 | PASS_COEFFICIENTS |
| Random Effects | systemgmmkit | linearmodels          |              4 |                      0 |                       0 |         9.99201e-16 |       0.000657776 | PASS_COEFFICIENTS |
| 2SLS           | systemgmmkit | R AER::ivreg          |              4 |                      0 |                       0 |         5.32907e-15 |       3.05311e-16 | PASS_NUMERIC      |
| 2SLS           | systemgmmkit | Stata                 |              4 |                      0 |                       0 |         6.34952e-08 |       0.000380336 | PASS_COEFFICIENTS |
| 2SLS           | systemgmmkit | linearmodels          |              4 |                      0 |                       0 |         6.55032e-15 |       0.000380341 | PASS_COEFFICIENTS |

## Coefficients

| model          | term_norm   |   R AER::ivreg |       R lm |      R plm |      Stata |   linearmodels |   statsmodels |   systemgmmkit |
|:---------------|:------------|---------------:|-----------:|-----------:|-----------:|---------------:|--------------:|---------------:|
| 2SLS           | L1_y        |      1.02296   | nan        | nan        |  1.02296   |      1.02296   |    nan        |      1.02296   |
| 2SLS           | const       |      0.0613915 | nan        | nan        |  0.0613915 |      0.0613915 |    nan        |      0.0613915 |
| 2SLS           | x_exog      |      0.249587  | nan        | nan        |  0.249587  |      0.249587  |    nan        |      0.249587  |
| 2SLS           | x_pred      |     -0.508035  | nan        | nan        | -0.508035  |     -0.508035  |    nan        |     -0.508035  |
| Fixed Effects  | L1_y        |    nan         | nan        |   0.53785  |  0.53785   |      0.53785   |    nan        |      0.53785   |
| Fixed Effects  | x_exog      |    nan         | nan        |   0.219076 |  0.219076  |      0.219076  |    nan        |      0.219076  |
| Fixed Effects  | x_pred      |    nan         | nan        |   0.348588 |  0.348588  |      0.348588  |    nan        |      0.348588  |
| OLS            | L1_y        |    nan         |   0.967552 | nan        |  0.967552  |    nan         |      0.967552 |      0.967552  |
| OLS            | const       |    nan         |   0.1148   | nan        |  0.1148    |    nan         |      0.1148   |      0.1148    |
| OLS            | x_exog      |    nan         |   0.231979 | nan        |  0.231979  |    nan         |      0.231979 |      0.231979  |
| OLS            | x_pred      |    nan         |   0.236144 | nan        |  0.236144  |    nan         |      0.236144 |      0.236144  |
| Pooled OLS     | L1_y        |    nan         | nan        |   0.967552 |  0.967552  |      0.967552  |    nan        |      0.967552  |
| Pooled OLS     | const       |    nan         | nan        |   0.1148   |  0.1148    |      0.1148    |    nan        |      0.1148    |
| Pooled OLS     | x_exog      |    nan         | nan        |   0.231979 |  0.231979  |      0.231979  |    nan        |      0.231979  |
| Pooled OLS     | x_pred      |    nan         | nan        |   0.236144 |  0.236144  |      0.236144  |    nan        |      0.236144  |
| Random Effects | L1_y        |    nan         | nan        |   0.967552 |  0.967552  |      0.967552  |    nan        |      0.967552  |
| Random Effects | const       |    nan         | nan        |   0.1148   |  0.1148    |      0.1148    |    nan        |      0.1148    |
| Random Effects | x_exog      |    nan         | nan        |   0.231979 |  0.231979  |      0.231979  |    nan        |      0.231979  |
| Random Effects | x_pred      |    nan         | nan        |   0.236144 |  0.236144  |      0.236144  |    nan        |      0.236144  |

## Standard Errors

| model          | term_norm   |   R AER::ivreg |        R lm |       R plm |     Stata |   linearmodels |   statsmodels |   systemgmmkit |
|:---------------|:------------|---------------:|------------:|------------:|----------:|---------------:|--------------:|---------------:|
| 2SLS           | L1_y        |      0.0214533 | nan         | nan         | 0.0214086 |      0.0214086 |   nan         |      0.0214533 |
| 2SLS           | const       |      0.0335845 | nan         | nan         | 0.0335145 |      0.0335145 |   nan         |      0.0335845 |
| 2SLS           | x_exog      |      0.0289802 | nan         | nan         | 0.0289198 |      0.0289198 |   nan         |      0.0289802 |
| 2SLS           | x_pred      |      0.182373  | nan         | nan         | 0.181993  |      0.181993  |   nan         |      0.182373  |
| Fixed Effects  | L1_y        |    nan         | nan         |   0.0197821 | 0.0197821 |      0.0197821 |   nan         |      0.0197821 |
| Fixed Effects  | x_exog      |    nan         | nan         |   0.0163158 | 0.0163158 |      0.0163158 |   nan         |      0.0163158 |
| Fixed Effects  | x_pred      |    nan         | nan         |   0.0203251 | 0.0203251 |      0.0203251 |   nan         |      0.0203251 |
| OLS            | L1_y        |    nan         |   0.0106426 | nan         | 0.0106426 |    nan         |     0.0106426 |      0.0106426 |
| OLS            | const       |    nan         |   0.020217  | nan         | 0.020217  |    nan         |     0.020217  |      0.020217  |
| OLS            | x_exog      |    nan         |   0.0190865 | nan         | 0.0190865 |    nan         |     0.0190865 |      0.0190865 |
| OLS            | x_pred      |    nan         |   0.0218819 | nan         | 0.0218819 |    nan         |     0.0218819 |      0.0218819 |
| Pooled OLS     | L1_y        |    nan         | nan         |   0.0106426 | 0.0106426 |      0.0106426 |   nan         |      0.0106426 |
| Pooled OLS     | const       |    nan         | nan         |   0.020217  | 0.020217  |      0.020217  |   nan         |      0.020217  |
| Pooled OLS     | x_exog      |    nan         | nan         |   0.0190865 | 0.0190865 |      0.0190865 |   nan         |      0.0190865 |
| Pooled OLS     | x_pred      |    nan         | nan         |   0.0218819 | 0.0218819 |      0.0218819 |   nan         |      0.0218819 |
| Random Effects | L1_y        |    nan         | nan         |   0.0106426 | 0.0106426 |      0.0106426 |   nan         |      0.0105025 |
| Random Effects | const       |    nan         | nan         |   0.020217  | 0.020217  |      0.020217  |   nan         |      0.0201129 |
| Random Effects | x_exog      |    nan         | nan         |   0.0190865 | 0.0190865 |      0.0190865 |   nan         |      0.0184287 |
| Random Effects | x_pred      |    nan         | nan         |   0.0218819 | 0.0218819 |      0.0218819 |   nan         |      0.0217518 |

## Interpretation

This artifact compares static and quasi-static estimators across Python, R, Stata, and systemgmmkit. OLS, pooled OLS, fixed effects, random effects, and 2SLS are compared term by term. Fixed-effects comparisons exclude intercepts because fixed-effect intercept normalization differs across implementations. Coefficient agreement is the primary comparison target for random effects and 2SLS where covariance scaling conventions may differ.
