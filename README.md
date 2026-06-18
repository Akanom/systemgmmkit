# systemgmmkit

[![PyPI version](https://img.shields.io/pypi/v/systemgmmkit.svg)](https://pypi.org/project/systemgmmkit/)
[![Python versions](https://img.shields.io/pypi/pyversions/systemgmmkit.svg)](https://pypi.org/project/systemgmmkit/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://github.com/Akanom/systemgmmkit/actions/workflows/ci.yml/badge.svg)](https://github.com/Akanom/systemgmmkit/actions/workflows/ci.yml)
[![Publish](https://github.com/Akanom/systemgmmkit/actions/workflows/publish.yml/badge.svg)](https://github.com/Akanom/systemgmmkit/actions/workflows/publish.yml)

---

# systemgmmkit 0.5.9

`systemgmmkit` is a Python package for applied panel-data econometrics. It provides a unified workflow for baseline linear models, panel estimators, instrumental-variable models, dynamic-panel GMM estimation, diagnostics, post-estimation, and reproducible reporting.

The package currently supports:

* Ordinary Least Squares;
* Pooled OLS;
* Fixed Effects;
* Random Effects;
* Panel IV / 2SLS;
* Difference GMM;
* System GMM;
* diagnostic reporting;
* post-estimation utilities;
* reproducible reporting workflows.

`systemgmmkit` is designed for empirical researchers working in economics, finance, management, operations, productivity analysis, public policy, development economics, political economy, industrial organization, and other panel-data settings.

---

# Why systemgmmkit?

Applied panel-data research often requires several tools for one workflow:

* baseline OLS models;
* pooled panel regressions;
* fixed-effects and random-effects models;
* instrumental-variable models;
* dynamic-panel GMM models;
* diagnostic tests;
* post-estimation analysis;
* reproducible tables and exports.

`systemgmmkit` aims to bring these pieces into a consistent Python API.

The package is built around four principles:

1. **Explicit model specification**
   Model assumptions should be visible in the code, not hidden inside estimation defaults.

2. **Reproducible empirical workflows**
   Estimation, diagnostics, and reporting should be easy to rerun and inspect.

3. **Transparent diagnostics**
   Dynamic-panel GMM results should expose sample size, instrument count, AR tests, Hansen/Sargan tests, covariance type, and backend metadata.

4. **Verification against reference implementations**
   Estimators are benchmarked against established Stata implementations where practical.

The objective is not only to estimate models, but to make modelling choices clear enough for replication, review, and publication.

---

# What's New in 0.5.9

Version `0.5.9` strengthens the public modelling workflow by expanding baseline estimation and post-estimation support.

New and expanded public APIs include:

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

Version `0.5.9` also improves dynamic GMM documentation by clearly distinguishing:

* lagged variables included directly in the structural equation; and
* lagged values used internally as GMM instruments.

This distinction is important for correct empirical modelling and for avoiding confusion between structural lags and instrument lag windows.

---

# Core Estimator Coverage

## Linear Models

* Ordinary Least Squares
* Robust OLS
* Pooled OLS
* Clustered OLS

## Panel Models

* One-way Fixed Effects
* Two-way Fixed Effects
* Random Effects
* Panel IV / 2SLS

## Dynamic Panel Models

* Difference GMM
* System GMM
* One-step estimation
* Two-step estimation
* Windmeijer-corrected standard errors
* Collapsed instruments
* Restricted GMM lag windows

## Post-Estimation

* Predictions
* Fitted values
* Residuals
* Variance-covariance extraction
* Confidence intervals
* Linear combinations
* Wald tests
* Marginal effects for linear estimators

## Reporting

* Markdown export
* CSV export
* LaTeX export
* Structured result objects
* Integration with `universal-output-hub`

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

Check the installed version:

```python
import systemgmmkit

print(systemgmmkit.__version__)
```

---

# Verification Philosophy

Verification is a core design principle of `systemgmmkit`.

Where practical, estimators are benchmarked against established Stata implementations, including:

* `regress`;
* `xtreg`;
* `ivregress`;
* `xtabond2`;
* `xtdpdgmm`.

Benchmark scripts, comparison workflows, and validation artifacts are maintained in the repository.

The goal is not merely to produce estimates. The goal is to provide transparent evidence that estimates match trusted reference implementations under maintained benchmark specifications.

---

# Current Validation Status

The major estimation paths currently exposed through the public API have either been directly benchmarked against Stata reference implementations or have dedicated comparison workflows maintained in the repository.

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

Validation claims apply to the maintained benchmark specifications and validation workflows in the repository. The controlled `xtabond2` benchmark is used for strict certification. The CMAPSS FD001 application is used as an external validation case. Users should still inspect their own model diagnostics, instrument counts, sample construction, lag-window choices, and identification assumptions.

---

# System GMM xtabond2 Certification

The native System GMM implementation has been certified against Stata `xtabond2` on a maintained collapsed two-step benchmark specification.

Certified components include:

* coefficient estimates;
* Windmeijer-corrected two-step standard errors;
* sample size;
* instrument count;
* Hansen overidentification diagnostic;
* Sargan overidentification diagnostic;
* Arellano-Bond AR(1) diagnostic;
* Arellano-Bond AR(2) diagnostic.

The maintained benchmark uses a controlled dynamic-panel specification with:

* collapsed instruments;
* restricted GMM lag windows;
* two-step robust estimation;
* Windmeijer correction;
* strict numerical comparison against `xtabond2`.

Under this maintained benchmark, the native implementation reproduces the `xtabond2` reference results within declared strict numerical tolerance.

---

# External CMAPSS FD001 Validation

In addition to the controlled benchmark, System GMM was externally validated on CMAPSS FD001 publication-style panel specifications.

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

The FD001 validation is used as an independent application check. The controlled `xtabond2` benchmark remains the strict certification benchmark.

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

| Metric                            |   Result |
| --------------------------------- | -------: |
| Maximum coefficient difference    | 4.64e-14 |
| Maximum standard-error difference | 2.04e-14 |

These differences represent machine-precision agreement with Stata under the maintained benchmark specification.

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

Equivalent Stata idea:

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

print(result.summary_frame())
```

Equivalent Stata idea:

```stata
regress y x1 x2 z1, vce(cluster firm_id)
```

---

## Fixed Effects

```python
from systemgmmkit import build_fixed_effects_spec, run_fixed_effects

spec = build_fixed_effects_spec(
    dependent="y",
    regressors=["x1", "x2"],
    controls=["z1"],
)

result = run_fixed_effects(
    spec,
    df,
    entity="firm_id",
    time="year",
)

print(result.summary_frame())
```

Equivalent Stata idea:

```stata
xtset firm_id year
xtreg y x1 x2 z1, fe
```

For two-way fixed effects, use the time-effect option supported by the installed version and confirm the returned model metadata before reporting results.

---

## Random Effects

```python
from systemgmmkit import RandomEffectsSpec, run_random_effects

spec = RandomEffectsSpec(
    dependent="y",
    regressors=["x1", "x2"],
    controls=["z1"],
)

result = run_random_effects(
    spec,
    df,
    entity="firm_id",
    time="year",
)

print(result.summary_frame())
```

Equivalent Stata idea:

```stata
xtset firm_id year
xtreg y x1 x2 z1, re
```

---

## Panel IV / 2SLS

```python
from systemgmmkit import PanelIVSpec, run_panel_2sls

spec = PanelIVSpec(
    dependent="y",
    exogenous=["x1", "z1"],
    endogenous=["x2"],
    instruments=["z2"],
)

result = run_panel_2sls(
    spec,
    df,
    entity="firm_id",
    time="year",
)

print(result.summary_frame())
```

Equivalent Stata idea:

```stata
ivregress 2sls y x1 z1 (x2 = z2)
```

---

# Dynamic Panel GMM Estimation

`systemgmmkit` supports both Difference GMM and System GMM for dynamic panel-data analysis.

The recommended workflow is:

1. Define the model specification.
2. Classify regressors according to their exogeneity assumptions.
3. Define the instrument strategy.
4. Run the estimator.
5. Review diagnostics before interpreting coefficients.
6. Export or report results.

The same workflow applies whether estimating Difference GMM or System GMM.

---

# Variable Classification Guide

Correct variable classification is one of the most important modelling decisions in dynamic-panel estimation.

| Classification | Interpretation                                  | Examples                                   |
| -------------- | ----------------------------------------------- | ------------------------------------------ |
| Endogenous     | May be correlated with current disturbances     | investment, aid, leverage, R&D             |
| Predetermined  | May react to past shocks but not current shocks | cashflow, backlog, lagged policy variables |
| Exogenous      | Assumed independent of the disturbance process  | firm size, year dummies, industry dummies  |

Researchers should perform robustness checks using alternative classifications when the theoretical justification is uncertain.

---

# Lagged Variables in Dynamic GMM

There are two different uses of lags in dynamic GMM.

| Use                           | Meaning                                               | Example                         |
| ----------------------------- | ----------------------------------------------------- | ------------------------------- |
| Lagged variable in the model  | The lag enters the structural equation as a regressor | `L1_investment` in `regressors` |
| Lagged variable as instrument | Past values are used internally as GMM instruments    | `gmm_lags=(2, 4)`               |

If a lagged version of an endogenous, predetermined, or exogenous variable should enter the model directly, create that lag in the data first and include it in `regressors`.

The current public API treats lagged regressors as ordinary columns supplied by the user. It does not automatically create `L1_` variables in the structural equation.

---

## Create lags before estimation

```python
df = df.sort_values(["firm_id", "year"]).copy()

df["L1_y"] = df.groupby("firm_id")["y"].shift(1)
df["L1_investment"] = df.groupby("firm_id")["investment"].shift(1)
df["L2_investment"] = df.groupby("firm_id")["investment"].shift(2)
df["L1_cashflow"] = df.groupby("firm_id")["cashflow"].shift(1)
df["L2_cashflow"] = df.groupby("firm_id")["cashflow"].shift(2)
df["L1_firm_size"] = df.groupby("firm_id")["firm_size"].shift(1)

df = df.dropna(
    subset=[
        "L1_y",
        "L1_investment",
        "L2_investment",
        "L1_cashflow",
        "L2_cashflow",
        "L1_firm_size",
    ]
)
```

---

## Lagged endogenous variables

A lagged endogenous variable can be included directly in the structural equation.

```python
regressors = [
    "L1_y",
    "investment",
    "L1_investment",
    "L2_investment",
    "firm_size",
]

endogenous = [
    "L1_y",
    "investment",
    "L1_investment",
    "L2_investment",
]

exogenous = [
    "firm_size",
]
```

In this example, `L1_investment` and `L2_investment` are model regressors. They are also classified as endogenous because the maintained assumption is that lagged investment is still not strictly exogenous.

---

## Lagged predetermined variables

A lagged predetermined variable can also be included directly in the structural equation.

```python
regressors = [
    "L1_y",
    "cashflow",
    "L1_cashflow",
    "L2_cashflow",
    "firm_size",
]

endogenous = [
    "L1_y",
]

predetermined = [
    "cashflow",
    "L1_cashflow",
    "L2_cashflow",
]

exogenous = [
    "firm_size",
]
```

Lagging a predetermined variable does not automatically make it exogenous. A lagged predetermined variable should usually remain classified as predetermined unless there is a strong theoretical reason to treat it as exogenous.

---

## Lagged exogenous variables

A lagged exogenous variable can be included directly in the structural equation.

```python
regressors = [
    "L1_y",
    "investment",
    "firm_size",
    "L1_firm_size",
]

endogenous = [
    "L1_y",
    "investment",
]

exogenous = [
    "firm_size",
    "L1_firm_size",
]
```

A lagged exogenous variable may be classified as exogenous only if strict exogeneity across time is defensible. If strict exogeneity is too strong, classify the lagged variable as predetermined instead.

---

## Current 0.5.9 lag-window rule

In version `0.5.9`, the public API supports a specification-level GMM instrument lag window:

```python
gmm_lags=(2, 4)
```

This means that the maintained GMM instrument lag-window strategy is applied at the specification level.

Different structural lags are supported by manually creating lagged columns:

```python
regressors = [
    "L1_y",
    "investment",
    "L1_investment",
    "L2_investment",
    "cashflow",
    "L1_cashflow",
    "L2_cashflow",
    "firm_size",
    "L1_firm_size",
]
```

However, in the documented `0.5.9` public API, role-specific or variable-specific GMM instrument lag windows should not be documented as current functionality unless the installed version explicitly supports them.

Do not document this as current `0.5.9` functionality:

```python
gmm_lags_by_role = {
    "endogenous": (2, 5),
    "predetermined": (1, 3),
}
```

Do not document this as current `0.5.9` functionality:

```python
gmm_lags_by_variable = {
    "investment": (2, 5),
    "cashflow": (1, 3),
}
```

These are planned next-release features.

---

# Difference GMM

Difference GMM is often appropriate when:

* the model contains a lagged dependent variable;
* regressors may be endogenous or predetermined;
* unobserved individual effects must be removed;
* the panel has many entities and relatively few time periods.

The public API consists of:

```python
from systemgmmkit import (
    build_difference_gmm_spec,
    run_difference_gmm,
)
```

---

## Basic Difference GMM

```python
from systemgmmkit import build_difference_gmm_spec, run_difference_gmm

spec = build_difference_gmm_spec(
    dependent="y",
    regressors=[
        "L1_y",
        "investment",
        "firm_size",
    ],
    endogenous=[
        "L1_y",
        "investment",
    ],
    exogenous=[
        "firm_size",
    ],
    gmm_lags=(2, 4),
    collapse=True,
)

result = run_difference_gmm(
    spec,
    data=df,
    entity="firm_id",
    time="year",
    backend="auto",
)

print(result)
```

Equivalent Stata idea:

```stata
xtabond2 y L.y investment firm_size, ///
    gmm(L.y investment, lag(2 4) collapse) ///
    iv(firm_size) ///
    robust
```

---

## Difference GMM with Endogenous Variables

Use endogenous classification when a regressor may be correlated with current shocks.

```python
spec = build_difference_gmm_spec(
    dependent="y",
    regressors=[
        "L1_y",
        "investment",
        "firm_size",
    ],
    endogenous=[
        "L1_y",
        "investment",
    ],
    exogenous=[
        "firm_size",
    ],
    gmm_lags=(2, 4),
    collapse=True,
)
```

Common examples of endogenous regressors include:

* investment;
* leverage;
* aid flows;
* credit supply;
* R&D spending;
* production decisions.

---

## Difference GMM with Predetermined Variables

Use predetermined classification when a variable may respond to past shocks but is assumed not to respond contemporaneously.

```python
spec = build_difference_gmm_spec(
    dependent="y",
    regressors=[
        "L1_y",
        "cashflow",
        "firm_size",
    ],
    endogenous=[
        "L1_y",
    ],
    predetermined=[
        "cashflow",
    ],
    exogenous=[
        "firm_size",
    ],
    gmm_lags=(2, 4),
    collapse=True,
)
```

Common examples of predetermined variables include:

* cash flow;
* lagged policy variables;
* operational backlog;
* maintenance workload;
* delayed implementation measures.

---

## Difference GMM with Exogenous Variables

Use exogenous classification when the variable is assumed independent of the disturbance process.

```python
spec = build_difference_gmm_spec(
    dependent="y",
    regressors=[
        "L1_y",
        "investment",
        "firm_size",
        "year2022",
        "year2023",
    ],
    endogenous=[
        "L1_y",
        "investment",
    ],
    exogenous=[
        "firm_size",
        "year2022",
        "year2023",
    ],
    gmm_lags=(2, 4),
    collapse=True,
)
```

Common examples of exogenous variables include:

* time dummies;
* industry dummies;
* country dummies;
* externally determined controls.

---

## Difference GMM with Instrument Control

Instrument count should generally be controlled to reduce overfitting and avoid weakening the Hansen test.

```python
spec = build_difference_gmm_spec(
    dependent="y",
    regressors=[
        "L1_y",
        "investment",
        "cashflow",
        "firm_size",
    ],
    endogenous=[
        "L1_y",
        "investment",
    ],
    predetermined=[
        "cashflow",
    ],
    exogenous=[
        "firm_size",
    ],
    gmm_lags=(2, 4),
    collapse=True,
)
```

Recommended practice:

* keep the instrument count below the number of groups where possible;
* use collapsed instruments when appropriate;
* report the number of instruments;
* report AR(1), AR(2), Hansen, and Sargan diagnostics;
* test alternative lag windows as robustness checks.

---

# System GMM

System GMM extends Difference GMM by combining:

* the differenced equation; and
* the levels equation.

System GMM is often preferred when variables are highly persistent and lagged levels are weak instruments for differenced variables.

The public API consists of:

```python
from systemgmmkit import (
    build_system_gmm_spec,
    run_system_gmm,
)
```

---

## Basic System GMM

```python
from systemgmmkit import build_system_gmm_spec, run_system_gmm

spec = build_system_gmm_spec(
    dependent="y",
    regressors=[
        "L1_y",
        "investment",
        "firm_size",
    ],
    endogenous=[
        "L1_y",
        "investment",
    ],
    exogenous=[
        "firm_size",
    ],
    gmm_lags=(2, 4),
    collapse=True,
    windmeijer=True,
)

result = run_system_gmm(
    spec,
    data=df,
    entity="firm_id",
    time="year",
    backend="auto",
)

print(result)
```

Equivalent Stata idea:

```stata
xtabond2 y L.y investment firm_size, ///
    gmm(L.y investment, lag(2 4) collapse) ///
    iv(firm_size) ///
    twostep robust small
```

---

## System GMM with Endogenous Variables

```python
spec = build_system_gmm_spec(
    dependent="y",
    regressors=[
        "L1_y",
        "investment",
        "firm_size",
    ],
    endogenous=[
        "L1_y",
        "investment",
    ],
    exogenous=[
        "firm_size",
    ],
    gmm_lags=(2, 4),
    collapse=True,
    windmeijer=True,
)
```

---

## System GMM with Predetermined Variables

```python
spec = build_system_gmm_spec(
    dependent="y",
    regressors=[
        "L1_y",
        "cashflow",
        "firm_size",
    ],
    endogenous=[
        "L1_y",
    ],
    predetermined=[
        "cashflow",
    ],
    exogenous=[
        "firm_size",
    ],
    gmm_lags=(2, 4),
    collapse=True,
    windmeijer=True,
)
```

---

## System GMM with Multiple Variable Types

```python
spec = build_system_gmm_spec(
    dependent="y",
    regressors=[
        "L1_y",
        "investment",
        "cashflow",
        "firm_size",
        "year2022",
        "year2023",
    ],
    endogenous=[
        "L1_y",
        "investment",
    ],
    predetermined=[
        "cashflow",
    ],
    exogenous=[
        "firm_size",
        "year2022",
        "year2023",
    ],
    gmm_lags=(2, 4),
    collapse=True,
    windmeijer=True,
)
```

---

## System GMM with lagged endogenous, predetermined, and exogenous regressors

```python
from systemgmmkit import build_system_gmm_spec, run_system_gmm

spec = build_system_gmm_spec(
    dependent="y",
    regressors=[
        "L1_y",
        "investment",
        "L1_investment",
        "L2_investment",
        "cashflow",
        "L1_cashflow",
        "L2_cashflow",
        "firm_size",
        "L1_firm_size",
    ],
    endogenous=[
        "L1_y",
        "investment",
        "L1_investment",
        "L2_investment",
    ],
    predetermined=[
        "cashflow",
        "L1_cashflow",
        "L2_cashflow",
    ],
    exogenous=[
        "firm_size",
        "L1_firm_size",
    ],
    gmm_lags=(2, 4),
    collapse=True,
    windmeijer=True,
)

result = run_system_gmm(
    spec,
    data=df,
    entity="firm_id",
    time="year",
    backend="auto",
)
```

System GMM uses both the differenced equation and the levels equation. The same distinction still applies: lagged variables in `regressors` are model covariates, while `gmm_lags` controls the instrument lag window.

---

## Equivalent Stata idea

```stata
xtabond2 y L.y investment L.investment L2.investment ///
    cashflow L.cashflow L2.cashflow firm_size L.firm_size, ///
    gmm(L.y investment L.investment L2.investment, lag(2 4) collapse) ///
    gmm(cashflow L.cashflow L2.cashflow, lag(2 4) collapse) ///
    iv(firm_size L.firm_size) ///
    twostep robust small
```

This Stata command illustrates the same separation:

* `L.investment` and `L2.investment` appear in the model equation and are treated as GMM-style endogenous variables;
* `L.cashflow` and `L2.cashflow` appear in the model equation and are treated as GMM-style predetermined variables;
* `L.firm_size` appears in the model equation and is treated as IV-style exogenous;
* `lag(2 4)` controls which lagged values are used as instruments;
* `collapse` limits the number of instruments.

---

## Important Modelling Note

Do not confuse these two decisions:

```python
regressors = ["L1_investment"]
```

means:

```text
Include lagged investment as an explanatory variable.
```

while:

```python
gmm_lags = (2, 4)
```

means:

```text
Use lagged values, usually lags 2 through 4, as GMM instruments.
```

For the current public API, `gmm_lags=(2, 4)` applies the maintained lag-window strategy at the specification level.

Safe rule:

```text
Create lagged regressors yourself when they belong in the model equation.
Classify each lagged regressor according to its maintained exogeneity assumption.
Use gmm_lags only to control the instrument lag window.
```

---

# Backend Selection

By default, dynamic GMM estimators use:

```python
backend="auto"
```

Example:

```python
result = run_system_gmm(
    spec,
    data=df,
    entity="firm_id",
    time="year",
    backend="auto",
)
```

The `auto` backend routes estimation through the preferred supported implementation available in the installed package.

Use explicit backend selection only when you need to test a specific implementation path.

---

# Dynamic GMM Diagnostics

For dynamic-panel GMM models, users should inspect diagnostics before interpreting coefficients.

Recommended diagnostics include:

* number of observations;
* number of groups;
* number of instruments;
* AR(1) test;
* AR(2) test;
* Hansen test;
* Sargan test;
* covariance estimator;
* one-step or two-step setting;
* Windmeijer correction status;
* estimation backend.

A statistically significant AR(1) test is expected in many differenced dynamic-panel models. The AR(2) test is usually more important for checking second-order serial correlation in differenced residuals.

The Hansen and Sargan tests should not be interpreted mechanically. Very high Hansen p-values can indicate instrument proliferation, while very low p-values may indicate invalid instruments or misspecification.

---

# Recommended Dynamic GMM Reporting

For published research, report:

* dependent variable;
* sample period;
* number of observations;
* number of groups;
* estimator type;
* transformation;
* lagged dependent variable treatment;
* endogenous variables;
* predetermined variables;
* exogenous variables;
* structural lags included in the model;
* GMM lag window;
* collapse setting;
* number of instruments;
* AR(1) diagnostic;
* AR(2) diagnostic;
* Hansen test;
* Sargan test;
* covariance estimator;
* Windmeijer correction status;
* estimation backend;
* package version.

This makes the empirical specification more transparent and easier to replicate.

---

# Post-Estimation

Version `0.5.9` includes the first public post-estimation framework.

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

Equivalent Stata idea:

```stata
predict yhat
```

Python:

```python
pred = predict(result)
```

or:

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

Equivalent Stata idea:

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

Equivalent Stata idea:

```stata
lincom x1 + x2
```

Python:

```python
effect = lincom(
    result,
    {
        "x1": 1,
        "x2": 1,
    },
)

print(effect)
```

Expected output includes:

* estimate;
* standard error;
* test statistic;
* p-value;
* confidence interval.

---

## Wald Tests

Equivalent Stata idea:

```stata
test x1 x2
```

Python:

```python
test_result = wald_test(
    result,
    R=[
        [0, 1, 0],
        [0, 0, 1],
    ],
)

print(test_result)
```

Expected output includes:

* Wald statistic;
* degrees of freedom;
* p-value.

---

## Marginal Effects

```python
me = marginal_effects(result)

print(me)
```

For linear estimators, marginal effects correspond to estimated slopes.

For nonlinear or interaction-heavy models, users should verify how the marginal effect is defined and whether additional manual computation is required.

---

# Reporting and Export

Results can be exported to:

* Markdown;
* CSV;
* LaTeX.

`systemgmmkit` is designed to integrate with:

* `universal-output-hub`;
* publication pipelines;
* reproducible research workflows;
* model-comparison tables.

Recommended reporting fields include:

* estimator;
* dependent variable;
* specification;
* covariance estimator;
* number of observations;
* number of groups;
* instrument count;
* AR diagnostics;
* Hansen diagnostics;
* Sargan diagnostics;
* backend;
* package version.

---

# Example Reporting Workflow with universal-output-hub

```python
from universal_output_hub import outreg

outreg(
    [result],
    model_names=["System GMM"],
    path="tables/system_gmm_results.md",
)
```

The reporting layer is intentionally separate from estimation. This allows users to estimate models in `systemgmmkit` and export publication-style tables through `universal-output-hub`.

---

# Practical Modelling Guidance

## Use OLS and panel estimators as baselines

Dynamic GMM should not usually be the first model estimated.

A defensible empirical workflow often starts with:

1. OLS or pooled OLS;
2. fixed effects;
3. random effects where appropriate;
4. IV / 2SLS where identification requires external instruments;
5. Difference GMM or System GMM for dynamic-panel settings.

This helps users understand how estimates change across assumptions.

---

## Control instrument proliferation

Instrument proliferation is one of the most common problems in applied dynamic GMM.

Recommended practice:

* use `collapse=True`;
* restrict `gmm_lags`;
* report instrument count;
* compare instrument count with number of groups;
* check whether Hansen p-values are suspiciously high;
* run robustness checks with alternative lag windows.

---

## Do not overinterpret one specification

Dynamic GMM estimates are sensitive to:

* lag-window choices;
* variable classification;
* transformation choice;
* instrument count;
* sample construction;
* missing-value handling;
* persistence of the dependent variable;
* weak instruments.

Users should treat dynamic GMM as part of a specification family, not as a single automatic estimator.

---

# Next Release Roadmap

The next release should extend the dynamic GMM API to support role-specific and variable-specific GMM instrument lag windows.

This feature is not documented as current `0.5.9` functionality. It is the recommended next implementation target.

---

## Planned role-specific GMM lag windows

The next release should support different GMM instrument lag windows for endogenous and predetermined variables.

Planned API:

```python
spec = build_system_gmm_spec(
    dependent="y",
    regressors=[
        "L1_y",
        "investment",
        "L1_investment",
        "cashflow",
        "L1_cashflow",
        "firm_size",
    ],
    endogenous=[
        "L1_y",
        "investment",
        "L1_investment",
    ],
    predetermined=[
        "cashflow",
        "L1_cashflow",
    ],
    exogenous=[
        "firm_size",
    ],
    gmm_lags=(2, 4),
    gmm_lags_by_role={
        "endogenous": (2, 5),
        "predetermined": (1, 3),
    },
    collapse=True,
    windmeijer=True,
)
```

Equivalent Stata idea:

```stata
xtabond2 y L.y investment L.investment cashflow L.cashflow firm_size, ///
    gmm(L.y investment L.investment, lag(2 5) collapse) ///
    gmm(cashflow L.cashflow, lag(1 3) collapse) ///
    iv(firm_size) ///
    twostep robust small
```

In this planned API:

* endogenous variables can use one GMM lag window;
* predetermined variables can use another GMM lag window;
* exogenous variables remain IV-style by default.

---

## Planned variable-specific GMM lag windows

The next release should also support variable-specific overrides.

Planned API:

```python
spec = build_system_gmm_spec(
    dependent="y",
    regressors=[
        "L1_y",
        "investment",
        "L1_investment",
        "cashflow",
        "L1_cashflow",
        "firm_size",
    ],
    endogenous=[
        "L1_y",
        "investment",
        "L1_investment",
    ],
    predetermined=[
        "cashflow",
        "L1_cashflow",
    ],
    exogenous=[
        "firm_size",
    ],
    gmm_lags=(2, 4),
    gmm_lags_by_role={
        "endogenous": (2, 5),
        "predetermined": (1, 3),
    },
    gmm_lags_by_variable={
        "L1_y": (2, 4),
        "investment": (3, 5),
        "L1_investment": (3, 6),
        "cashflow": (1, 2),
        "L1_cashflow": (2, 3),
    },
    collapse=True,
    windmeijer=True,
)
```

The planned precedence rule should be:

```text
gmm_lags_by_variable > gmm_lags_by_role > gmm_lags
```

Meaning:

* if a variable has a variable-specific lag window, use that;
* otherwise use its role-specific lag window;
* otherwise fall back to the global `gmm_lags`.

---

## Planned treatment of exogenous variables

Exogenous variables should remain IV-style by default.

Recommended design:

```python
exogenous = [
    "firm_size",
    "L1_firm_size",
]
```

The next release should not force exogenous variables into GMM-style instrumentation.

If users need lagged exogenous variables in the model equation, they should still create those structural lags manually:

```python
df["L1_firm_size"] = df.groupby("firm_id")["firm_size"].shift(1)
```

Then include them as regressors and classify them as exogenous if strict exogeneity is defensible:

```python
regressors = [
    "firm_size",
    "L1_firm_size",
]

exogenous = [
    "firm_size",
    "L1_firm_size",
]
```

If strict exogeneity is too strong, the lagged variable should be classified as predetermined instead.

---

## Planned validation requirements for the next release

Before role-specific and variable-specific lag windows are released, the implementation should include:

* unit tests for global `gmm_lags`;
* unit tests for `gmm_lags_by_role`;
* unit tests for `gmm_lags_by_variable`;
* precedence tests for variable-level overrides;
* tests confirming exogenous variables remain IV-style unless explicitly handled otherwise;
* Difference GMM parity checks;
* System GMM parity checks;
* instrument-count checks;
* instrument-name checks;
* collapsed and uncollapsed instrument tests;
* documentation examples;
* Stata comparison scripts using separate `gmm()` blocks.

Definition of done:

```text
The next release should allow users to assign different GMM instrument lag windows to endogenous and predetermined variables, and should allow variable-specific overrides, without breaking backward compatibility with gmm_lags=(2, 4).
```

---

# Citation

If you use `systemgmmkit` in academic work, please cite:

```text
Akanbi, Oluwajuwon Mayomi.

systemgmmkit:
Panel Data Econometrics and Dynamic GMM Workflows in Python.

Version 0.5.9.

https://github.com/Akanom/systemgmmkit
```

BibTeX:

```bibtex
@software{akanbi_systemgmmkit,
  author = {Akanbi, Oluwajuwon Mayomi},
  title = {systemgmmkit: Panel Data Econometrics and Dynamic GMM Workflows in Python},
  year = {2026},
  url = {https://github.com/Akanom/systemgmmkit},
  version = {0.5.9}
}
```

Replace or supplement this citation with DOI information once a Zenodo archive or software paper is available.

---

# License

MIT License.

See `LICENSE` for details.
