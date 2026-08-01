# systemgmmkit Panel Econometrics Certification Report

Generated: `2026-08-01 06:40:31 UTC`
Certification registry: `artifacts/parity/xtabond2/system_gmm_certification_specs.json`
Registry scope: the registry and unified certificate are authoritative only for the maintained System-GMM/xtabond2 row below. Other rows identify separate test contracts; their execution status is reported by CI, not hardcoded here.

## Certification Summary

| Suite | Status | Test Path | Scope |
|---|---:|---|---|
| Conformance Suite | TEST_CONTRACT | `tests/conformance` | Core API, diagnostics, reporting, and registry contracts. |
| Static Estimator Certification | TEST_CONTRACT | `tests/parity/static` | FD, FE, RE, IV/2SLS certification contracts. |
| Difference GMM Expanded Certification | TEST_CONTRACT | `tests/parity/gmm/test_difference_gmm_expanded_certification.py` | Balanced, unbalanced, missing periods, lag windows, collapse behavior. |
| System GMM Structural Contract | TEST_CONTRACT | `tests/parity/gmm/test_system_gmm_certification.py` | Balanced, unbalanced, missing periods, lag windows, collapse behavior, and diagnostic availability. |
| System GMM xtabond2 Unified Parity | PASS | `artifacts/parity/xtabond2/diagnostic_parity_certificate.csv` | 6 aligned specifications: parameters, Windmeijer SEs, exact counts, Hansen/Sargan, and signed AR diagnostics. |

## Current Certification Position

- Maintained System GMM certification specifications: `system_gmm_baseline_controls`, `system_gmm_no_controls`, `system_gmm_three_way_controls`, `system_gmm_decomposition_controls`, `system_gmm_unbalanced_panel`, `system_gmm_variable_missing`.
- Static panel estimators have certification tests for FE, RE, IV/2SLS, and FD workflows.
- Difference GMM has expanded native certification coverage across balanced/unbalanced panels, missing periods, lag windows, and collapsed/uncollapsed instruments.
- System GMM has benchmark-specific xtabond2 parity for complete parameter sets, Windmeijer standard errors, exact structural counts, Hansen/Sargan diagnostics, and signed AR diagnostics on 6 aligned specifications.
- The numerical gate reads raw native and Stata artifacts and records LF-normalized canonical SHA-256 digests for the registry, comparator, generators, fixtures, do-files, parameter exports, and diagnostic exports.
- Comparator identity is supplied by a path-free attestation derived from the bounded completed log and cross-checked against metadata embedded in every tracked Stata diagnostic export. Its local source log is intentionally uncommitted; the attestation binds the exact outputs and installed ado observed at generation.
- Stata xtabond2 is the formal certification oracle; pydynpd is an optional execution backend and auxiliary comparator.
- `PASS_XTABOND2_PARITY` means numerical cross-software agreement on these fixtures; it does not establish instrument validity or endorse a specification.

### Stata overidentification evidence (not a parity gate)

| Specification | Hansen p | Reject at 0.05 | Sargan p | Reject at 0.05 |
|---|---:|---:|---:|---:|
| `system_gmm_baseline_controls` | 0.15998017 | False | 0.087915465 | False |
| `system_gmm_no_controls` | 0.023561207 | True | 0.0056798715 | True |
| `system_gmm_three_way_controls` | 0.021436332 | True | 3.6873565e-05 | True |
| `system_gmm_decomposition_controls` | 0.0063964056 | True | 1.2790481e-05 | True |
| `system_gmm_unbalanced_panel` | 0.23239508 | False | 0.29722285 | False |
| `system_gmm_variable_missing` | 0.011506669 | True | 0.000783778 | True |

Raw p-values and rejection flags are generated from the same recomputed certificate rows.

## Reviewer-Relevant Status

| Component | Reviewer Claim Allowed Now | Stronger Claim Still Needed |
|---|---|---|
| FE / RE / IV / FD | Implemented and certification-tested | Strict Stata/linearmodels parity for all SE variants |
| Difference GMM | Expanded native certification-tested | Additional aligned xtabond2 specifications |
| System GMM | 6-spec benchmark-specific xtabond2 estimation and diagnostic parity | Broader data/specification coverage |
| Diagnostics | 6-spec Hansen/Sargan and signed AR numerical parity | Difference-in-Hansen and broader designs |

## Next Certification Milestone

Extend the current System GMM certification boundary:

1. generate and register evidence for `system_gmm_three_way_no_controls`, or keep it explicitly outside the certified boundary;
2. add short-T, longer-T, and high-N/low-T aligned designs;
3. certify applicable Difference-in-Hansen diagnostics;
4. add alternative lag and instrument-classification designs;
5. create a separately aligned pydynpd contract before speed ranking.

A pydynpd parity or speed comparison is a separate milestone and requires the full alignment gate to pass first.
