# System GMM parity matrix

## Purpose

This document defines the current native `systemgmmkit` System GMM certification
boundary against Stata `xtabond2`. Every claim is benchmark-specific; none implies
universal identity across datasets, lag windows, instruments, transformations,
missing-data patterns, covariance assumptions, or finite-sample corrections.

## Reference and alignment roles

- Stata `xtabond2` is the formal certification oracle.
- `pydynpd` is an optional execution backend and auxiliary comparator. It is not
  part of the formal native System GMM certificate.
- Native reference and accelerated preparation engines have a separate exact-result
  identity contract inside SystemGMMKit.

External results are comparable only after aligning the effective sample, equations,
lag semantics, equation-specific instruments, collapse behavior, constant and time
dummy treatment, estimation steps, finite-sample scaling, Windmeijer treatment, and
covariance normalization. Unaligned results must not support parity or speed rankings.

## Authoritative certification scope

The current certificate recomputes coefficient, standard-error, count, and diagnostic
comparisons from raw native and Stata artifacts. It covers four aligned, collapsed,
two-step System GMM specifications.

| Spec ID | Coefficients / Windmeijer SEs | N / groups / instruments / df | Hansen / Sargan | Signed AR(1) / AR(2) | Status |
| --- | --- | --- | --- | --- | --- |
| `system_gmm_baseline_controls` | Pass | Exact | Pass | Pass | `PASS_XTABOND2_PARITY` |
| `system_gmm_no_controls` | Pass | Exact | Pass | Pass | `PASS_XTABOND2_PARITY` |
| `system_gmm_three_way_controls` | Pass | Exact | Pass | Pass | `PASS_XTABOND2_PARITY` |
| `system_gmm_decomposition_controls` | Pass | Exact | Pass | Pass | `PASS_XTABOND2_PARITY` |
| `system_gmm_three_way_no_controls` | No committed certificate | Not certified | Not certified | Not certified | `EXPERIMENTAL_PARITY_PENDING` |

Difference GMM has a separate strict certificate and is not represented by the
System GMM unified certificate.

An older roadmap labeled `system_gmm_three_way_no_controls` as an AR-parity pass,
but the corresponding historical comparison CSV had no row for that specification
and its conformance test still declared it pending. That unsupported label is not
treated as certification evidence.

## Numerical gates

| Object | Gate |
| --- | --- |
| Expected parameter set | Exact; unmatched native or Stata terms fail |
| Coefficients | `max_abs_diff <= 1e-6` |
| Windmeijer standard errors | Specification-specific relative tolerance from `1e-3` to `1e-6` |
| Observations, groups, instruments, overidentification df | Exact |
| Hansen / Sargan statistic and p-value | `max_abs_diff <= 1e-6` |
| Signed AR(1) / AR(2) z-statistic | `max_abs_diff <= 0.10` |
| AR(1) / AR(2) p-value | `max_abs_diff <= 0.03` |

The largest observed four-spec signed-AR differences are approximately `0.02264`
for z and `0.00638` for p. The Stata-reported clock is informational and is never a
gate. SHA-256 hashes of each fixture, generated do-file, native/Stata parameter
export, and native/Stata diagnostic export are recorded in the machine-readable
certificate.

## Evidence and reproduction

- Unified parameter-and-diagnostic certificate (filename retained for compatibility):
  `artifacts/parity/xtabond2/diagnostic_parity_certificate.csv`
- Baseline coefficient/SE legacy certificate:
  `artifacts/parity/xtabond2/xtabond2_system_gmm_parity_certificate.csv`
- Raw per-spec evidence:
  `artifacts/parity/xtabond2/specs/`
- Fresh-current-engine numerical pytest guard:
  `tests/test_xtabond2_system_gmm_authoritative_gate.py`
- Portable Stata driver:
  `scripts/parity/rerun_xtabond2_certification.do`

Run the native comparisons from the repository root, then run the Stata driver with
the repository root as its argument. The generated do-files pin Stata 17 syntax and
make `eq(both)`, level-equation IV scope, two-step robust estimation, and collapsed
instruments explicit.

## `pydynpd` interpretation

Archived `pydynpd` rows are classified as `REVIEW`, not as certificates or parity
failures, because those workloads did not establish identical effective samples and
construction conventions. A shared estimator label is insufficient. A future
`pydynpd` parity or speed comparison must first pass the same alignment contract and
must use a separate evidence artifact.

## Remaining work

1. Add a committed certificate for `system_gmm_three_way_no_controls` or keep it
   outside the certified suite.
2. Extend certification to unbalanced panels, missing data, alternative lag windows,
   and alternative instrument layouts.
3. Build a separately aligned `pydynpd` contract before publishing any cross-package
   speed ranking.
