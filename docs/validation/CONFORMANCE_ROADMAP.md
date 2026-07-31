# systemgmmkit Conformance Roadmap

## Existing benchmark spec names

The conformance suite keeps these dynamic-GMM benchmark names:

* `difference_gmm_baseline_controls`
* `system_gmm_baseline_controls`
* `system_gmm_no_controls`
* `system_gmm_three_way_controls`
* `system_gmm_three_way_no_controls`
* `system_gmm_decomposition_controls`

## Current certification language

| Area / Spec | Current status | Interpretation |
| --- | --- | --- |
| Pooled OLS, FE, RE, Panel IV / 2SLS | `PASS_ALIGNED` | Implemented and aligned on maintained static-panel benchmark paths. |
| Robust and clustered standard errors | `PASS_ALIGNED` | Aligned for the tested static-panel benchmark paths. |
| `difference_gmm_baseline_controls` | `PASS_PARITY` / `PASS_STRICT` | Native Difference GMM passes its maintained strict contract. |
| `system_gmm_baseline_controls` | `PASS_XTABOND2_PARITY` | Complete parameters, Windmeijer SEs, counts, Hansen/Sargan, and signed AR diagnostics pass the aligned `xtabond2` gates. |
| `system_gmm_no_controls` | `PASS_XTABOND2_PARITY` | Complete parameters, Windmeijer SEs, counts, Hansen/Sargan, and signed AR diagnostics pass the aligned `xtabond2` gates. |
| `system_gmm_three_way_controls` | `PASS_XTABOND2_PARITY` | Complete parameters, Windmeijer SEs, counts, Hansen/Sargan, and signed AR diagnostics pass the aligned `xtabond2` gates. |
| `system_gmm_decomposition_controls` | `PASS_XTABOND2_PARITY` | Complete parameters, Windmeijer SEs, counts, Hansen/Sargan, and signed AR diagnostics pass the aligned `xtabond2` gates. |
| `system_gmm_three_way_no_controls` | `EXPERIMENTAL_PARITY_PENDING` | No committed certification artifact currently supports this specification. |

The pending status intentionally retires an older unsupported AR-parity label: the
historical comparison artifact contained no `system_gmm_three_way_no_controls` row,
and the specification has never had a complete coefficient/SE/diagnostic certificate.

## Completed conformance work

The completed conformance base includes:

1. pooled OLS, one-way FE, two-way FE, RE, and panel IV / 2SLS alignment;
2. robust and clustered standard-error alignment on maintained static paths;
3. first-difference estimator support and benchmark alignment;
4. native Difference GMM benchmark parity and expanded structural coverage;
5. four-spec native System GMM coefficient and Windmeijer-SE parity;
6. exact observations, groups, instruments, and overidentification degrees of freedom;
7. Hansen and Sargan statistic and p-value parity at `1e-6` absolute tolerance;
8. signed AR(1)/AR(2) z-statistic parity at `0.10` absolute tolerance;
9. AR(1)/AR(2) p-value parity at `0.03` absolute tolerance;
10. fresh-current-engine numerical pytest guards and a machine-readable unified certificate; and
11. SHA-256 provenance for controlled fixtures, generated Stata do-files, and exact
    native/Stata parameter and diagnostic exports.

## Remaining validation-extension work

Future priorities are extensions beyond the current certified boundary:

1. generate evidence for `system_gmm_three_way_no_controls` or keep it outside the
   claimed suite;
2. add unbalanced-panel, missing-data, short-`T`, longer-`T`, and high-`N`, low-`T`
   certification designs;
3. add alternative lag-window and instrument-classification designs;
4. add Difference-in-Hansen certification where supported and applicable;
5. expand exact Stata-compatible option documentation and known non-equivalence cases;
6. broaden e(sample)-style sample tracking;
7. validate FOD-specific covariance and AR diagnostics against `xtdpdgmm`;
8. add reviewer-facing notebooks and graphical parity reporting; and
9. build a separately aligned `pydynpd` contract before publishing a cross-package
   speed ranking.

## Certification boundary

Correct wording:

> `systemgmmkit` provides benchmark-specific conformance evidence for static panel estimators, panel IV / 2SLS, native Difference GMM, and native System GMM. On four maintained, aligned System GMM fixtures, the native estimator passes Stata `xtabond2` gates for the complete expected parameter set, Windmeijer-corrected two-step standard errors, exact observations/groups/instruments/overidentification degrees of freedom, Hansen and Sargan diagnostics, and signed Arellano-Bond AR(1)/AR(2) diagnostics. This evidence does not imply universal Stata identity across other data or specifications.

Stata `xtabond2` is the formal System GMM certification oracle. `pydynpd` is an
optional execution backend and auxiliary comparator. Unaligned `pydynpd` results
must not be used as parity or speed-ranking evidence.
