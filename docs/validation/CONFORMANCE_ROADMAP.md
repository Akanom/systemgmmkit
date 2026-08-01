# systemgmmkit Conformance Roadmap

## Existing benchmark spec names

The conformance suite keeps these dynamic-GMM benchmark names:

* `difference_gmm_baseline_controls`
* `system_gmm_baseline_controls`
* `system_gmm_no_controls`
* `system_gmm_three_way_controls`
* `system_gmm_three_way_no_controls`
* `system_gmm_decomposition_controls`
* `system_gmm_unbalanced_panel`
* `system_gmm_variable_missing`

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
| `system_gmm_unbalanced_panel` | `PASS_XTABOND2_PARITY` | Complete parameters, Windmeijer SEs, exact counts and sample keys, Hansen/Sargan, and signed AR diagnostics pass the aligned `xtabond2` gates. |
| `system_gmm_variable_missing` | `PASS_XTABOND2_PARITY` | Complete parameters, Windmeijer SEs, exact counts and sample keys, Hansen/Sargan, and signed AR diagnostics pass the aligned `xtabond2` gates. |
| `system_gmm_three_way_no_controls` | `EXPERIMENTAL_PARITY_PENDING` | No committed certification artifact currently supports this specification. |

`PASS_XTABOND2_PARITY` denotes numerical cross-software agreement on these
maintained fixtures; it does not establish instrument validity or endorse a
specification. Stata rejects both Hansen and Sargan at 5% for no-controls,
three-way-controls, decomposition, and variable-missing, while baseline and the
unbalanced-panel fixture do not. The unified certificate retains the exact
p-values and reject-at-0.05 flags.

The pending status intentionally retires an older unsupported AR-parity label: the
historical comparison artifact contained no `system_gmm_three_way_no_controls` row,
and the specification has never had a complete coefficient/SE/diagnostic certificate.

## Completed conformance work

The completed conformance base includes:

1. pooled OLS, one-way FE, two-way FE, RE, and panel IV / 2SLS alignment;
2. robust and clustered standard-error alignment on maintained static paths;
3. first-difference estimator support and benchmark alignment;
4. native Difference GMM benchmark parity and expanded structural coverage;
5. six-spec native System GMM coefficient and Windmeijer-SE parity;
6. exact observations, groups, instruments, and overidentification degrees of freedom;
7. Hansen and Sargan statistic and p-value parity at `1e-6` absolute tolerance;
8. signed AR(1)/AR(2) z-statistic parity at `0.10` absolute tolerance;
9. AR(1)/AR(2) p-value parity at `0.03` absolute tolerance;
10. fresh-current-engine numerical pytest guards and a machine-readable unified certificate;
11. exact native/Stata estimation-sample keys for the maintained unbalanced-panel
    and variable-missing designs;
12. one central registry for the six maintained System-GMM specifications, oracle,
    and numerical gates; and
13. LF-normalized canonical SHA-256 provenance for the registry, comparator,
    generators, controlled fixtures, generated Stata do-files, and exact native/Stata
    parameter, diagnostic, and declared sample exports.

## Static fixed-effects runtime boundary

The native fixed-effects backend now reports `native-within`. It estimates structural
slopes on a compact within-transformed design instead of constructing a full LSDV dummy
matrix for ordinary one-way and two-way FE fits. The old LSDV construction remains an
internal audit path and is used in tests to confirm slope equivalence, including an
unbalanced two-way panel case.

This is a runtime and memory-scaling improvement, not a broader validation claim.
Conformance language remains benchmark-specific and tied to the maintained static-panel
paths.

## Remaining validation-extension work

Future priorities are extensions beyond the current certified boundary:

1. generate evidence for `system_gmm_three_way_no_controls` or keep it outside the
   claimed suite;
2. extend unbalanced-panel and missing-data certification beyond the two maintained
   controlled designs;
3. add short-`T`, longer-`T`, and high-`N`, low-`T` certification designs;
4. add alternative lag-window and instrument-classification designs;
5. add Difference-in-Hansen certification where supported and applicable;
6. expand exact Stata-compatible option documentation and known non-equivalence cases;
7. broaden e(sample)-style sample tracking;
8. validate FOD-specific covariance and AR diagnostics against `xtdpdgmm`;
9. add reviewer-facing notebooks and graphical parity reporting; and
10. build a separately aligned `pydynpd` contract before publishing a cross-package
   speed ranking.

## Certification boundary

For the maintained System-GMM/`xtabond2` boundary only,
`artifacts/parity/xtabond2/system_gmm_certification_specs.json` is the sole
specification/oracle/tolerance registry and
`artifacts/parity/xtabond2/diagnostic_parity_certificate.csv` is the sole
numerical decision artifact. The path-free comparator attestation is historical-
log-derived; it discloses that the local log is uncommitted and that output/ado
hashes were observed when the attestation was generated.

Correct wording:

> `systemgmmkit` provides benchmark-specific conformance evidence for static panel estimators, panel IV / 2SLS, native Difference GMM, and native System GMM. On six maintained, aligned System GMM fixtures, the native estimator passes Stata `xtabond2` numerical-agreement gates for the complete expected parameter set, Windmeijer-corrected two-step standard errors, exact observations/groups/instruments/overidentification degrees of freedom, Hansen and Sargan diagnostics, and signed Arellano-Bond AR(1)/AR(2) diagnostics. The unbalanced-panel and variable-missing fixtures also pass exact estimation-sample-key gates. This evidence does not imply universal Stata identity, instrument validity, or specification endorsement across other data or specifications.

Stata `xtabond2` is the formal System GMM certification oracle. `pydynpd` is an
optional execution backend and auxiliary comparator. Unaligned `pydynpd` results
must not be used as parity or speed-ranking evidence.
