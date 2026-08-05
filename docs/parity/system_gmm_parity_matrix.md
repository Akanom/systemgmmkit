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

The current certificate recomputes coefficient, standard-error, count, sample, and
diagnostic comparisons from raw native and Stata artifacts. It covers six maintained, aligned,
collapsed, two-step System GMM specifications.

| Spec ID | Coefficients / Windmeijer SEs | N / groups / instruments / df | Exact sample keys | Hansen / Sargan | Signed AR(1) / AR(2) | Status |
| --- | --- | --- | --- | --- | --- | --- |
| `system_gmm_baseline_controls` | Pass | Exact | Not separately exported | Pass | Pass | `PASS_XTABOND2_PARITY` |
| `system_gmm_no_controls` | Pass | Exact | Not separately exported | Pass | Pass | `PASS_XTABOND2_PARITY` |
| `system_gmm_three_way_controls` | Pass | Exact | Not separately exported | Pass | Pass | `PASS_XTABOND2_PARITY` |
| `system_gmm_decomposition_controls` | Pass | Exact | Not separately exported | Pass | Pass | `PASS_XTABOND2_PARITY` |
| `system_gmm_unbalanced_panel` | Pass | Exact | Pass | Pass | Pass | `PASS_XTABOND2_PARITY` |
| `system_gmm_variable_missing` | Pass | Exact | Pass | Pass | Pass | `PASS_XTABOND2_PARITY` |
| `system_gmm_three_way_no_controls` | No committed certificate | Not certified | Not certified | Not certified | Not certified | `EXPERIMENTAL_PARITY_PENDING` |

Here, “Pass” for Hansen, Sargan, and AR means numerical cross-software
agreement, not instrument validity or specification endorsement. Stata rejects
both Hansen and Sargan tests at 5% for no-controls (`0.02356` / `0.00568`),
three-way-controls (`0.02144` / `0.0000369`), decomposition (`0.00640` /
`0.0000128`), and variable-missing (`0.01151` / `0.0007838`); baseline
(`0.15998` / `0.08792`) and unbalanced-panel (`0.23240` / `0.29722`) do not.
Raw p-values and reject-at-0.05 flags are retained in the unified certificate.

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
| Estimation-sample entity/time keys | Exact for specifications that declare sample exports (currently the unbalanced-panel and variable-missing fixtures) |
| Hansen / Sargan statistic and p-value | `max_abs_diff <= 1e-6` |
| Signed AR(1) / AR(2) z-statistic | `max_abs_diff <= 0.10` |
| AR(1) / AR(2) p-value | `max_abs_diff <= 0.03` |

The largest observed six-spec signed-AR differences are approximately `0.02264`
for z and `0.00638` for p. The Stata-reported clock is informational and is never a
gate. LF-normalized canonical SHA-256 digests of the registry, comparator,
generators, support files, fixtures, generated do-files, native/Stata parameter
exports, native/Stata diagnostic exports, and declared sample exports are recorded
in the machine-readable certificate.

## Evidence and reproduction

- Unified parameter-and-diagnostic certificate (filename retained for compatibility):
  `artifacts/parity/xtabond2/diagnostic_parity_certificate.csv`
- Central machine-readable specification and gate registry:
  `artifacts/parity/xtabond2/system_gmm_certification_specs.json`
- Sanitized comparator provenance attestation:
  `artifacts/parity/xtabond2/xtabond2_comparator_provenance.json`
- Baseline legacy compatibility projection (not an independent authority):
  `artifacts/parity/xtabond2/xtabond2_system_gmm_parity_certificate.csv`
- Raw per-spec evidence:
  `artifacts/parity/xtabond2/specs/`
- Fresh-current-engine numerical pytest guard:
  `tests/test_xtabond2_system_gmm_authoritative_gate.py`
- Portable Stata driver:
  `scripts/parity/rerun_xtabond2_certification.do`

The unified certificate is the sole numerical certification authority. The legacy
baseline file is generated by selecting its baseline row and introduces no separate
terms, tolerances, or pass/fail decision.

The registry is the sole specification/oracle/tolerance source for these six
System-GMM/`xtabond2` fixtures. The current provenance attestation is derived from
allowlisted fields in a completed local Stata log and hash-bound tracked exports.
That path-bearing log remains uncommitted; the attestation discloses how its
tracked-output and installed-ado hashes were bound at generation time.

Run the native comparisons from the repository root, then run the Stata driver with
the repository root as its argument. The generated do-files pin Stata 17 syntax and
make `eq(both)`, level-equation IV scope, two-step robust estimation, and collapsed
instruments explicit.

Exact regeneration sequence (run Python commands from the repository root):

```text
python scripts/parity/build_xtabond2_system_gmm_do.py
python scripts/parity/build_xtabond2_system_gmm_no_controls_do.py
python scripts/parity/build_xtabond2_system_gmm_three_way_controls_do.py
python scripts/parity/build_xtabond2_system_gmm_decomposition_controls_do.py
python scripts/parity/build_xtabond2_unbalanced_missing_extension.py
python scripts/parity/run_native_unbalanced_missing_extension.py
python scripts/parity/build_xtabond2_certification_driver.py
```

Save any open Stata work first because the generated driver begins with `clear all`,
then run this inside Stata:

```stata
do "scripts/parity/rerun_xtabond2_certification.do" "."
```

After Stata completes, rebuild the sanitized attestation and all derived claims:

```text
python scripts/parity/build_xtabond2_comparator_provenance.py --log artifacts/parity/xtabond2/xtabond2_certification_rerun.log --ado <path-to-installed-xtabond2.ado>
python scripts/parity/compare_xtabond2_ar_diagnostics.py
python scripts/parity/apply_xtabond2_system_gmm_certificate.py
python scripts/parity/build_certification_report.py
python -m pytest tests/test_xtabond2_system_gmm_authoritative_gate.py tests/test_system_gmm_certification_registry.py -q
```

## `pydynpd` interpretation

Archived `pydynpd` rows are classified as `REVIEW`, not as certificates or parity
failures, because those workloads did not establish identical effective samples and
construction conventions. A shared estimator label is insufficient. A future
`pydynpd` parity or speed comparison must first pass the same alignment contract and
must use a separate evidence artifact.

## Remaining work

1. Add a committed certificate for `system_gmm_three_way_no_controls` or keep it
   outside the certified suite.
2. Extend unbalanced-panel and missing-data certification beyond the two maintained
   controlled designs.
3. Extend certification to alternative lag windows and instrument layouts.
4. Build a separately aligned `pydynpd` contract before publishing any cross-package
   speed ranking.
