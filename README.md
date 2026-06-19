# systemgmmkit

[![PyPI version](https://img.shields.io/pypi/v/systemgmmkit.svg)](https://pypi.org/project/systemgmmkit/)
[![Python versions](https://img.shields.io/pypi/pyversions/systemgmmkit.svg)](https://pypi.org/project/systemgmmkit/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://github.com/Akanom/systemgmmkit/actions/workflows/ci.yml/badge.svg)](https://github.com/Akanom/systemgmmkit/actions/workflows/ci.yml)
[![Publish](https://github.com/Akanom/systemgmmkit/actions/workflows/publish.yml/badge.svg)](https://github.com/Akanom/systemgmmkit/actions/workflows/publish.yml)

---

# systemgmmkit 0.5.10

`systemgmmkit` is a Python package for applied panel-data econometrics. It provides a unified workflow for baseline linear models, panel estimators, instrumental-variable models, dynamic-panel GMM estimation, diagnostics, post-estimation, visualization, and reproducible reporting.

The package currently supports:

* Ordinary Least Squares;
* Pooled OLS;
* Fixed Effects;
* Random Effects;
* Panel IV / 2SLS;
* Difference GMM;
* System GMM;
* Windmeijer-corrected two-step dynamic GMM;
* Hansen, Sargan, AR(1), and AR(2) diagnostics;
* post-estimation utilities;
* standard post-estimation graphics;
* SGM-Viz diagnostic dashboards;
* result-level plotting accessors;
* HTML / PNG / SVG / PDF-compatible reporting workflows;
* integration with `universal-output-hub`.

`systemgmmkit` is designed for empirical researchers working in economics, finance, management, operations, productivity analysis, public policy, development economics, political economy, industrial organization, and other panel-data settings.

---

# Why systemgmmkit?

Applied panel-data research often requires several disconnected tools:

* baseline OLS models;
* pooled panel regressions;
* fixed-effects and random-effects models;
* instrumental-variable models;
* dynamic-panel GMM models;
* diagnostic tests;
* post-estimation analysis;
* publication tables;
* diagnostic figures;
* reproducible exports.

`systemgmmkit` aims to bring these pieces into a consistent Python API.

The package is built around five principles:

1. **Explicit model specification**
   Model assumptions should be visible in the code, not hidden inside estimation defaults.

2. **Reproducible empirical workflows**
   Estimation, diagnostics, post-estimation, visualization, and reporting should be easy to rerun and inspect.

3. **Transparent dynamic-panel diagnostics**
   Dynamic-panel GMM results should expose sample size, instrument count, AR tests, Hansen/Sargan tests, covariance type, backend metadata, and instrument architecture.

4. **Verification against reference implementations**
   Estimators are benchmarked against established Stata implementations where practical.

5. **Publication-oriented communication**
   Results should be interpretable not only as coefficient tables, but also through diagnostics, model-health dashboards, persistence plots, instrument-architecture displays, and report-ready graphics.

The objective is not only to estimate models. The objective is to make modelling choices clear enough for replication, review, publication, and applied decision-making.

---

# What's New in 0.5.10

Version `0.5.10` is a post-estimation, graphics, and diagnostic-reporting release.

It builds on the `0.5.9` estimator and post-estimation foundation by adding a complete visualization layer for applied panel-data workflows.

## SGM-Viz v2 diagnostic dashboards

New flagship visualization APIs include:

* `HealthMetrics`
* `InstrumentArchitecture`
* `PersistenceAnalytics`
* `model_health_dashboard_v2()`
* `dynamic_persistence_dashboard_v2()`
* `instrument_architecture_dashboard_v2()`
* `effect_surface_dashboard_v2()`
* `publication_panel_v2()`
* `export_sgm_viz_v2_gallery()`
* `export_sgm_viz_report()`
* `model_comparison_dashboard_v2()`

These plots are designed specifically for dynamic-panel workflows. They are not generic chart wrappers.

## Result-level plotting API

Version `0.5.10` adds result-level plotting accessors:

```python
result.plot.health()
result.plot.persistence()
result.plot.instruments()
result.plot.publication_panel()
result.plot.standard_gallery()
result.plot.export_all()
```

For result objects that do not support direct `.plot` attachment, use:

```python
from systemgmmkit.postestimation import plot_accessor

viz = plot_accessor(result)

viz.health()
viz.persistence()
viz.instruments()
viz.publication_panel()
viz.standard_gallery("outputs/standard_gallery")
```

## Standard post-estimation graphics gallery

Version `0.5.10` also adds a standard R/Stata-style post-estimation graphics gallery:

* coefficient / parameter impact plot;
* marginal effects plot;
* margins / prediction plot;
* conditional effects plot;
* interaction plot;
* residuals vs fitted plot;
* QQ plot of residuals;
* residual histogram / density profile;
* panel trajectory plot;
* fixed-effects / unit-effects plot;
* instrument count plot;
* Hansen / Sargan / AR diagnostics plot;
* counterfactual scenario plot;
* 3D / effect-surface plot.

The full gallery can be exported in one command:

```python
result.plot.standard_gallery(
    "outputs/standard_gallery",
    prefix="model",
)
```

or:

```python
from systemgmmkit.postestimation import export_standard_postestimation_gallery

gallery = export_standard_postestimation_gallery(
    result,
    output_dir="outputs/standard_gallery",
    prefix="model",
)
```

## Report modes

SGM-Viz HTML reports support three report modes:

```text
dashboard    = individual dashboards only
publication  = composed publication panel only
full         = all figures, including repeated components
```

Example:

```python
result.plot.export_all(
    "outputs/sgm_report",
    gallery_mode="dashboard",
)
```

For a paper-style one-page summary figure:

```python
result.plot.export_all(
    "outputs/paper_report",
    gallery_mode="publication",
)
```

## Single-plot usage

Users can generate one figure directly without creating a full gallery:

```python
result.plot.health(save="outputs/health.png")
result.plot.persistence(save="outputs/persistence.png")
result.plot.instruments(save="outputs/instruments.png")
result.plot.publication_panel(save="outputs/publication_panel.png")
```

Standard plots are also directly callable:

```python
from systemgmmkit.postestimation import coefficient_plot

coefficient_plot(
    result,
    save="outputs/coefficient_plot.png",
)
```

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
* Hansen diagnostics
* Sargan diagnostics
* Arellano-Bond AR(1) diagnostics
* Arellano-Bond AR(2) diagnostics

## Post-Estimation

* Predictions
* Fitted values
* Residuals
* Variance-covariance extraction
* Confidence intervals
* Linear combinations
* Wald tests
* Marginal effects for linear estimators

## Graphics and Diagnostics

* Coefficient plots
* Marginal effects plots
* Prediction / margins plots
* Interaction plots
* Conditional effects plots
* Residual diagnostics
* Fixed-effects plots
* Panel trajectory plots
* Instrument count plots
* Hansen / AR diagnostic plots
* Counterfactual scenario plots
* 3D effect surfaces
* SGM-Viz model-health dashboards
* SGM-Viz persistence analytics
* SGM-Viz instrument architecture dashboards
* SGM-Viz publication panels
* HTML gallery export
* PNG / SVG / PDF-compatible figure export

## Reporting

* Markdown export
* CSV export
* LaTeX export
* HTML figure galleries
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

For graphics support, ensure `matplotlib` is available:

```bash
pip install matplotlib
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
| SGM-Viz v2 dashboards      | PASS_TESTED_EXPORT    |
| Standard graphics gallery  | PASS_TESTED_EXPORT    |
| Result plot accessors      | PASS_TESTED_EXPORT    |

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

1. Define the structural model.
2. Create any lagged variables that should enter the model equation.
3. Classify regressors as endogenous, predetermined, or exogenous.
4. Define the GMM instrument strategy.
5. Run the estimator.
6. Inspect diagnostics before interpreting coefficients.
7. Export tables and diagnostic figures.

The same workflow applies whether estimating Difference GMM or System GMM.

---

# Variable Classification Guide

Correct variable classification is one of the most important modelling decisions in dynamic-panel estimation.

| Classification | Interpretation                                       | Typical instrument treatment                                                        | Examples                                                                     |
| -------------- | ---------------------------------------------------- | ----------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| Endogenous     | May be correlated with current and past disturbances | GMM-style instruments using deeper lags                                             | investment, aid, leverage, R&D, production decisions                         |
| Predetermined  | May react to past shocks but not current shocks      | GMM-style instruments, often allowing shorter lag windows than endogenous variables | cash flow, backlog, lagged policy variables, delayed implementation measures |
| Exogenous      | Assumed independent of the disturbance process       | IV-style instruments by default                                                     | firm size, year dummies, industry dummies, externally determined controls    |

Researchers should perform robustness checks using alternative classifications when the theoretical justification is uncertain.

---

# Structural Lags vs Instrument Lags

Dynamic GMM has two different uses of lags. They must not be confused.

| Use                          | Meaning                                               | Example                         |
| ---------------------------- | ----------------------------------------------------- | ------------------------------- |
| Lagged variable in the model | The lag enters the structural equation as a regressor | `L1_investment` in `regressors` |
| Lagged value as instrument   | Past values are used internally as GMM instruments    | `gmm_lags=(2, 4)`               |

This distinction is central.

```python
regressors = ["L1_investment"]
```

means:

```text
Include lagged investment as an explanatory variable in the model equation.
```

while:

```python
gmm_lags = (2, 4)
```

means:

```text
Use lags 2 through 4 as GMM instruments.
```

Safe rule:

```text
Create lagged regressors yourself when they belong in the model equation.
Classify each lagged regressor according to its maintained exogeneity assumption.
Use GMM lag-window arguments only to control instrument construction.
```

---

# Create Structural Lags Before Estimation

The public API treats lagged regressors as ordinary columns supplied by the user. It does not automatically create structural `L1_` or `L2_` model variables.

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

# Instrumenting Endogenous Variables

Use endogenous classification when a regressor may be correlated with current shocks.

Common endogenous variables include:

* lagged dependent variables;
* investment;
* aid flows;
* leverage;
* credit supply;
* R&D spending;
* production decisions;
* project implementation decisions.

Example:

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

predetermined = []

exogenous = [
    "firm_size",
]
```

In this example, `L1_investment` and `L2_investment` are included directly in the model equation and are also classified as endogenous. Lagging an endogenous variable does not automatically make it exogenous.

---

# Instrumenting Predetermined Variables

Use predetermined classification when a variable may respond to past shocks but is assumed not to respond contemporaneously.

Common predetermined variables include:

* cash flow;
* backlog;
* delayed implementation measures;
* lagged policy variables;
* maintenance workload;
* past operational pressure.

Example:

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

Lagging a predetermined variable does not automatically make it exogenous. A lagged predetermined variable should usually remain classified as predetermined unless strict exogeneity is theoretically defensible.

---

# Instrumenting Exogenous Variables

Exogenous variables are treated as IV-style instruments by default.

Example:

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

predetermined = []

exogenous = [
    "firm_size",
    "L1_firm_size",
]
```

A lagged exogenous variable may be classified as exogenous only if strict exogeneity across time is defensible. If strict exogeneity is too strong, classify the lagged variable as predetermined instead.

---

# GMM Lag-Window Strategy in 0.5.10

Version `0.5.10` supports three levels of GMM lag-window control:

1. global GMM lag window;
2. role-specific GMM lag windows;
3. variable-specific GMM lag windows.

The precedence rule is:

```text
gmm_lags_by_variable > gmm_lags_by_role > gmm_lags
```

Meaning:

* if a variable has a variable-specific lag window, use that;
* otherwise, if its role has a role-specific lag window, use that;
* otherwise, fall back to the global `gmm_lags`.

---

## Global GMM Lag Window

The global GMM lag window applies to all GMM-style variables unless overridden.

```python
gmm_lags = (2, 4)
```

This means GMM-style instruments are constructed using lags 2 through 4.

Example:

```python
spec = build_system_gmm_spec(
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
    windmeijer=True,
)
```

Equivalent Stata idea:

```stata
xtabond2 y L.y investment cashflow firm_size, ///
    gmm(L.y investment cashflow, lag(2 4) collapse) ///
    iv(firm_size) ///
    twostep robust small
```

---

## Role-Specific GMM Lag Windows

Role-specific GMM lag windows allow endogenous and predetermined variables to use different instrument lag ranges.

This is useful because predetermined variables may be validly instrumented with shorter lags than fully endogenous variables, depending on the maintained timing assumptions.

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

In this example:

* endogenous variables use lags 2 through 5;
* predetermined variables use lags 1 through 3;
* exogenous variables remain IV-style by default.

---

## Variable-Specific GMM Lag Windows

Variable-specific GMM lag windows allow individual variables to override both role-specific and global lag windows.

This is useful when some variables are more persistent, more weakly instrumented, or require a more conservative instrument strategy.

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

In this example:

| Variable        | Role          | Effective GMM lag window | Reason                     |
| --------------- | ------------- | -----------------------: | -------------------------- |
| `L1_y`          | endogenous    |                 `(2, 4)` | variable-specific override |
| `investment`    | endogenous    |                 `(3, 5)` | variable-specific override |
| `L1_investment` | endogenous    |                 `(3, 6)` | variable-specific override |
| `cashflow`      | predetermined |                 `(1, 2)` | variable-specific override |
| `L1_cashflow`   | predetermined |                 `(2, 3)` | variable-specific override |

The variable-specific settings override both:

```python
gmm_lags_by_role={
    "endogenous": (2, 5),
    "predetermined": (1, 3),
}
```

and:

```python
gmm_lags=(2, 4)
```

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

## Difference GMM with Role-Specific Instruments

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
    gmm_lags_by_role={
        "endogenous": (2, 5),
        "predetermined": (1, 3),
    },
    collapse=True,
)
```

Equivalent Stata idea:

```stata
xtabond2 y L.y investment cashflow firm_size, ///
    gmm(L.y investment, lag(2 5) collapse) ///
    gmm(cashflow, lag(1 3) collapse) ///
    iv(firm_size) ///
    robust
```

---

## Difference GMM with Variable-Specific Instruments

```python
spec = build_difference_gmm_spec(
    dependent="y",
    regressors=[
        "L1_y",
        "investment",
        "L1_investment",
        "cashflow",
        "firm_size",
    ],
    endogenous=[
        "L1_y",
        "investment",
        "L1_investment",
    ],
    predetermined=[
        "cashflow",
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
    },
    collapse=True,
)
```

Equivalent Stata idea:

```stata
xtabond2 y L.y investment L.investment cashflow firm_size, ///
    gmm(L.y, lag(2 4) collapse) ///
    gmm(investment, lag(3 5) collapse) ///
    gmm(L.investment, lag(3 6) collapse) ///
    gmm(cashflow, lag(1 2) collapse) ///
    iv(firm_size) ///
    robust
```

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

## System GMM with Endogenous, Predetermined, and Exogenous Variables

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

## System GMM with Role-Specific Instruments

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

---

## System GMM with Variable-Specific Instruments

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

Equivalent Stata idea:

```stata
xtabond2 y L.y investment L.investment cashflow L.cashflow firm_size, ///
    gmm(L.y, lag(2 4) collapse) ///
    gmm(investment, lag(3 5) collapse) ///
    gmm(L.investment, lag(3 6) collapse) ///
    gmm(cashflow, lag(1 2) collapse) ///
    gmm(L.cashflow, lag(2 3) collapse) ///
    iv(firm_size) ///
    twostep robust small
```

---

# Exogenous Variables Remain IV-Style by Default

Exogenous variables should remain IV-style by default.

```python
exogenous = [
    "firm_size",
    "L1_firm_size",
]
```

The package should not force exogenous variables into GMM-style instrumentation.

If users need lagged exogenous variables in the model equation, they should create those structural lags manually:

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

# Instrument Control

Instrument count should be controlled to reduce overfitting and avoid weakening the Hansen test.

Recommended practice:

* keep the instrument count below the number of groups where possible;
* use collapsed instruments when appropriate;
* restrict GMM lag windows;
* use role-specific lag windows where theoretically justified;
* use variable-specific lag windows where persistence or weak-instrument concerns differ by variable;
* report the number of instruments;
* report AR(1), AR(2), Hansen, and Sargan diagnostics;
* compare alternative lag-window choices as robustness checks.

---

# Instrument Architecture Reporting

Version `0.5.10` supports instrument-architecture reporting through SGM-Viz.

```python
from systemgmmkit.postestimation import InstrumentArchitecture

architecture = InstrumentArchitecture(
    estimator="System GMM",
    difference_equation=(
        "L2.y",
        "L3.y",
        "L2.investment",
        "L3.investment",
    ),
    level_equation=(
        "D.y",
        "D.investment",
    ),
    standard_instruments=(
        "firm_size",
        "time effects",
    ),
    lag_range=(2, 4),
    collapsed=True,
    transformation="FOD",
    total_instruments=result.instruments,
    groups=result.groups,
)

result.plot.instruments(
    architecture=architecture,
    save="outputs/instrument_architecture.png",
)
```

For role-specific or variable-specific instrument designs, the instrument architecture should document the actual instrument blocks used in the model.

---

# Dynamic GMM Diagnostics

For dynamic-panel GMM models, users should inspect diagnostics before interpreting coefficients.

Recommended diagnostics include:

* number of observations;
* number of groups;
* number of instruments;
* instrument/group ratio;
* AR(1) test;
* AR(2) test;
* Hansen test;
* Sargan test;
* covariance estimator;
* one-step or two-step setting;
* Windmeijer correction status;
* transformation;
* estimation backend;
* instrument architecture.

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
* global GMM lag window;
* role-specific GMM lag windows, if used;
* variable-specific GMM lag windows, if used;
* collapse setting;
* number of instruments;
* instrument/group ratio;
* AR(1) diagnostic;
* AR(2) diagnostic;
* Hansen test;
* Sargan test;
* covariance estimator;
* Windmeijer correction status;
* estimation backend;
* package version;
* model-health dashboard or equivalent diagnostics.

---

# Post-Estimation Utilities

Version `0.5.10` includes public post-estimation utilities.

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

## Predictions

```python
pred = predict(result)
```

or:

```python
pred = result.predict()
```

## Fitted Values

```python
fit = fitted_values(result)
```

## Residuals

```python
resid = residuals(result)
```

## Variance-Covariance Matrix

```python
V = vcov(result)
```

## Confidence Intervals

```python
ci = confint(result)
```

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

## Marginal Effects

```python
me = marginal_effects(result)

print(me)
```

For linear estimators, marginal effects correspond to estimated slopes.

---

# Standard Post-Estimation Graphics

Version `0.5.10` includes standard post-estimation plot functions.

## Coefficient plot

```python
from systemgmmkit.postestimation import coefficient_plot

coefficient_plot(
    result,
    style="sgm",
    preset="paper",
    save="outputs/coefficient_plot.png",
)
```

## Marginal effects plot

```python
from systemgmmkit.postestimation import marginal_effects_plot

marginal_effects_plot(
    effects_df,
    style="sgm",
    preset="paper",
    save="outputs/marginal_effects.png",
)
```

Expected input:

```python
effects_df = pd.DataFrame({
    "term": ["techshare", "polity", "fragility"],
    "effect": [0.18, 0.04, -0.09],
    "std_error": [0.04, 0.02, 0.03],
})
```

## Margins / prediction plot

```python
from systemgmmkit.postestimation import margins_prediction_plot

margins_prediction_plot(
    margins_df,
    x="techshare",
    y="pred",
    lower="lo",
    upper="hi",
    group="polity_group",
    save="outputs/prediction_plot.png",
)
```

## Interaction plot

```python
from systemgmmkit.postestimation import interaction_plot

interaction_plot(
    interaction_df,
    x="techshare",
    y="pred",
    moderator="fragility_group",
    lower="lo",
    upper="hi",
    save="outputs/interaction_plot.png",
)
```

## Residual diagnostics

```python
from systemgmmkit.postestimation import (
    residuals_vs_fitted_plot,
    qq_residual_plot,
    residual_histogram,
)

residuals_vs_fitted_plot(result, save="outputs/residuals_vs_fitted.png")
qq_residual_plot(result.residuals, save="outputs/qq_residuals.png")
residual_histogram(result.residuals, save="outputs/residual_histogram.png")
```

## Hansen / AR diagnostic plot

```python
from systemgmmkit.postestimation import hansen_ar_diagnostic_plot

hansen_ar_diagnostic_plot(
    {
        "Hansen": result.hansen_p,
        "Sargan": result.sargan_p,
        "AR(1)": result.ar1_p,
        "AR(2)": result.ar2_p,
    },
    save="outputs/hansen_ar_diagnostics.png",
)
```

---

# Standard Post-Estimation Gallery

To export the complete standard plot gallery:

```python
from systemgmmkit.postestimation import export_standard_postestimation_gallery

gallery = export_standard_postestimation_gallery(
    result,
    output_dir="outputs/standard_gallery",
    prefix="model",
)
```

Using the result accessor:

```python
result.plot.standard_gallery(
    "outputs/standard_gallery",
    prefix="model",
)
```

The standard gallery is the R/Stata-style plot collection. It is useful for detailed diagnostic review and publication appendix workflows.

---

# SGM-Viz v2 Diagnostic Dashboards

SGM-Viz is the package's higher-level diagnostic visualization system.

It combines:

* econometric diagnostic discipline;
* publication-quality layout;
* dashboard-style readability;
* dynamic-panel-specific interpretation.

## Model health dashboard

```python
result.plot.health(
    save="outputs/model_health.png",
)
```

This figure summarizes:

* Hansen diagnostic;
* Sargan diagnostic;
* AR(1);
* AR(2);
* observations;
* groups;
* instruments;
* instrument/group ratio;
* collapse status.

## Dynamic persistence dashboard

```python
result.plot.persistence(
    phi=result.params["L1.y"],
    save="outputs/persistence.png",
)
```

This figure reports:

* persistence coefficient;
* shock decay path;
* half-life;
* long-run multiplier;
* persistence class.

## Instrument architecture dashboard

```python
from systemgmmkit.postestimation import InstrumentArchitecture

architecture = InstrumentArchitecture(
    estimator="System GMM",
    difference_equation=("L2.y", "L3.y"),
    level_equation=("D.y",),
    standard_instruments=("x", "w", "time effects"),
    lag_range=(2, 3),
    collapsed=True,
    transformation="FOD",
    total_instruments=result.instruments,
    groups=result.groups,
)

result.plot.instruments(
    architecture=architecture,
    save="outputs/instruments.png",
)
```

This figure communicates:

* difference-equation instruments;
* level-equation instruments;
* standard instruments;
* lag range;
* collapse status;
* total instrument count;
* instrument/group ratio.

## Publication panel

```python
result.plot.publication_panel(
    architecture=architecture,
    phi=result.params["L1.y"],
    save="outputs/publication_panel.png",
)
```

The publication panel combines:

* model health;
* dynamic persistence;
* instrument architecture;
* parameter impact.

---

# One-Command SGM-Viz Report

```python
result.plot.export_all(
    "outputs/sgm_report",
    prefix="model",
    architecture=architecture,
    gallery_mode="dashboard",
)
```

Report modes:

```text
dashboard    = individual dashboards only
publication  = composed publication panel only
full         = all figures
```

Recommended use:

```python
result.plot.export_all(
    "outputs/sgm_report",
    gallery_mode="dashboard",
)
```

For a one-page paper figure:

```python
result.plot.export_all(
    "outputs/paper_report",
    gallery_mode="publication",
)
```

---

# Model Comparison Dashboard

```python
from systemgmmkit.postestimation import model_comparison_dashboard_v2

model_comparison_dashboard_v2(
    [baseline_result, robustness_result],
    labels=["Baseline", "Robustness"],
    save="outputs/model_comparison.png",
)
```

This is designed for screening alternative GMM specifications by:

* Hansen p-value;
* Sargan p-value;
* AR(2) p-value;
* instrument/group ratio.

---

# Reporting and Export

Results can be exported to:

* Markdown;
* CSV;
* LaTeX;
* PNG;
* SVG;
* PDF-compatible figures;
* HTML galleries.

`systemgmmkit` is designed to integrate with:

* `universal-output-hub`;
* publication pipelines;
* reproducible research workflows;
* model-comparison tables;
* diagnostic figure workflows.

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

## Control instrument proliferation

Instrument proliferation is one of the most common problems in applied dynamic GMM.

Recommended practice:

* use `collapse=True`;
* restrict `gmm_lags`;
* report instrument count;
* compare instrument count with number of groups;
* check whether Hansen p-values are suspiciously high;
* run robustness checks with alternative lag windows;
* inspect the SGM-Viz instrument architecture dashboard.

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
* package version;
* model-health dashboard or equivalent diagnostics.

---

# Roadmap

The next technical extension should focus on variable-level and role-level GMM instrument design.

Planned features:

* role-specific GMM lag windows;
* variable-specific GMM lag windows;
* explicit precedence rule:

```text
gmm_lags_by_variable > gmm_lags_by_role > gmm_lags
```

* tests confirming exogenous variables remain IV-style unless explicitly handled otherwise;
* Difference GMM and System GMM parity checks using separate `gmm()` blocks;
* instrument-count and instrument-name validation;
* documentation examples;
* Stata comparison scripts.

These features should not be documented as current functionality until implemented and validated.

---

# Citation

If you use `systemgmmkit` in academic work, please cite:

```text
Akanbi, Oluwajuwon Mayomi.

systemgmmkit:
Panel Data Econometrics and Dynamic GMM Workflows in Python.

Version 0.5.10.

https://github.com/Akanom/systemgmmkit
```

BibTeX:

```bibtex
@software{akanbi_systemgmmkit,
  author = {Akanbi, Oluwajuwon Mayomi},
  title = {systemgmmkit: Panel Data Econometrics and Dynamic GMM Workflows in Python},
  year = {2026},
  url = {https://github.com/Akanom/systemgmmkit},
  version = {0.5.10}
}
```

Replace or supplement this citation with DOI information once a Zenodo archive or software paper is available.

---

# License

MIT License.

See `LICENSE` for details.
