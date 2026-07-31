# xtabond2 System GMM Unified Parity Certificate

This certificate compares native SystemGMMKit with Stata `xtabond2` on 4
maintained, specification-aligned fixtures. Claims are benchmark-specific.
The maintained specification list and numerical gates come from
`artifacts/parity/xtabond2/system_gmm_certification_specs.json`.
Comparator identity is carried by the path-free, machine-generated provenance
attestation `artifacts/parity/xtabond2/xtabond2_comparator_provenance.json`. The historical Stata
exports predate embedded comparator columns, so the attestation binds their current
hashes to allowlisted fields from the completed local run log. The source log is not
committed because it contains machine-specific paths; its hash and this limitation are
preserved in the attestation.

| spec                              | parameter_set_complete   | parameters_finite   | standard_errors_positive   |   max_abs_coef_diff |   max_rel_se_diff | parameter_status      | same_spec_id   | same_stata_version   | same_xtabond2_e_version   | same_xtabond2_ado_header   | stata_output_hashes_match_provenance   | stata_export_provenance_embedded   | comparator_status   | same_nobs   | same_n_groups   | same_instrument_count   | same_overid_df   |   stata_hansen_p | stata_hansen_reject_005   |   stata_sargan_p | stata_sargan_reject_005   |   abs_hansen_diff |   abs_hansen_p_diff |   abs_sargan_diff |   abs_sargan_p_diff |   abs_ar1_z_diff |   abs_ar1_p_diff |   abs_ar2_z_diff |   abs_ar2_p_diff | diagnostic_status      | status               |
|:----------------------------------|:-------------------------|:--------------------|:---------------------------|--------------------:|------------------:|:----------------------|:---------------|:---------------------|:--------------------------|:---------------------------|:---------------------------------------|:-----------------------------------|:--------------------|:------------|:----------------|:------------------------|:-----------------|-----------------:|:--------------------------|-----------------:|:--------------------------|------------------:|--------------------:|------------------:|--------------------:|-----------------:|-----------------:|-----------------:|-----------------:|:-----------------------|:---------------------|
| system_gmm_baseline_controls      | True                     | True                | True                       |         2.30926e-14 |       5.78083e-07 | PASS_PARAMETER_PARITY | True           | True                 | True                      | True                       | True                                   | False                              | PASS                | True        | True            | True                    | True             |       0.15998    | False                     |      0.0879155   | False                     |       2.06057e-13 |         1.27121e-14 |       2.61124e-13 |         9.29812e-15 |      0.000304539 |      5.24207e-05 |      0.000107342 |      8.44671e-05 | PASS_DIAGNOSTIC_PARITY | PASS_XTABOND2_PARITY |
| system_gmm_no_controls            | True                     | True                | True                       |         8.88178e-16 |       5.46217e-07 | PASS_PARAMETER_PARITY | True           | True                 | True                      | True                       | True                                   | False                              | PASS                | True        | True            | True                    | True             |       0.0235612  | True                      |      0.00567987  | True                      |       2.07834e-13 |         2.09902e-15 |       2.91323e-13 |         6.99961e-16 |      0.0011769   |      0.000310172 |      1.91173e-05 |      1.51775e-05 | PASS_DIAGNOSTIC_PARITY | PASS_XTABOND2_PARITY |
| system_gmm_three_way_controls     | True                     | True                | True                       |         3.66374e-15 |       2.63268e-06 | PASS_PARAMETER_PARITY | True           | True                 | True                      | True                       | True                                   | False                              | PASS                | True        | True            | True                    | True             |       0.0214363  | True                      |      3.68736e-05 | True                      |       3.19744e-14 |         2.01228e-16 |       3.90799e-14 |         8.09763e-18 |      0.00885653  |      3.29024e-14 |      0.000147412 |      0.000117609 | PASS_DIAGNOSTIC_PARITY | PASS_XTABOND2_PARITY |
| system_gmm_decomposition_controls | True                     | True                | True                       |         1.88738e-14 |       1.57383e-07 | PASS_PARAMETER_PARITY | True           | True                 | True                      | True                       | True                                   | False                              | PASS                | True        | True            | True                    | True             |       0.00639641 | True                      |      1.27905e-05 | True                      |       6.18172e-13 |         1.60028e-15 |       1.11555e-12 |         1.36372e-18 |      0.00745459  |      0.00108339  |      0.0226432   |      0.00638077  | PASS_DIAGNOSTIC_PARITY | PASS_XTABOND2_PARITY |

## Gates

- expected parameter sets: exact and unique; coefficients and standard errors: finite
- standard errors: strictly positive
- Stata and xtabond2 versions: exact match to the certification registry
- coefficient absolute differences: `<= 1e-06`
- Windmeijer standard-error relative differences: specification-specific
  tolerances recorded in `se_rel_tol`
- observations, groups, instruments, and overidentification degrees of freedom: exact
- Hansen/Sargan statistic and p-value absolute differences: `<= 1e-06`
- signed AR(1)/AR(2) z-statistic absolute differences: `<= 0.1`
- AR(1)/AR(2) p-value absolute differences: `<= 0.03`

Overall status passes only when both parameter and diagnostic gates pass.
Parity status means cross-software agreement on the maintained fixture; it does not
endorse instrument validity or the model specification. The Stata Hansen/Sargan
p-values and reject-at-0.05 flags are reported explicitly and are not parity gates.
SHA-256 hashes bind the certificate to the registry, fixture, do-file, and exact
native and Stata parameter and diagnostic exports. The Stata-reported date and time
are retained as informational metadata only and are not conformity gates.
