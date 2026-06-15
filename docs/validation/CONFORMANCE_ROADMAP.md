# systemgmmkit Conformance Roadmap

## Existing benchmark spec names

The conformance suite keeps the existing dynamic-GMM benchmark names:

* `difference_gmm_baseline_controls`
* `system_gmm_baseline_controls`
* `system_gmm_three_way_controls`
* `system_gmm_three_way_no_controls`
* `system_gmm_decomposition_controls`

## Current certification language

| Area / Spec                         | Current status                             | Interpretation                                                                                                                                                                                                                                     |
| ----------------------------------- | ------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Pooled OLS                          | `PASS_ALIGNED`                             | Pooled OLS is implemented and aligned against the maintained reference expectation for the tested benchmark.                                                                                                                                       |
| One-way Fixed Effects               | `PASS_ALIGNED`                             | One-way FE is implemented and aligned against the maintained reference expectation for the tested benchmark.                                                                                                                                       |
| Two-way Fixed Effects               | `PASS_ALIGNED`                             | Two-way FE is implemented and aligned against the maintained reference expectation for the tested benchmark.                                                                                                                                       |
| Random Effects                      | `PASS_ALIGNED`                             | Random Effects is implemented and aligned against the maintained reference expectation for the tested benchmark.                                                                                                                                   |
| Panel IV / 2SLS                     | `PASS_ALIGNED`                             | Panel IV / 2SLS is implemented and aligned against the maintained reference expectation for the tested benchmark.                                                                                                                                  |
| Robust standard errors              | `PASS_ALIGNED`                             | Robust covariance behavior is implemented and aligned for the tested static-panel benchmark paths.                                                                                                                                                 |
| Clustered standard errors           | `PASS_ALIGNED`                             | Clustered covariance behavior is implemented and aligned for the tested static-panel benchmark paths.                                                                                                                                              |
| `difference_gmm_baseline_controls`  | `PASS_PARITY` / `PASS_STRICT`              | Native Difference GMM passes the maintained benchmark parity check within numerical tolerance.                                                                                                                                                     |
| `system_gmm_baseline_controls`      | `PASS_STRICT_XTABOND2_SYSTEM_GMM_BASELINE` | Native System GMM passes the maintained strict `xtabond2` baseline benchmark for sample size, instrument count, coefficients, Hansen diagnostics, Windmeijer-corrected two-step standard errors, and signed AR(1)/AR(2) diagnostics with p-values. |
| `system_gmm_three_way_controls`     | `PASS_SYSTEM_GMM_AR_PARITY`                | Multi-specification System GMM AR diagnostic parity passed under the maintained validation thresholds.                                                                                                                                             |
| `system_gmm_three_way_no_controls`  | `PASS_SYSTEM_GMM_AR_PARITY`                | Multi-specification System GMM AR diagnostic parity passed under the maintained validation thresholds.                                                                                                                                             |
| `system_gmm_decomposition_controls` | `PASS_SYSTEM_GMM_AR_PARITY`                | Multi-specification System GMM AR diagnostic parity passed under the maintained validation thresholds.                                                                                                                                             |

## Completed conformance work

The following items are now part of the completed or substantially validated conformance base:

1. pooled OLS alignment;
2. one-way fixed-effects alignment;
3. two-way fixed-effects alignment;
4. random-effects alignment;
5. panel IV / 2SLS alignment;
6. robust standard-error alignment for the maintained static-panel benchmark paths;
7. clustered standard-error alignment for the maintained static-panel benchmark paths;
8. first-difference estimator support;
9. first-difference estimator parity/alignment on the maintained benchmark;
10. native Difference GMM benchmark parity;
11. expanded Difference GMM certification on the maintained benchmark suite;
12. native System GMM strict baseline parity against Stata `xtabond2`;
13. System GMM instrument-count parity for the maintained benchmark;
14. System GMM coefficient parity for the maintained benchmark;
15. System GMM Hansen diagnostic parity for the maintained benchmark;
16. System GMM Windmeijer-corrected two-step standard-error parity for the maintained benchmark;
17. System GMM signed AR(1)/AR(2) diagnostic parity with p-values for the maintained benchmark;
18. multi-specification System GMM AR diagnostic parity across baseline, no-controls, three-way interaction, and decomposition specifications;
19. automated parity report generation for the maintained benchmark artifacts;
20. reviewer-facing parity artifacts for the maintained `xtabond2` validation suite.

## Remaining validation-extension work

The remaining work is now focused on extending the certification boundary, not on establishing the core estimator set.

Future validation-extension priorities include:

1. additional unbalanced-panel and missing-data designs beyond the maintained benchmark suite;
2. additional short-`T`, longer-`T`, and high-`N`, low-`T` examples;
3. additional lag-window combinations and instrument-classification designs;
4. additional Sargan and Difference-in-Hansen reporting where supported and applicable;
5. explicit documentation of exact Stata-compatible option combinations;
6. documentation of known non-equivalence cases, especially where Stata, backend, and native conventions differ;
7. broader e(sample)-style sample-tracking diagnostics;
8. FOD-specific validation against `xtdpdgmm`, especially FOD Windmeijer covariance and FOD AR(1)/AR(2) diagnostic parity;
9. graphical parity reporting through `universal-output-hub`;
10. additional reviewer-facing notebooks showing the full parity workflow end to end.

## Certification boundary

The package should be described as having benchmark-specific certification and alignment, not universal identity with every external software implementation.

Correct wording:

> `systemgmmkit` provides benchmark-specific conformance evidence for static panel estimators, panel IV / 2SLS, native Difference GMM, and native System GMM. Pooled OLS, fixed effects, two-way fixed effects, random effects, panel IV / 2SLS, robust covariance, and clustered covariance are aligned on the maintained static-panel benchmark paths. The maintained native System GMM benchmark is certified against Stata `xtabond2` for sample size, instrument count, coefficients, Hansen diagnostics, Windmeijer-corrected two-step standard errors, and signed Arellano-Bond AR diagnostics. Broader validation across additional panel designs, option combinations, and implementation-dependent configurations remains an extension priority.

This roadmap protects the package from overclaiming while making clear that the core estimator set and the maintained native System GMM parity milestone have already been reached.
