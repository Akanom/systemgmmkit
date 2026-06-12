# Roadmap

## Current released state

### v0.5.0 — Native Windmeijer parity release

Completed:

- Native Windmeijer-corrected two-step covariance support for native dynamic-panel GMM.
- Native System GMM benchmark certification against Stata `xtabond2` `e(V)`.
- Uncorrected clustered two-step covariance benchmark preserved through `SYSTEMGMMKIT_NATIVE_WINDMEIJER=0`.
- Ruff, pytest, GitHub CI, release workflow, and PyPI publishing confirmed.

## Completed System GMM parity certification

The broader System GMM parity matrix has now been expanded beyond the original baseline benchmark.

Certified specifications:

| Specification | Purpose | Status |
| --- | --- | --- |
| `system_gmm_baseline_controls` | Baseline collapsed two-step System GMM benchmark. | Certified |
| `system_gmm_no_controls` | Minimal System GMM construction and covariance behavior. | Certified |
| `system_gmm_three_way_controls` | Interaction-heavy System GMM design. | Certified |
| `system_gmm_decomposition_controls` | Multi-regressor decomposition-style System GMM design. | Certified |
| `difference_gmm_baseline_controls` | Existing Difference GMM guard. | Certified |

Certified quantities for System GMM include:

- coefficient parity;
- Windmeijer-corrected two-step standard-error parity;
- Hansen p-value parity;
- number of instruments;
- number of observations;
- covariance type;
- committed benchmark artifacts;
- automated pytest guards.

## Remaining validation work

High-priority remaining items:

- Certify AR(1)/AR(2) diagnostic parity.
- Add unbalanced-panel System GMM parity tests.
- Add missing-data parity tests.
- Add alternative lag-window parity tests.
- Add alternative instrument-classification parity tests.
- Prepare reviewer-facing software-paper evidence tables.

## Release discipline

No universal Stata-equivalence claim should be made. All parity statements should remain benchmark-specific and tied to committed artifacts, comparison scripts, pytest guards, and passing CI.
