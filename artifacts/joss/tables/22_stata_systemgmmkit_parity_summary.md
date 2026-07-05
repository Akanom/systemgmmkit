# Artifact 22: Controlled Stata/systemgmmkit Comparison

## Status Summary

| model          | sgk_file                                            | stata_file                                                     |   common_terms |   sgk_only_terms |   stata_only_terms |   max_abs_coef_diff |   max_abs_se_diff |   max_abs_p_diff | status                  |
|:---------------|:----------------------------------------------------|:---------------------------------------------------------------|---------------:|-----------------:|-------------------:|--------------------:|------------------:|-----------------:|:------------------------|
| Difference GMM | Artifacts\Joss\tables\22_difference_gmm_results.csv | Artifacts\Joss\tables\22_stata_difference_gmm_coefficients.csv |              3 |                0 |                  0 |         0.021803    |       0.0461864   |      0.0948838   | PASS_TOLERANT_AUXILIARY |
| System GMM     | Artifacts\Joss\tables\22_system_gmm_results.csv     | Artifacts\Joss\tables\22_stata_system_gmm_coefficients.csv     |              4 |                0 |                  0 |         2.49213e-08 |       5.71535e-07 |      1.36706e-06 | PASS_NUMERIC            |

## Interpretation

This comparison uses aligned effective samples between Stata and systemgmmkit. System GMM reaches numerical agreement. Difference GMM falls within the predefined tolerant auxiliary agreement band. Formal parity claims for the paper should rely on Artifact 24, the maintained dynamic-GMM parity certificate.
