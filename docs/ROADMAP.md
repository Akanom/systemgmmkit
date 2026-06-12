# Roadmap

## Current released state

### v0.5.0 — Native Windmeijer parity release

Completed:

- Native Windmeijer-corrected two-step covariance support for native dynamic-panel GMM.
- Native System GMM benchmark certification against Stata `xtabond2` `e(V)` on the current collapsed two-step benchmark.
- Baseline parity documented for coefficients, raw residual moments (`Z'u`), group-scaled two-step weighting matrix (`A2 / n_groups`), Hansen J, and Windmeijer-corrected standard errors.
- Uncorrected clustered two-step covariance benchmark preserved through `SYSTEMGMMKIT_NATIVE_WINDMEIJER=0`.
- Ruff, pytest, GitHub CI, release workflow, and PyPI publishing confirmed.

## Next milestone: broader System GMM parity matrix

The next validation milestone is to extend native System GMM parity coverage beyond the single certified benchmark.

The goal is not to claim universal Stata identity. The goal is to build a transparent, repeatable, benchmark-specific parity matrix across several System GMM specifications.

### Priority specifications

| Specification | Purpose | Priority |
| --- | --- | --- |
| `system_gmm_baseline_controls` | Maintain and extend the current certified benchmark. | P0 |
| `system_gmm_no_controls` | Validate minimal System GMM construction and covariance behavior. | P0 |
| `system_gmm_three_way_controls` | Validate interaction-heavy specifications. | P1 |
| `system_gmm_decomposition_controls` | Validate multi-regressor decomposition-style specifications. | P1 |
| `difference_gmm_baseline_controls` | Preserve strict Difference GMM regression guard. | P1 |

### Validation dimensions

Each specification should report:

- coefficient parity;
- standard-error parity;
- covariance type;
- Hansen J;
- AR(1) and AR(2);
- number of instruments;
- number of observations;
- number of groups;
- sample identity;
- backend / Stata command assumptions.

### Release discipline

No broader certification claim should be added to the README until a specification has:

- a committed Stata benchmark artifact;
- a native benchmark artifact;
- an automated comparison script;
- a pytest regression guard;
- documented tolerance thresholds;
- passing GitHub CI.
