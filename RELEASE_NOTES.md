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
