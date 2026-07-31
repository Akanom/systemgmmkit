# systemgmmkit Panel Econometrics Certification Report

Generated: `2026-07-31 00:27:24 UTC`

## Certification Summary

| Suite | Status | Test Path | Scope |
|---|---:|---|---|
| Conformance Suite | PASS | `tests/conformance` | Core API, diagnostics, reporting, and registry contracts. |
| Static Estimator Certification | PASS | `tests/parity/static` | FD, FE, RE, IV/2SLS certification contracts. |
| Difference GMM Expanded Certification | PASS | `tests/parity/gmm/test_difference_gmm_expanded_certification.py` | Balanced, unbalanced, missing periods, lag windows, collapse behavior. |
| System GMM Structural Contract | CONTRACT_PASS | `tests/parity/gmm/test_system_gmm_certification.py` | Balanced, unbalanced, missing periods, lag windows, collapse behavior, and diagnostic availability. |
| System GMM xtabond2 Unified Parity | PASS | `artifacts/parity/xtabond2/diagnostic_parity_certificate.csv` | Four aligned specifications: parameters, Windmeijer SEs, exact counts, Hansen/Sargan, and signed AR diagnostics. |

## Current Certification Position

- Static panel estimators have certification tests for FE, RE, IV/2SLS, and FD workflows.
- Difference GMM has expanded native certification coverage across balanced/unbalanced panels, missing periods, lag windows, and collapsed/uncollapsed instruments.
- System GMM has benchmark-specific xtabond2 parity for complete parameter sets, Windmeijer standard errors, exact structural counts, Hansen/Sargan diagnostics, and signed AR diagnostics on four aligned specifications.
- The numerical gate reads raw native and Stata artifacts and records fixture, do-file, parameter-export, and diagnostic-export SHA-256 hashes.
- Stata xtabond2 is the formal certification oracle; pydynpd is an optional execution backend and auxiliary comparator.

## Reviewer-Relevant Status

| Component | Reviewer Claim Allowed Now | Stronger Claim Still Needed |
|---|---|---|
| FE / RE / IV / FD | Implemented and certification-tested | Strict Stata/linearmodels parity for all SE variants |
| Difference GMM | Expanded native certification-tested | Additional aligned xtabond2 specifications |
| System GMM | Four-spec benchmark-specific xtabond2 estimation and diagnostic parity | Broader data/specification coverage |
| Diagnostics | Four-spec Hansen/Sargan and signed AR numerical parity | Difference-in-Hansen and broader designs |

## Next Certification Milestone

Extend the current System GMM certification boundary:

1. add or explicitly exclude `system_gmm_three_way_no_controls`;
2. add unbalanced-panel and missing-data fixtures;
3. certify applicable Difference-in-Hansen diagnostics;
4. add alternative lag and instrument-classification designs;
5. create a separately aligned pydynpd contract before speed ranking.

A pydynpd parity or speed comparison is a separate milestone and requires the full alignment gate to pass first.
