# Artifact 25: Cross-Software Result Comparison

## Pairwise Summary

| model          | reference    | comparison_software   |   common_terms |   reference_only_terms |   comparison_only_terms |   max_abs_coef_diff |   max_abs_se_diff | status                  |
|:---------------|:-------------|:----------------------|---------------:|-----------------------:|------------------------:|--------------------:|------------------:|:------------------------|
| Difference GMM | systemgmmkit | Stata xtabond2        |              3 |                      0 |                       0 |         0.021803    |       0.0461864   | PASS_TOLERANT_AUXILIARY |
| Difference GMM | systemgmmkit | plm::pgmm             |              3 |                      0 |                       0 |         0.0505934   |       0.0578331   | REVIEW                  |
| Difference GMM | systemgmmkit | pydynpd               |              3 |                      0 |                       0 |         0.0508635   |       0.0674724   | REVIEW                  |
| System GMM     | systemgmmkit | Stata xtabond2        |              4 |                      0 |                       0 |         2.49213e-08 |       5.71535e-07 | PASS_NUMERIC            |
| System GMM     | systemgmmkit | plm::pgmm             |              3 |                      1 |                       0 |         0.142361    |       0.0449389   | REVIEW                  |
| System GMM     | systemgmmkit | pydynpd               |              4 |                      0 |                       0 |         0.0645595   |       0.0377615   | REVIEW                  |

## Interpretation

The comparison uses systemgmmkit as the reference within this artifact. Stata xtabond2 is expected to match closely where the effective sample and instrument conventions are aligned. R package results are reported as ecosystem comparison outputs; strict parity is not assumed unless the underlying model specification and instrument construction are fully aligned.
