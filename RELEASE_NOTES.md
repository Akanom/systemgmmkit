# systemgmmkit 0.5.8.dev0 Release Notes

## Overview

`systemgmmkit 0.5.8.dev0` is the current GitHub development branch following the publication of `systemgmmkit 0.5.7`.

Version `0.5.7` established benchmark-specific Stata `xtabond2` parity for the maintained native Difference GMM and System GMM validation paths.

Version `0.5.8.dev0` extends the package beyond estimation and introduces the first public post-estimation framework together with verified Ordinary Least Squares (OLS) and Pooled OLS workflows.

The primary focus of this development cycle is:

* OLS support
* Pooled OLS support
* Post-estimation infrastructure
* Stata parity verification for linear models
* Stata parity verification for post-estimation procedures

This release continues the package's emphasis on reproducibility, transparent econometric workflows, and benchmark validation against established reference implementations.

---

# Major Additions

## Ordinary Least Squares (OLS)

Version 0.5.8 introduces a dedicated OLS estimation workflow.

New components:

* `OLSSpec`
* `run_ols()`
* `LinearModelResult`

Supported covariance estimators:

* Nonrobust
* HC0
* Robust / HC1
* Clustered

OLS provides a natural baseline model before moving to panel-specific estimators such as Fixed Effects, Random Effects, Panel IV, Difference GMM, or System GMM.

---

## Pooled OLS

Version 0.5.8 introduces pooled OLS support for panel-shaped datasets.

New components:

* `PooledOLSSpec`
* `run_pooled_ols()`

Supported features:

* Panel-shaped data
* Clustered standard errors
* Entity-level clustering
* Consistent result objects
* Stata-style comparison workflows

---

# Post-Estimation Framework

Version 0.5.8 introduces the first public post-estimation foundation.

New public APIs:

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

---

# Stata Verification Milestone

A major objective of this development cycle was verification against Stata.

The following components were benchmarked against Stata using a real FD001 panel-data benchmark.

## Verified OLS Components

Verified against:

```stata
regress ..., vce(robust)
```

Validated quantities:

* coefficients
* robust standard errors
* t-statistics
* p-values
* confidence intervals

Observed differences:

| Metric                            | Result   |
| --------------------------------- | -------- |
| Maximum coefficient difference    | 4.64e-14 |
| Maximum standard error difference | 2.04e-14 |

These differences are effectively machine precision.

---

## Verified Clustered OLS Components

Verified against:

```stata
regress ..., vce(cluster entity)
```

Validated quantities:

* coefficients
* clustered standard errors
* t-statistics
* p-values
* confidence intervals

Observed differences remain at machine precision.

---

## Verified lincom Parity

Verified against:

```stata
lincom variable1 + variable2
```

Validated quantities:

* estimate
* standard error
* test statistic
* p-value
* confidence interval

FD001 benchmark comparison showed numerical agreement between Stata and `systemgmmkit`.

---

## Verified Wald Test Parity

Verified against:

```stata
test variable1 variable2 ...
```

Validated quantities:

* F statistic
* numerator degrees of freedom
* denominator degrees of freedom
* p-value

FD001 benchmark comparison showed numerical agreement between Stata and `systemgmmkit`.

---

# Inherited GMM Capability from 0.5.7

Version 0.5.8 continues to include all validated native GMM functionality introduced during the 0.5.7 certification cycle.

---

## Native Difference GMM

Supported features:

* Arellano-Bond Difference GMM
* Endogenous variables
* Predetermined variables
* Exogenous variables
* Lag-window control
* Collapsed instruments
* One-step estimation
* Two-step estimation
* Diagnostic reporting

Maintained benchmark status:

```text
PASS_XTABOND2_FD001_DIAGNOSTIC_PARITY
```

Validated diagnostics include:

* AR(1)
* AR(2)
* Hansen
* Sargan
* Observation counts
* Group counts
* Instrument counts
* Degrees of freedom

---

## Native System GMM

Supported features:

* Blundell-Bond System GMM
* Difference equation moments
* Level equation moments
* Collapsed instruments
* Restricted lag windows
* One-step estimation
* Two-step estimation
* Windmeijer correction

Maintained benchmark status:

```text
PASS_XTABOND2_FD001_DIAGNOSTIC_PARITY
```

Validated quantities include:

* coefficients
* Windmeijer-corrected standard errors
* Hansen statistics
* Sargan statistics
* AR(1)
* AR(2)
* instrument counts
* observation counts
* group counts

---

# Verification Summary

Current benchmark validation status:

| Component                  | Status                |
| -------------------------- | --------------------- |
| OLS                        | PASS_STATA_PARITY     |
| Robust OLS                 | PASS_STATA_PARITY     |
| Clustered OLS              | PASS_STATA_PARITY     |
| Confidence Intervals       | PASS_STATA_PARITY     |
| lincom                     | PASS_STATA_PARITY     |
| Wald Test                  | PASS_STATA_PARITY     |
| Fixed Effects              | PASS_STATA_COMPARISON |
| Random Effects             | PASS_STATA_COMPARISON |
| Panel IV / 2SLS            | PASS_STATA_COMPARISON |
| Difference GMM             | PASS_XTABOND2_PARITY  |
| System GMM                 | PASS_XTABOND2_PARITY  |
| Windmeijer Standard Errors | PASS_XTABOND2_PARITY  |

---

# Reporting and Export

The package continues to support:

* structured result objects
* model summaries
* Markdown export
* CSV export
* LaTeX export
* integration with universal-output-hub

Supported exported diagnostics include:

* coefficient tables
* covariance matrices
* confidence intervals
* Hansen diagnostics
* Sargan diagnostics
* AR diagnostics
* instrument counts
* observation counts
* group counts

---

# Validation Boundary

Version 0.5.8 provides benchmark-specific validation evidence.

Certified and validated:

* OLS parity on maintained FD001 benchmark workflows
* Clustered OLS parity on maintained FD001 benchmark workflows
* lincom parity on maintained FD001 benchmark workflows
* Wald-test parity on maintained FD001 benchmark workflows
* Difference GMM parity on maintained FD001 benchmark workflows
* System GMM parity on maintained FD001 benchmark workflows
* Windmeijer standard-error parity on maintained benchmark specifications

Not claimed:

* universal identity with every possible Stata configuration
* universal identity across every lag window
* universal identity across every missing-data pattern
* universal identity across every covariance estimator
* universal identity across every instrument specification

The correct interpretation is:

```text
systemgmmkit provides benchmark-specific parity evidence for maintained validation workflows and benchmark datasets. It does not claim universal bit-for-bit equivalence across all econometric specifications.
```

---

# Installation

Latest published release:

```bash
python -m pip install systemgmmkit==0.5.7
```

Development branch:

```bash
pip install git+https://github.com/Akanom/systemgmmkit.git
```

Local development installation:

```bash
python -m pip install -e ".[dev,all]"
```

---

# Recommended Reporting Statement

For empirical research, report:

* package version
* estimator
* specification
* covariance estimator
* instrument count
* backend
* AR diagnostics
* Hansen diagnostics
* Sargan diagnostics

Suggested wording:

```text
Estimation was performed using systemgmmkit 0.5.8.dev0. Linear-model and post-estimation workflows were benchmarked against Stata reference implementations. Dynamic-panel GMM models used the documented systemgmmkit backend and specification settings. For maintained validation benchmarks, systemgmmkit includes benchmark-specific parity evidence against Stata for OLS, clustered OLS, lincom, Wald tests, Difference GMM, System GMM, Windmeijer-corrected standard errors, and associated diagnostics.
```

---

# Release Policy

`systemgmmkit 0.5.7` remains the latest published PyPI release.

`0.5.8.dev0` is a GitHub development version and should not be considered a stable published release.

Publication of `v0.5.8` should occur only after:

* completion of development work
* documentation review
* parity verification review
* test-suite completion
* intentional release tagging

No PyPI publication should occur directly from the current development state.
