# GMM Lag-Window Certification Report

## Scope

This report validates the role-specific and variable-specific GMM lag-window API.

The validation covers:

- global GMM lag windows via `gmm_lags`
- role-specific lag windows via `gmm_lags_by_role`
- variable-specific lag windows via `gmm_lags_by_variable`
- backward-compatible default lag behavior
- manual xtabond2 execution on existing benchmark data
- overidentification degrees-of-freedom recovery blocker

## Certification Status

| Layer | Status | Interpretation |
|---|---|---|
| Public API | PASS | New arguments are accepted and translated into internal GMM lag windows. |
| Backward compatibility | PASS | Baseline dependent lag default remains `(2, 3)` while other GMM variables retain `(2, 2)`. |
| Stata command generation | PASS | Generated `xtabond2` commands contain the expected `gmmstyle(... lag(a b) collapse)` blocks. |
| Manual Stata real-data execution | PASS | The generated commands run on the existing benchmark data. |
| Overidentification df blocker | PASS | Execution blocks if Hansen/Sargan df cannot be recovered. Real-data run recovered df successfully. |
| Native-vs-xtabond2 parity for custom lag windows | NOT CERTIFIED | Native System GMM remains experimental for these custom lag-window specifications. |

## Real-Data Stata Diagnostics

| model   |    N |   N_g |   k_instruments |   k_params |   overid_df |   overid_df_source |   hansen_p |    sargan_p |       ar1_p |    ar2_p |
|:--------|-----:|------:|----------------:|-----------:|------------:|-------------------:|-----------:|------------:|------------:|---------:|
| m_base  | 1248 |    96 |              19 |          4 |          15 |                  2 | 0.0152869  | 5.48408e-07 | 0.000170503 | 0.866493 |
| m_role  | 1248 |    96 |              27 |          4 |          23 |                  2 | 0.0756832  | 2.75985e-06 | 2.27466e-05 | 0.963886 |
| m_var   | 1248 |    96 |              24 |          4 |          20 |                  2 | 0.00680447 | 1.05347e-09 | 4.79847e-06 | 0.735195 |

## Native-vs-Stata No-Time-Dummy Comparison

The no-time-dummy comparison was run to remove structural time-dummy contamination. Material coefficient gaps remain; therefore native-vs-xtabond2 parity is not certified for these new custom lag-window specifications.

| model   |   max_abs_coef_diff |   mean_abs_coef_diff |   max_abs_se_diff |   mean_abs_se_diff |
|:--------|--------------------:|---------------------:|------------------:|-------------------:|
| m_base  |            0.588722 |            0.167217  |          0.266354 |          0.0732235 |
| m_role  |            0.351616 |            0.128682  |          0.173591 |          0.0747808 |
| m_var   |            0.291692 |            0.0979386 |          0.199787 |          0.0990701 |

## Decision

This feature is accepted as an API/specification and Stata command-generation enhancement.

It must not be described as native System GMM parity for custom lag-window specifications until the native backend is separately certified against xtabond2 for these exact specifications.

## Follow-up Backlog

1. Align native instrument counting with xtabond2 for custom lag-window specifications.
2. Confirm whether the native backend applies `spec.gmm` lag windows identically across difference and level equations.
3. Extract Hansen/Sargan diagnostics from native results consistently.
4. Re-run native-vs-xtabond2 parity after backend alignment.
