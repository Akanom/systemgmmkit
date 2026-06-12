# systemgmmkit Panel Econometrics Certification Report

Generated: `2026-06-12 06:12:14 UTC`

## Certification Summary

| Suite | Status | Test Path | Scope |
|---|---:|---|---|
| Conformance Suite | PASS | `tests/conformance` | Core API, diagnostics, reporting, and registry contracts. |
| Static Estimator Certification | PASS | `tests/parity/static` | FD, FE, RE, IV/2SLS certification contracts. |
| Difference GMM Expanded Certification | PASS | `tests/parity/gmm/test_difference_gmm_expanded_certification.py` | Balanced, unbalanced, missing periods, lag windows, collapse behavior. |
| System GMM Certification | PASS | `tests/parity/gmm/test_system_gmm_certification.py` | Balanced, unbalanced, missing periods, lag windows, collapse behavior, diagnostics contract. |

## Current Certification Position

- Static panel estimators have certification tests for FE, RE, IV/2SLS, and FD workflows.
- Difference GMM has expanded native certification coverage across balanced/unbalanced panels, missing periods, lag windows, and collapsed/uncollapsed instruments.
- System GMM has native certification coverage across the same structural scenarios, but remains labelled experimental until strict coefficient and standard-error parity against xtabond2 and pydynpd is completed.
- Windmeijer correction remains explicitly not certified unless separately implemented and benchmarked.

## Reviewer-Relevant Status

| Component | Reviewer Claim Allowed Now | Stronger Claim Still Needed |
|---|---|---|
| FE / RE / IV / FD | Implemented and certification-tested | Strict Stata/linearmodels parity for all SE variants |
| Difference GMM | Expanded native certification-tested | Full xtabond2/pydynpd parity table across benchmark specs |
| System GMM | Runs and passes structural certification | Strict xtabond2/pydynpd parity for coefficients, SEs, diagnostics, sample, and instruments |
| Diagnostics | Implemented and contract-tested | Numeric parity against reference implementations |

## Next Certification Milestone

Native System GMM strict parity against xtabond2 and pydynpd:

1. coefficient parity;
2. standard-error parity;
3. AR(1), AR(2), Hansen, Sargan, Diff-Hansen parity;
4. instrument-count parity;
5. exact estimation-sample parity.
