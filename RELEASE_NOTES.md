# systemgmmkit 1.0.5 Release Notes

## First-difference Difference GMM parity correction

Version `1.0.5` corrects the native collapsed, first-difference, two-step
Difference-GMM path. Version `1.0.4` incorrectly used the homoskedastic 2SLS
first-step weight `(Z'Z)^-1` instead of the Arellano--Bond transformed-error
weight `(sum_i Z_i' H_i Z_i)^-1`. That changed first-step residuals and therefore
propagated into two-step coefficients, covariance, and diagnostics.

The release also corrects the two-step Hansen criterion, the first-step Sargan
normalization, the signed AR diagnostic denominator, and the Windmeijer
covariance construction for this bounded path. The FD covariance now follows
the matrix construction in `xtabond2` 3.7.2 directly. The existing System-GMM
and FOD Difference-GMM paths remain separate.

Parity was rechecked against unchanged Stata 17 IC `xtabond2` 3.7.2 exports for
balanced, unbalanced, and variable-missing panels. All three fixtures pass exact
parameter, semantic-moment, count, and entity-time sample-key identities and
the registered numerical gates for coefficients, Windmeijer covariance, A2,
Z'e2, Hansen, Sargan, and signed AR(1)/AR(2) diagnostics. This is bounded
numerical agreement, not universal Stata identity or evidence of instrument
validity.

Install the corrected release with:

```bash
python -m pip install --upgrade systemgmmkit==1.0.5
```

---

# systemgmmkit 1.0.4 Release Notes

## PyPI publication correction

Version `1.0.4` contains the Kaggle import hardening and fixed-decimal table
formatting introduced in the `1.0.3` source release. The `1.0.3` trusted
publication workflow stopped before its PyPI upload because the direct
wheel-archive import check ran in the clean build environment before NumPy and
the other runtime dependencies were installed. PyPI therefore remained at
`1.0.2`.

The archive check now runs in the isolated wheel smoke environment after the
exact wheel and its dependencies are installed. It also verifies that Python
loaded `systemgmmkit` from the wheel archive path, not from the extracted
installation. The installed-wheel and installed-sdist smoke tests remain
unchanged.

No estimator code, numerical result, or certification claim differs from the
tested `1.0.3` source. Install the corrected PyPI release with:

```bash
python -m pip install --upgrade systemgmmkit==1.0.4
```

---

# systemgmmkit 1.0.3 Release Notes

## Kaggle and distribution-import reliability

Version `1.0.3` makes `systemgmmkit.estimators` an explicit regular Python
subpackage. The previous wheel installed correctly through ordinary `pip`
extraction, but direct wheel/archive imports could fail with
`ModuleNotFoundError: No module named 'systemgmmkit.estimators'` because the
subpackage depended on implicit namespace discovery. The explicit package
boundary removes that ambiguity without changing estimator behavior or the
stable public API.

The Kaggle/Colab quickstart now installs the exact package and Universal Output
Hub versions while allowing `pip` to add missing core dependencies. Satisfied
scientific dependencies are retained through `--upgrade-strategy
only-if-needed`. The release gate checks source-tree imports, the built wheel as
an archive, an isolated installed wheel, an isolated installed sdist, and the
notebook installation contract before publication.

Public result Markdown and regression-table exports now use fixed numeric
precision. With the default four digits, a displayed zero p-value is rendered
as `0.0000` rather than `0`, and the Kaggle quickstart applies the same rule to
its on-screen and exported tables. Raw result objects retain numeric p-values;
this is a presentation-only change.

No estimator algebra, coefficients, covariance matrices, standard errors,
diagnostics, or maintained cross-software certification claims change in this
release.

Install this release with:

```bash
python -m pip install --upgrade systemgmmkit==1.0.3
```

---

# systemgmmkit 1.0.2 Release Notes

## Native GMM numerical-health surface

Version `1.0.2` adds three read-only fields to `NativeGMMResult`:
`normal_matrix_rank`, `normal_matrix_required_rank`, and
`normal_matrix_condition_number`. They report the NumPy numerical rank and
2-norm condition number of the final coefficient normal matrix
`X' Z W Z' X`. A non-finite condition number is represented as unavailable.

These fields let downstream diagnostic gates distinguish full numerical rank
from shape checks and enforce a prespecified conditioning threshold. They are
descriptive numerical diagnostics, not evidence that instruments or structural
assumptions are valid. Estimator algebra, coefficients, covariance, standard
errors, and existing diagnostics are unchanged.

Install this release with:

```bash
python -m pip install systemgmmkit==1.0.2
```

---

# systemgmmkit 1.0.1 Release Notes

## Native GMM covariance provenance

Version `1.0.1` exposes the complete coefficient-aligned covariance matrix used
to produce native dynamic-GMM standard errors. Native results also report a
machine-readable correction identifier and reference. A two-step fit requested
with `windmeijer=True` reports `covariance_correction="windmeijer_2005"`, DOI
`10.1016/j.jeconom.2004.02.005`, and covariance type
`robust-clustered-two-step-windmeijer`. Uncorrected and one-step paths report
`covariance_correction="none"` and no correction reference.

The surface is additive and does not change estimator algebra, coefficients,
standard errors, diagnostics, or the six-specification `xtabond2` certification
boundary. The covariance matrix is required to be finite, symmetric,
coefficient-aligned, and diagonally consistent with the reported standard
errors. Post-estimation `vcov()` now returns this full matrix instead of a
diagonal standard-error fallback for native GMM results.

Install this release with:

```bash
python -m pip install systemgmmkit==1.0.1
```

---

# systemgmmkit 1.0.0 Release Notes

## Stable API and instrument-health reporting

Version `1.0.0` establishes the documented public API as stable. Future
incompatible changes to maintained estimator, result, diagnostics,
post-estimation, and workflow interfaces require a new major version;
deprecations will remain available for at least one minor release where
practical. Experimental behavior remains explicitly identified in its API or
documentation.

Native and `pydynpd` dynamic-GMM result summaries now report a structured
instrument-health assessment. The assessment records instrument and group
counts, their ratio, and one of four states: `acceptable` at or below 0.8,
`approaching` above 0.8 through 1.0, `critical` when instruments exceed groups,
or `unavailable` when either count is missing. Critical output recommends
shorter lag windows, collapsed instruments, and sensitivity checks. These
thresholds are conservative screening rules; they do not mechanically prove or
disprove instrument validity and do not replace Hansen, Sargan, AR, or
substantive identification analysis.

The release preserves the v0.5.14 native System GMM numerical-certification
scope: six maintained aligned specifications against Stata 17 and `xtabond2`
3.7.2, including exact sample-key checks for the unbalanced-panel and
variable-missing fixtures. Passing those gates is benchmark-specific numerical
agreement, not universal Stata equivalence or specification endorsement.

The stable release gate includes the complete test suite, enforced statement
and branch coverage floors, 100% dynamic-panel routing coverage, progressive
core mypy checks, Ruff, distribution inspection, dependency audits, SBOM
generation, exact wheel/sdist smoke tests, signed tagging, and protected PyPI
Trusted Publishing.

Static typing remains an enforced progressive gate over the documented core
modules rather than a PEP 561 promise for every optional visualization and ML
module. Additional lag-window, instrument-classification, and comparator
fixtures remain welcome extensions to the benchmark-specific certification;
their absence does not broaden the current claim boundary.

Install this release with:

```bash
python -m pip install systemgmmkit==1.0.0
```

---

# systemgmmkit 0.5.14 Release Notes

## Certified System GMM evidence and safer panel handling

Version `0.5.14` promotes one machine-generated source of truth for native
System GMM certification. The registry and unified certificate cover six
maintained, aligned, collapsed two-step specifications against Stata 17 and
`xtabond2` 3.7.2 (`e(version)=03.07.00`): baseline controls, no controls,
three-way controls, decomposition controls, an unbalanced panel, and a
variable-specific missing-data design.

The authoritative gate reruns the current native engine and verifies the
complete expected parameter set, Windmeijer-corrected standard errors, exact
observations/groups/instruments/overidentification degrees of freedom,
Hansen/Sargan statistics and p-values, and signed AR(1)/AR(2) statistics and
p-values. The unbalanced-panel and variable-missing fixtures additionally pass
exact estimation-sample-key gates. Canonical SHA-256 digests bind the generated
certificate to the registry, comparator, code, fixtures, do-files, and exact
native/Stata exports. The historical local Stata log is excluded because it
contains machine-specific paths; a path-free attestation preserves its hash and
records that limitation.

`PASS_XTABOND2_PARITY` means numerical agreement on these fixtures. It does not
establish instrument validity or endorse a specification. Stata rejects both
Hansen and Sargan at 5% for the no-controls (`0.02356` / `0.00568`),
three-way-controls (`0.02144` / `0.0000369`), decomposition (`0.00640` /
`0.0000128`), and variable-missing (`0.01151` / `0.0007838`) fixtures. The
baseline (`0.15998` / `0.08792`) and unbalanced-panel (`0.23240` / `0.29722`)
fixtures do not reject. The raw p-values and reject-at-0.05 flags remain visible
in the certificate. `system_gmm_three_way_no_controls` remains outside the
certified set because no complete Stata comparison artifact exists for it.

Native System GMM now preserves each variable's missing-value history, uses
explicit equation metadata for diagnostic rows, and matches AR residual pairs on
the exact panel-time grid. Integral numeric time labels follow Stata's default
unit-period delta, including periods absent from every entity. Dense grids fail
with recoding guidance before exceeding 100,000 periods or five million
entity-period rows. Non-integral numeric and datetime labels still use
ordered-rank semantics until the public specification gains an explicit time
delta; parity beyond the maintained fixtures is not claimed.

## API, typing, coverage, and reporting

The release narrows the wildcard-import surface to 77 dependency-free names
while retaining lazy explicit-import compatibility for optional plotting APIs.
It exposes the documented easy-GMM workflow names, removes shadowed legacy
modules and the accidental `contextlib` root attribute, adds compact display-only
inference tables, and provides an optional Universal Output Hub adapter on Python
3.10 and newer without changing Python 3.9 core support.

A progressive mypy gate now covers nine core specification, estimator, result,
validation, and table modules. A dedicated Python 3.12 all-extras coverage job
enforces statement, branch, and combined ratchets plus 100% statement and branch
coverage for dynamic-panel backend routing. The package remains classified as
Alpha while broader typing, methodological coverage, and API-stability work
continues.

## Release integrity

The release toolchain now requires `cryptography>=50,<51` and locks 50.0.0,
which removes the vulnerability affecting the previous release dependency. The
PyPI publisher action is updated to v1.14.2 at an immutable commit. Publication
continues to build once; audit dependencies into a CycloneDX SBOM; inspect the
distributions; and install, dependency-check, and smoke-test the exact wheel and
sdist in separate isolated environments. The downstream job attests and passes
those unchanged artifacts through PyPI Trusted Publishing and the protected
`pypi` environment. Smoke evidence reports versions and checks without exposing
a local installation path. The tracked Kaggle quickstart is prepared to install
the exact `systemgmmkit==0.5.14` and `universal-output-hub==0.2.4` PyPI
distributions with `--no-deps` instead of an unreleased Git commit; the public
Kaggle kernel must be republished after this version is available on PyPI.

Install this release with:

```bash
python -m pip install systemgmmkit==0.5.14
```

---

# systemgmmkit 0.5.13 Release Notes

## Controlled exact-parity acceleration

Version `0.5.13` adds an opt-in accelerated native-GMM preparation engine. It
caches repeated per-fit pandas sources while preserving the established
transformation, instrument ordering, matrix assembly, estimation, covariance,
Windmeijer correction, and diagnostic paths.

The validated reference engine remains the default and permanent audit path:

```python
reference = run_native_dynamic_panel_gmm(
    spec,
    data,
    entity="firm_id",
    time="year",
    preparation_engine="reference",
)
accelerated = run_native_dynamic_panel_gmm(
    spec,
    data,
    entity="firm_id",
    time="year",
    preparation_engine="accelerated",
)
```

The maintained benchmark covers balanced, unbalanced, unsorted, and gapped
panels; first-difference and forward-orthogonal-deviation transformations;
Difference and System GMM; one- and two-step estimation; collapsed instruments;
and Windmeijer-corrected inference. On the documented instrument-heavy workload,
the interleaved warm-run median improved from `1.301863` seconds to `0.389465`
seconds, a `3.34x` speedup and `70.08%` runtime reduction, with exact equality of
prepared matrices and fitted outputs.

The release also adds opt-in preparation acceleration to native LSDV fixed
effects and panel IV/2SLS. On the documented deterministic static benchmark,
two-way fixed effects improved from a `0.475624`-second reference median to
`0.064555` seconds (`7.37x`, an `86.43%` reduction). Panel IV with entity and time
LSDV controls improved from `0.533521` seconds to `0.107536` seconds (`4.96x`, a
`79.84%` reduction). Prepared designs and fitted results were exactly identical.
Rank-deficient designs use the unchanged sequential reference selector.

```python
fixed_effects = run_fixed_effects(
    fe_spec,
    data,
    entity="firm_id",
    time="year",
    preparation_engine="accelerated",
)

panel_iv = run_panel_2sls(
    iv_spec,
    data,
    entity="firm_id",
    time="year",
    preparation_engine="accelerated",
)
```

The same benchmark recorded OLS at `0.013533` seconds, clustered pooled OLS at
`0.105526` seconds, and random effects at `0.024369` seconds. Those paths were
already fast for the maintained workloads. A candidate random-effects cache
improved the median by only about 6%, so it was deliberately not added to the
public API.

The release also documents the benchmark environment, reproduction commands,
maintenance cost, rollback path, and reviewed dependency-scanner findings.

---

# systemgmmkit 0.5.12 Release Notes

## Supply-chain and dependency hardening

Version `0.5.12` is a security-focused patch release. It adds bounded direct
dependencies, hash-verified reproducible requirement sets, automated dependency
auditing, distribution-content inspection, an SBOM, dependency-review gates,
pinned GitHub Actions, and trusted PyPI publishing with build provenance.

Matplotlib is now an optional `plots` dependency. Core estimation and
post-estimation imports work without Matplotlib; plotting APIs report the exact
extra to install when it is absent:

```bash
python -m pip install "systemgmmkit[plots]"
```

The release workflow verifies that the release tag matches the package version,
builds once, checks both artifacts, and publishes the verified artifacts through
the protected `pypi` environment. See `docs/security/` for the evidence review,
release-integrity procedure, and the remaining Socket alert monitoring policy.

---

# systemgmmkit 0.5.9 Release Notes

## Overview

`systemgmmkit 0.5.9` expands the package from a dynamic-panel GMM implementation into a broader panel-data econometrics workflow package.

This release adds and documents:

* Ordinary Least Squares;
* Pooled OLS;
* post-estimation utilities;
* Stata-verified linear-model workflows;
* Stata-verified post-estimation procedures;
* strengthened Difference GMM and System GMM validation;
* System GMM `xtabond2` diagnostic certification;
* CMAPSS FD001 external validation for publication-style dynamic-panel workflows.

Earlier releases established the native Difference GMM and System GMM estimation paths. Version `0.5.9` strengthens those foundations and extends the package toward a fuller empirical workflow: baseline estimation, panel estimation, dynamic GMM, diagnostics, post-estimation, and reproducible reporting.

The main focus of this release is:

* OLS support;
* Pooled OLS support;
* post-estimation infrastructure;
* Stata parity verification for linear models;
* Stata parity verification for selected post-estimation procedures;
* strict `xtabond2` certification for the maintained System GMM benchmark;
* external validation on CMAPSS FD001 publication-style panel specifications.

---

# Major Additions

## Ordinary Least Squares

Version `0.5.9` introduces a dedicated OLS estimation workflow.

New public components include:

* `OLSSpec`;
* `run_ols()`;
* `LinearModelResult`.

Supported covariance estimators include:

* nonrobust;
* HC0;
* robust / HC1;
* clustered.

OLS provides a natural baseline model before moving to panel-specific estimators such as Fixed Effects, Random Effects, Panel IV, Difference GMM, or System GMM.

---

## Pooled OLS

Version `0.5.9` introduces pooled OLS support for panel-shaped datasets.

New public components include:

* `PooledOLSSpec`;
* `run_pooled_ols()`.

Supported features include:

* panel-shaped data;
* clustered standard errors;
* entity-level clustering;
* consistent result objects;
* Stata-style comparison workflows.

Pooled OLS is useful as a baseline estimator before applying within-transformation, random-effects, IV, or dynamic-panel estimators.

---

# Post-Estimation Framework

Version `0.5.9` introduces the first public post-estimation framework.

New public APIs include:

```python
predict()
fitted_values()
residuals()
vcov()
confint()
lincom()
wald_test()
marginal_effects()
```

These APIs provide functionality similar to common Stata post-estimation workflows and establish the foundation for future advanced post-estimation capabilities.

The first public post-estimation layer focuses on linear estimators and common applied workflows:

* predictions;
* fitted values;
* residual extraction;
* variance-covariance matrix extraction;
* confidence intervals;
* linear combinations;
* Wald tests;
* marginal effects for linear models.

---

# Stata Verification Milestone

A major objective of this release was verification against Stata reference implementations.

The following components were benchmarked against Stata using maintained FD001 panel-data workflows.

---

## Verified OLS Components

Verified against:

```stata
regress ..., vce(robust)
```

Validated quantities include:

* coefficients;
* robust standard errors;
* t-statistics;
* p-values;
* confidence intervals.

Observed agreement under the maintained FD001 benchmark:

| Metric                            | Result   |
| --------------------------------- | -------- |
| Maximum coefficient difference    | 4.64e-14 |
| Maximum standard-error difference | 2.04e-14 |

These differences are effectively machine precision.

---

## Verified Clustered OLS Components

Verified against:

```stata
regress ..., vce(cluster entity)
```

Validated quantities include:

* coefficients;
* clustered standard errors;
* t-statistics;
* p-values;
* confidence intervals.

Observed differences remain at machine precision under the maintained benchmark workflow.

---

## Verified `lincom` Parity

Verified against:

```stata
lincom variable1 + variable2
```

Validated quantities include:

* estimate;
* standard error;
* test statistic;
* p-value;
* confidence interval.

The maintained FD001 benchmark comparison shows numerical agreement between Stata and `systemgmmkit`.

---

## Verified Wald-Test Parity

Verified against:

```stata
test variable1 variable2 ...
```

Validated quantities include:

* F statistic;
* numerator degrees of freedom;
* denominator degrees of freedom;
* p-value.

The maintained FD001 benchmark comparison shows numerical agreement between Stata and `systemgmmkit`.

---

# Dynamic GMM Validation

Version `0.5.9` continues to include native Difference GMM and System GMM functionality and strengthens the validation language around those estimators.

The package supports:

* Arellano-Bond Difference GMM;
* Blundell-Bond System GMM;
* endogenous variables;
* predetermined variables;
* exogenous variables;
* restricted GMM lag windows;
* collapsed instruments;
* one-step estimation;
* two-step estimation;
* Windmeijer-corrected standard errors;
* diagnostic reporting.

---

## Native Difference GMM

Supported features include:

* endogenous variables;
* predetermined variables;
* exogenous variables;
* lag-window control;
* collapsed instruments;
* one-step estimation;
* two-step estimation;
* AR diagnostics;
* Hansen diagnostics;
* Sargan diagnostics;
* observation, group, and instrument counts.

Maintained benchmark status:

```text
PASS_XTABOND2_PARITY
```

Validated diagnostics include:

* AR(1);
* AR(2);
* Hansen;
* Sargan;
* observation counts;
* group counts;
* instrument counts;
* degrees of freedom.

---

## Native System GMM

Supported features include:

* Blundell-Bond System GMM;
* differenced-equation moments;
* levels-equation moments;
* endogenous variables;
* predetermined variables;
* exogenous variables;
* collapsed instruments;
* restricted lag windows;
* one-step estimation;
* two-step estimation;
* Windmeijer correction.

Maintained benchmark status:

```text
PASS_XTABOND2_PARITY
```

Validated quantities include:

* coefficients;
* Windmeijer-corrected two-step standard errors;
* Hansen statistics and p-values;
* Sargan statistics and p-values;
* AR(1) diagnostics;
* AR(2) diagnostics;
* instrument counts;
* observation counts;
* group counts.

---

# System GMM `xtabond2` Certification

The native System GMM implementation has been certified against Stata `xtabond2` on the maintained collapsed two-step benchmark specification.

Certified components include:

* coefficient estimates;
* Windmeijer-corrected two-step standard errors;
* sample size;
* instrument count;
* Hansen overidentification diagnostic;
* Sargan overidentification diagnostic;
* Arellano-Bond AR(1) diagnostic;
* Arellano-Bond AR(2) diagnostic.

The maintained certification benchmark uses:

* collapsed instruments;
* restricted GMM lag windows;
* two-step robust estimation;
* Windmeijer correction;
* strict numerical comparison against `xtabond2`.

Under this benchmark, the native System GMM implementation reproduces the `xtabond2` reference results within declared strict numerical tolerance.

---

# CMAPSS FD001 External Validation

In addition to the controlled `xtabond2` certification benchmark, System GMM was externally validated on CMAPSS FD001 publication-style panel specifications.

Two validation models were used.

Risk model:

```text
risk ~ L1.risk + degradation_index + sensor_mean_z + pc2 + op_setting1 + op_setting2
```

Degradation model:

```text
degradation_index ~ L1.degradation_index + sensor_mean_z + pc2 + pc3 + op_setting1 + op_setting2
```

Across both FD001 validation models, `systemgmmkit` reproduces `xtabond2` results for:

* coefficient estimates;
* Windmeijer-corrected standard errors;
* sample size;
* instrument count;
* Hansen diagnostics;
* Sargan diagnostics;
* AR(1) and AR(2) diagnostics within declared external-validation tolerance.

The CMAPSS FD001 exercise is an independent application validation. The controlled `xtabond2` benchmark remains the strict certification benchmark.

---

# Verification Summary

Current benchmark validation status:

| Component                  | Status                |
| -------------------------- | --------------------- |
| OLS                        | PASS_STATA_PARITY     |
| Robust OLS                 | PASS_STATA_PARITY     |
| Clustered OLS              | PASS_STATA_PARITY     |
| Confidence intervals       | PASS_STATA_PARITY     |
| `lincom`                   | PASS_STATA_PARITY     |
| Wald / F tests             | PASS_STATA_PARITY     |
| Fixed Effects              | PASS_STATA_COMPARISON |
| Random Effects             | PASS_STATA_COMPARISON |
| Panel IV / 2SLS            | PASS_STATA_COMPARISON |
| Difference GMM             | PASS_XTABOND2_PARITY  |
| System GMM                 | PASS_XTABOND2_PARITY  |
| Windmeijer standard errors | PASS_XTABOND2_PARITY  |
| Hansen diagnostics         | PASS_XTABOND2_PARITY  |
| Sargan diagnostics         | PASS_XTABOND2_PARITY  |
| AR(1) diagnostics          | PASS_XTABOND2_PARITY  |
| AR(2) diagnostics          | PASS_XTABOND2_PARITY  |

Validation claims apply to the maintained benchmark specifications and validation workflows in the repository. The controlled `xtabond2` benchmark is used for strict certification. The CMAPSS FD001 application is used as an external validation case.

Users should still inspect their own model diagnostics, instrument counts, sample construction, lag-window choices, and identification assumptions.

---

# Reporting and Export

The package supports:

* structured result objects;
* model summaries;
* Markdown export;
* CSV export;
* LaTeX export;
* integration with `universal-output-hub`.

Supported exported diagnostics include:

* coefficient tables;
* covariance matrices;
* confidence intervals;
* Hansen diagnostics;
* Sargan diagnostics;
* AR diagnostics;
* instrument counts;
* observation counts;
* group counts.

---

# Dynamic GMM Modelling Notes

Version `0.5.9` clarifies an important modelling distinction in dynamic GMM:

```text
Structural lags are model regressors.
Instrument lags define the GMM instrument window.
```

For example:

```python
regressors=["L1_y", "investment", "L1_investment"]
```

means that `L1_y` and `L1_investment` are included directly in the model equation.

By contrast:

```python
gmm_lags=(2, 4)
```

means that lagged values, usually lags 2 through 4, are used internally as GMM instruments.

In the current public API, users should manually create lagged structural regressors before estimation and then classify them according to the maintained exogeneity assumption.

Example:

```python
df = df.sort_values(["firm_id", "year"]).copy()
df["L1_y"] = df.groupby("firm_id")["y"].shift(1)
df["L1_investment"] = df.groupby("firm_id")["investment"].shift(1)
```

Then include the lagged variables in the model:

```python
spec = build_system_gmm_spec(
    dependent="y",
    regressors=[
        "L1_y",
        "investment",
        "L1_investment",
        "firm_size",
    ],
    endogenous=[
        "L1_y",
        "investment",
        "L1_investment",
    ],
    exogenous=[
        "firm_size",
    ],
    gmm_lags=(2, 4),
    collapse=True,
    windmeijer=True,
)
```

Lagging an endogenous or predetermined regressor does not automatically make it exogenous. Users should classify lagged variables according to the maintained economic or causal assumption.

---

# Validation Boundary

Version `0.5.9` provides benchmark-specific validation evidence.

Certified and validated:

* OLS parity on maintained FD001 benchmark workflows;
* robust OLS parity on maintained FD001 benchmark workflows;
* clustered OLS parity on maintained FD001 benchmark workflows;
* confidence-interval parity on maintained FD001 benchmark workflows;
* `lincom` parity on maintained FD001 benchmark workflows;
* Wald-test parity on maintained FD001 benchmark workflows;
* Difference GMM parity on maintained benchmark workflows;
* System GMM parity on the maintained `xtabond2` benchmark;
* Windmeijer standard-error parity on maintained benchmark specifications;
* Hansen and Sargan diagnostic parity on maintained benchmark specifications;
* AR diagnostic parity on the maintained benchmark and external-validation workflows.

Not claimed:

* universal identity with every possible Stata configuration;
* universal identity across every lag window;
* universal identity across every missing-data pattern;
* universal identity across every covariance estimator;
* universal identity across every instrument specification;
* universal bit-for-bit equivalence across all empirical datasets.

The correct interpretation is:

```text
systemgmmkit provides benchmark-specific parity evidence for maintained validation workflows and benchmark datasets. It does not claim universal bit-for-bit equivalence across all econometric specifications.
```

---

# Installation

Latest published release:

```bash
python -m pip install systemgmmkit
```

Install a specific release:

```bash
python -m pip install systemgmmkit==0.5.9
```

Development branch:

```bash
python -m pip install git+https://github.com/Akanom/systemgmmkit.git
```

Local development installation:

```bash
python -m pip install -e ".[dev,all]"
```

Check the installed version:

```python
import systemgmmkit

print(systemgmmkit.__version__)
```

---

# Recommended Reporting Statement

For empirical research, report:

* package version;
* estimator;
* specification;
* covariance estimator;
* instrument count;
* backend;
* AR diagnostics;
* Hansen diagnostics;
* Sargan diagnostics.

Suggested wording:

```text
Estimation was performed using systemgmmkit 0.5.9. Linear-model and post-estimation workflows were benchmarked against Stata reference implementations. Dynamic-panel GMM models used the documented systemgmmkit backend and specification settings. For maintained validation benchmarks, systemgmmkit includes benchmark-specific parity evidence against Stata for OLS, clustered OLS, confidence intervals, lincom, Wald tests, Difference GMM, System GMM, Windmeijer-corrected standard errors, overidentification diagnostics, and AR diagnostics.
```

For System GMM specifically:

```text
The System GMM implementation was certified against Stata xtabond2 on a maintained collapsed two-step benchmark and externally validated on CMAPSS FD001 publication-style panel specifications. Certification and validation claims apply to the maintained benchmark workflows and declared numerical tolerances.
```

---

# Release Policy

`systemgmmkit 0.5.9` should be released only after:

* development work is complete;
* documentation has been reviewed;
* parity verification artifacts have been regenerated;
* the test suite passes;
* version metadata is consistent;
* release notes are updated;
* the GitHub release tag is intentionally created;
* PyPI publication is intentionally triggered.

No PyPI publication should occur from an unreviewed development state.

---

# Summary

`systemgmmkit 0.5.9` is a major validation and workflow release.

It extends the package beyond dynamic-panel GMM by adding OLS, pooled OLS, and post-estimation tools, while also strengthening the evidence base for the native GMM implementation.

The release provides:

* broader estimator coverage;
* first public post-estimation support;
* Stata-verified linear-model workflows;
* strict System GMM `xtabond2` certification;
* CMAPSS FD001 external validation;
* clearer documentation of structural lags versus instrument lag windows;
* stronger reporting guidance for applied empirical research.
