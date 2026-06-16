# systemgmmkit

[![PyPI version](https://img.shields.io/pypi/v/systemgmmkit.svg)](https://pypi.org/project/systemgmmkit/)
[![Python versions](https://img.shields.io/pypi/pyversions/systemgmmkit.svg)](https://pypi.org/project/systemgmmkit/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://github.com/Akanom/systemgmmkit/actions/workflows/ci.yml/badge.svg)](https://github.com/Akanom/systemgmmkit/actions/workflows/ci.yml)
[![Publish](https://github.com/Akanom/systemgmmkit/actions/workflows/publish.yml/badge.svg)](https://github.com/Akanom/systemgmmkit/actions/workflows/publish.yml)

---

# systemgmmkit 0.5.8

`systemgmmkit` is a Python package for panel-data econometrics that provides a unified workflow from baseline linear models to advanced dynamic-panel GMM estimation.

The package combines:

* Ordinary Least Squares (OLS)
* Pooled OLS
* Fixed Effects
* Random Effects
* Panel IV / 2SLS
* Difference GMM
* System GMM
* Diagnostics
* Post-estimation
* Reproducible reporting

within a single framework.

The package is designed for applied empirical research in economics, finance, management, operations, public policy, political economy, industrial organization, productivity analysis, and other panel-data settings.

---

# Why systemgmmkit?

Many econometric workflows require researchers to combine multiple packages to obtain:

* baseline estimation;
* panel estimators;
* instrumental-variable estimation;
* dynamic-panel estimation;
* diagnostics;
* post-estimation;
* publication-ready reporting.

`systemgmmkit` aims to provide these capabilities through a consistent and reproducible API.

The package is built around four principles:

1. Explicit model specification.
2. Reproducible workflows.
3. Transparent diagnostics.
4. Verification against established reference implementations.

---

# What's New in 0.5.8

Version `0.5.8.dev0` introduces the first public post-estimation framework and completes the baseline linear-model workflow.

New public APIs include:

* `OLSSpec`
* `PooledOLSSpec`
* `run_ols()`
* `run_pooled_ols()`
* `predict()`
* `fitted_values()`
* `residuals()`
* `vcov()`
* `confint()`
* `lincom()`
* `wald_test()`
* `marginal_effects()`

These additions establish the foundation for future advanced post-estimation capabilities while maintaining compatibility with the broader panel-estimation framework.

---

# Core Estimator Coverage

## Linear Models

* Ordinary Least Squares
* Robust OLS
* Pooled OLS
* Clustered OLS

## Panel Models

* One-Way Fixed Effects
* Two-Way Fixed Effects
* Random Effects
* Panel IV / 2SLS

## Dynamic Panel Models

* Difference GMM
* System GMM
* One-Step Estimation
* Two-Step Estimation
* Windmeijer-Corrected Standard Errors
* Collapsed Instruments
* Restricted Lag Windows

## Reporting

* Markdown Export
* CSV Export
* LaTeX Export
* Structured Result Objects
* Integration with universal-output-hub

---

# Verification Philosophy

Verification is a core design principle of `systemgmmkit`.

Whenever practical, estimators are benchmarked against established Stata implementations including:

* `regress`
* `xtreg`
* `ivregress`
* `xtabond2`
* `xtdpdgmm`

Benchmark scripts, comparison workflows, and validation artifacts are maintained within the repository.

The objective is not merely to produce estimates, but to provide transparent evidence that estimates match trusted reference implementations under maintained benchmark specifications.

---

# Current Validation Status

The major estimation paths currently exposed through the public API have either:

1. been directly benchmarked against Stata reference implementations; or
2. have dedicated comparison workflows maintained within the repository.

## Verified Components

| Component                  | Status                |
| -------------------------- | --------------------- |
| OLS                        | PASS_STATA_PARITY     |
| Robust OLS                 | PASS_STATA_PARITY     |
| Clustered OLS              | PASS_STATA_PARITY     |
| Confidence Intervals       | PASS_STATA_PARITY     |
| lincom                     | PASS_STATA_PARITY     |
| Wald / F Tests             | PASS_STATA_PARITY     |
| Fixed Effects              | PASS_STATA_COMPARISON |
| Random Effects             | PASS_STATA_COMPARISON |
| Panel IV / 2SLS            | PASS_STATA_COMPARISON |
| Difference GMM             | PASS_XTABOND2_PARITY  |
| System GMM                 | PASS_XTABOND2_PARITY  |
| Windmeijer Standard Errors | PASS_XTABOND2_PARITY  |
| Hansen Diagnostics         | PASS_XTABOND2_PARITY  |
| Sargan Diagnostics         | PASS_XTABOND2_PARITY  |
| AR(1) Diagnostics          | PASS_XTABOND2_PARITY  |
| AR(2) Diagnostics          | PASS_XTABOND2_PARITY  |

---

# Verified OLS Benchmark

The OLS and pooled OLS implementations have been verified against Stata using a real FD001 panel-data benchmark.

Benchmark model:

```text
risk ~ degradation_index + sensor_mean_z + pc2 + op_setting1 + op_setting2
```

Panel structure:

```text
entity = unit
time = cycle
```

Observed agreement:

| Metric                            | Result   |
| --------------------------------- | -------- |
| Maximum coefficient difference    | 4.64e-14 |
| Maximum standard-error difference | 2.04e-14 |

These differences represent machine-precision agreement with Stata.

---

# Installation

Stable release:

```bash
pip install systemgmmkit
```

Development version:

```bash
pip install git+https://github.com/Akanom/systemgmmkit.git
```

Local development installation:

```bash
pip install -e ".[dev,all]"
```

---

# Quick Start

## Ordinary Least Squares

```python
from systemgmmkit import OLSSpec, run_ols

spec = OLSSpec(
    dependent="y",
    regressors=["x1", "x2"],
    controls=["z1", "z2"],
    covariance="robust",
)

result = run_ols(spec, df)

print(result.summary_frame())
```

Equivalent Stata command:

```stata
regress y x1 x2 z1 z2, vce(robust)
```

---

## Pooled OLS

```python
from systemgmmkit import PooledOLSSpec, run_pooled_ols

spec = PooledOLSSpec(
    dependent="y",
    regressors=["x1", "x2"],
    controls=["z1"],
    covariance="clustered",
)

result = run_pooled_ols(
    spec,
    df,
    entity="firm_id",
    time="year",
)
```

Equivalent Stata command:

```stata
regress y x1 x2 z1, vce(cluster firm_id)
```

---

## Fixed Effects

```python
result = run_fixed_effects(
    spec,
    df,
    entity="firm_id",
    time="year",
)
```

Equivalent Stata:

```stata
xtreg y x1 x2, fe
```

---

## Random Effects

```python
result = run_random_effects(
    spec,
    df,
    entity="firm_id",
    time="year",
)
```

Equivalent Stata:

```stata
xtreg y x1 x2, re
```

---

## Panel IV / 2SLS

```python
result = run_panel_2sls(
    spec,
    df,
    entity="firm_id",
    time="year",
)
```

Equivalent Stata:

```stata
ivregress 2sls
```

---

## Difference GMM

```python
result = run_difference_gmm(
    spec,
    df,
    entity="firm_id",
    time="year",
)
```

Equivalent Stata:

```stata
xtabond2
```

---

## System GMM

```python
result = run_system_gmm(
    spec,
    df,
    entity="firm_id",
    time="year",
)
```

Equivalent Stata:

```stata
xtabond2
```

---

# Post-Estimation

The 0.5.8 development cycle introduces the first public post-estimation framework.

Import:

```python
from systemgmmkit import (
    predict,
    fitted_values,
    residuals,
    vcov,
    confint,
    lincom,
    wald_test,
    marginal_effects,
)
```

---

## Predictions

Equivalent Stata:

```stata
predict yhat
```

Python:

```python
pred = predict(result)
```

or

```python
pred = result.predict()
```

---

## Fitted Values

```python
fit = fitted_values(result)
```

---

## Residuals

Equivalent Stata:

```stata
predict ehat, residuals
```

Python:

```python
resid = residuals(result)
```

---

## Variance-Covariance Matrix

```python
V = vcov(result)
```

---

## Confidence Intervals

```python
ci = confint(result)
```

---

## Linear Combinations

Equivalent Stata:

```stata
lincom x1 + x2
```

Python:

```python
lincom(
    result,
    {
        "x1": 1,
        "x2": 1,
    },
)
```

Returns:

* estimate
* standard error
* statistic
* p-value
* confidence interval

---

## Wald Tests

Equivalent Stata:

```stata
test x1 x2
```

Python:

```python
wald_test(
    result,
    R=[
        [0,1,0],
        [0,0,1],
    ],
)
```

Returns:

* Wald statistic
* degrees of freedom
* p-value

---

## Marginal Effects

```python
marginal_effects(result)
```

For linear estimators, marginal effects correspond to estimated slopes.

---

# Reporting and Export

Results can be exported to:

* Markdown
* CSV
* LaTeX

and integrated with:

* universal-output-hub
* publication pipelines
* reproducible research workflows

---

# Recommended Reporting Practice

For empirical research, report:

* estimator;
* specification;
* covariance estimator;
* instrument count;
* AR diagnostics;
* Hansen diagnostics;
* backend;
* package version.

This improves transparency and reproducibility.

---

# Citation

If you use `systemgmmkit` in academic work, please cite:

```text
Akanbi, Oluwajuwon Mayomi.

systemgmmkit:
Panel Data Econometrics and Dynamic GMM Workflows in Python.

Version 0.5.8.

https://github.com/Akanom/systemgmmkit
```

BibTeX:

```bibtex
@software{akanbi_systemgmmkit,
  author = {Akanbi, Oluwajuwon Mayomi},
  title = {systemgmmkit: Panel Data Econometrics and Dynamic GMM Workflows in Python},
  year = {2026},
  url = {https://github.com/Akanom/systemgmmkit}
}
```

Replace with DOI information once a software paper or Zenodo archive is published.

---

# License

MIT License.

See `LICENSE` for details.
