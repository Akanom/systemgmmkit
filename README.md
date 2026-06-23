# systemgmmkit

[![PyPI version](https://img.shields.io/pypi/v/systemgmmkit.svg)](https://pypi.org/project/systemgmmkit/)
[![Python versions](https://img.shields.io/pypi/pyversions/systemgmmkit.svg)](https://pypi.org/project/systemgmmkit/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://github.com/Akanom/systemgmmkit/actions/workflows/ci.yml/badge.svg)](https://github.com/Akanom/systemgmmkit/actions/workflows/ci.yml)
[![Publish](https://github.com/Akanom/systemgmmkit/actions/workflows/publish.yml/badge.svg)](https://github.com/Akanom/systemgmmkit/actions/workflows/publish.yml)

---

# systemgmmkit 0.5.11

`systemgmmkit` is a Python package for applied panel-data econometrics and dynamic-panel GMM workflows.

It provides a unified workflow for:

* baseline linear models;
* panel estimators;
* instrumental-variable models;
* Difference GMM and System GMM;
* easy dynamic-GMM wrapper APIs;
* dynamic-panel diagnostics;
* post-estimation analysis;
* visualization and diagnostic dashboards;
* ML-style workflow utilities around fitted econometric models;
* reproducible reporting and export.

The package is designed for empirical researchers working in economics, finance, management, operations, productivity analysis, public policy, development economics, political economy, industrial organization, and other panel-data settings.

---

# Why systemgmmkit?

Applied panel-data work often requires several disconnected tools:

* OLS and pooled OLS;
* fixed-effects and random-effects estimators;
* panel IV / 2SLS;
* Difference GMM and System GMM;
* overidentification and serial-correlation diagnostics;
* post-estimation analysis;
* coefficient tables;
* diagnostic plots;
* model comparison;
* forecasting and backtesting;
* reproducible outputs.

`systemgmmkit` aims to bring these pieces into a consistent Python workflow.

The package is built around five principles:

1. **Explicit model specification**

   Model assumptions should be visible in the code, not hidden inside estimation defaults.

2. **Reproducible empirical workflows**

   Estimation, diagnostics, post-estimation, visualization, validation, forecasting, and reporting should be easy to rerun and inspect.

3. **Transparent dynamic-panel diagnostics**

   Dynamic-panel GMM results should expose sample size, group count, instrument count, AR tests, Hansen/Sargan tests, covariance type, backend metadata, and instrument architecture.

4. **Verification against reference implementations**

   Estimators are benchmarked against established Stata implementations where practical.

5. **Publication-oriented communication**

   Results should be interpretable not only as coefficient tables, but also through diagnostics, model-health dashboards, persistence plots, instrument-architecture displays, prediction outputs, validation tables, forecast outputs, and report-ready graphics.

The objective is not only to estimate models. The objective is to make modelling choices clear enough for replication, review, publication, and applied decision-making.

---

# What's New in 0.5.11

Version `0.5.11` is an **ML-style workflow and usability release**.

It builds on the `0.5.10` visualization and diagnostic-reporting layer by adding:

* an additive workflow namespace, `systemgmmkit.ml`, for prediction, validation, model comparison, forecasting, forecast backtesting, and GMM specification-search scaffolding around already fitted econometric result objects;
* easier user-facing wrappers for Difference GMM and System GMM through `difference_gmm()` and `system_gmm()`.

This release does **not** rewrite the validated estimator internals and does **not** introduce new dynamic-panel estimator theory.

---

## New ML-style workflow namespace

```python
from systemgmmkit.ml import (
    ResultAdapter,
    adapt_result,
    predict,
    fitted_values,
    residuals,
    regression_metrics,
    panel_train_test_split,
    PanelTimeSeriesSplit,
    cross_validate_panel,
    compare_models,
    forecast,
    backtest_forecast,
    GMMGridSearch,
    GMMSearchResult,
)
```

The intended design is:

```text
validated econometric estimator
        ↓
result object
        ↓
ML-style workflow utilities
```

The ML workflow layer supports:

* prediction from fitted result objects;
* fitted-value extraction;
* residual extraction;
* regression metrics;
* time-respecting panel train/test splitting;
* expanding-window panel cross-validation;
* model comparison across fitted estimators;
* recursive forecasting from dynamic-panel results;
* forecast backtesting;
* GMM specification-search scaffolding.

The purpose is not to turn `systemgmmkit` into a generic machine-learning library. The purpose is to make validated econometric models usable in modern prediction, validation, forecasting, comparison, and reporting workflows.

---

## New easy dynamic-GMM wrapper API

Version `0.5.11` adds easier user-facing wrappers:

```python
from systemgmmkit import difference_gmm, system_gmm
```

These wrappers sit on top of the validated lower-level GMM builders and runners.

The intended workflow is:

```text
easy wrapper
    ↓
validated spec builder
    ↓
validated GMM runner
    ↓
result object
```

The easy API is designed for users who want a readable one-call workflow while still preserving explicit modelling choices.

The lower-level APIs remain available for advanced users, validation workflows, and parity checks:

```python
from systemgmmkit import (
    build_difference_gmm_spec,
    run_difference_gmm,
    build_system_gmm_spec,
    run_system_gmm,
)
```

The easy API is a convenience layer. It is not a new estimator.

---

# Current Feature Coverage

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
* Easy Difference GMM wrapper through `difference_gmm()`
* Easy System GMM wrapper through `system_gmm()`
* One-step estimation
* Two-step estimation
* Windmeijer-corrected standard errors
* Collapsed instruments
* Restricted global GMM lag windows
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

## ML-Style Workflow

* Prediction from fitted result objects
* Fitted-value and residual extraction
* Regression metrics
* Panel-aware train/test splitting
* Expanding-window panel cross-validation
* Model comparison
* Recursive forecasting
* Forecast backtesting
* GMM specification-search scaffolding

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

# Dynamic Panel GMM

`systemgmmkit` supports both Difference GMM and System GMM.

The recommended workflow is:

1. Define the structural model.
2. Create any lagged variables that should enter the model equation.
3. Classify regressors as endogenous, predetermined, or exogenous.
4. Define the GMM instrument strategy.
5. Run the estimator.
6. Inspect diagnostics before interpreting coefficients.
7. Export tables and diagnostic figures.

Users can run dynamic-panel GMM through either:

* the easy wrapper API: `difference_gmm()` and `system_gmm()`;
* the lower-level specification API: `build_difference_gmm_spec()`, `run_difference_gmm()`, `build_system_gmm_spec()`, and `run_system_gmm()`.

---

# Easy Dynamic GMM API

## Easy System GMM

```python
from systemgmmkit import system_gmm

result = system_gmm(
    data=df,
    entity="firm_id",
    time="year",
    dependent="y",
    lagged_dependent=1,
    regressors=[
        "investment",
        "cashflow",
        "firm_size",
    ],
    endogenous=[
        "investment",
    ],
    predetermined=[
        "cashflow",
    ],
    exogenous=[
        "firm_size",
    ],
    gmm_lags=(2, 2),
    collapse=True,
    windmeijer=True,
)
```

By default, `lagged_dependent=1` creates a structural lag column named `L1_y`, adds it to the model equation, and classifies it as endogenous.

If the lagged dependent variable should be treated differently, use:

```python
result = system_gmm(
    data=df,
    entity="firm_id",
    time="year",
    dependent="y",
    lagged_dependent=1,
    lagged_dependent_role="predetermined",
    regressors=["investment", "firm_size"],
    endogenous=["investment"],
    exogenous=["firm_size"],
    gmm_lags=(2, 2),
)
```

Allowed `lagged_dependent_role` values are:

* `"endogenous"`;
* `"predetermined"`;
* `"exogenous"`;
* `"none"`.

Unclassified regressors are treated as exogenous by default for usability, but researchers should classify variables explicitly in serious empirical work.

---

## Easy Difference GMM

```python
from systemgmmkit import difference_gmm

result = difference_gmm(
    data=df,
    entity="firm_id",
    time="year",
    dependent="y",
    lagged_dependent=1,
    regressors=[
        "investment",
        "cashflow",
        "firm_size",
    ],
    endogenous=[
        "investment",
    ],
    predetermined=[
        "cashflow",
    ],
    exogenous=[
        "firm_size",
    ],
    gmm_lags=(2, 2),
    collapse=True,
)
```

The easy Difference GMM wrapper follows the same structural-lag and variable-classification logic as the easy System GMM wrapper.

---

## Inspecting the generated workflow

For inspection, set `return_workflow=True`:

```python
from systemgmmkit import system_gmm

workflow = system_gmm(
    data=df,
    entity="firm_id",
    time="year",
    dependent="y",
    regressors=["investment", "firm_size"],
    endogenous=["investment"],
    exogenous=["firm_size"],
    gmm_lags=(2, 2),
    return_workflow=True,
)

result = workflow.result
spec = workflow.spec
model_data = workflow.data
```

The workflow object exposes:

* fitted result;
* generated specification;
* model dataframe after lag creation and missing-value handling;
* final regressors;
* endogenous variables;
* predetermined variables;
* exogenous variables;
* GMM lag window;
* collapse setting;
* model type.

---

# Advanced Dynamic GMM API

Advanced users can still use the lower-level API directly.

## Difference GMM

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

## System GMM

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

The lower-level API gives full control over the specification object and remains the reference API for validation and parity workflows.

---

# Variable Classification Guide

Correct variable classification is one of the most important modelling decisions in dynamic-panel estimation.

| Classification | Interpretation                                       | Typical instrument treatment                                                              | Examples                                                                     |
| -------------- | ---------------------------------------------------- | ----------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| Endogenous     | May be correlated with current and past disturbances | GMM-style instruments using deeper lags                                                   | investment, aid, leverage, R&D, production decisions                         |
| Predetermined  | May react to past shocks but not current shocks      | GMM-style instruments, often allowing shorter lag windows than fully endogenous variables | cash flow, backlog, lagged policy variables, delayed implementation measures |
| Exogenous      | Assumed independent of the disturbance process       | IV-style instruments by default                                                           | firm size, year dummies, industry dummies, externally determined controls    |

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

# Creating Structural Lags

The lower-level API treats lagged regressors as ordinary columns supplied by the user. It does not automatically create structural `L1_` or `L2_` model variables.

```python
df = df.sort_values(["firm_id", "year"]).copy()

df["L1_y"] = df.groupby("firm_id")["y"].shift(1)
df["L1_investment"] = df.groupby("firm_id")["investment"].shift(1)
df["L2_investment"] = df.groupby("firm_id")["investment"].shift(2)

df = df.dropna(
    subset=[
        "L1_y",
        "L1_investment",
        "L2_investment",
    ]
)
```

The easy API can create lagged dependent-variable columns automatically through:

```python
lagged_dependent=1
```

or:

```python
lagged_dependent=2
```

This convenience applies to the dependent variable only. Other structural lags should still be created explicitly by the user.

---

# GMM Lag-Window Strategy

The current public GMM lag-window control is the global GMM lag window:

```python
gmm_lags = (2, 4)
```

This means GMM-style instruments are constructed using lags 2 through 4 for GMM-style variables.

Example:

```python
from systemgmmkit import build_system_gmm_spec

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

Role-specific and variable-specific GMM lag-window designs are planned roadmap items. They should not be documented as current functionality until implemented, tested, and validated.

Planned precedence rule:

```text
gmm_lags_by_variable > gmm_lags_by_role > gmm_lags
```

---

# Exogenous Variables Remain IV-Style by Default

Exogenous variables are treated as IV-style instruments by default.

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
* restrict global GMM lag windows;
* report the number of instruments;
* report AR(1), AR(2), Hansen, and Sargan diagnostics;
* compare alternative lag-window choices as robustness checks.

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

# Post-Estimation Utilities

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

---

# SGM-Viz Diagnostic Dashboards

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

## One-command report export

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

---

# ML-Style Workflow Layer

`systemgmmkit.ml` adds machine-learning-style workflow utilities around already fitted econometric result objects.

This layer is intentionally additive:

```text
validated econometric estimator
        ↓
result object
        ↓
ML-style workflow utilities
```

It does **not** replace the econometric estimators and does **not** rewrite the validated estimation core.

## Public API

```python
from systemgmmkit.ml import (
    ResultAdapter,
    adapt_result,
    predict,
    fitted_values,
    residuals,
    regression_metrics,
    panel_train_test_split,
    PanelTimeSeriesSplit,
    cross_validate_panel,
    compare_models,
    forecast,
    backtest_forecast,
    GMMGridSearch,
    GMMSearchResult,
)
```

## Prediction and residuals

```python
from systemgmmkit.ml import predict, fitted_values, residuals

pred = predict(result, df)
fit = fitted_values(result, df)
err = residuals(result, df, y="growth_rate")
```

## Regression metrics

```python
from systemgmmkit.ml import regression_metrics

scores = regression_metrics(
    y_true=df["growth_rate"],
    y_pred=pred,
)
```

Metrics include:

* MAE;
* MSE;
* RMSE;
* MAPE;
* SMAPE;
* R²;
* evaluated observation count.

## Panel-aware train/test split

```python
from systemgmmkit.ml import panel_train_test_split

train, test = panel_train_test_split(
    df,
    time="year",
    test_size=0.2,
)
```

The split is time-respecting and does not randomly split panel rows.

## Panel-aware cross-validation

```python
from systemgmmkit.ml import PanelTimeSeriesSplit, cross_validate_panel

cv = PanelTimeSeriesSplit(
    n_splits=5,
    min_train_periods=10,
    test_periods=1,
)

scores = cross_validate_panel(
    estimator=my_estimator,
    data=df,
    y="growth_rate",
    time="year",
    cv=cv,
)
```

## Model comparison

```python
from systemgmmkit.ml import compare_models

comparison = compare_models(
    models={
        "OLS": ols_result,
        "Fixed Effects": fe_result,
        "System GMM": sysgmm_result,
    },
    data=test_df,
    y="growth_rate",
)
```

The comparison table reports prediction metrics such as MAE, MSE, RMSE, MAPE, SMAPE, and R². Where available, scalar diagnostics are also included with a `diag_` prefix.

## Recursive forecasting

```python
from systemgmmkit.ml import forecast

fc = forecast(
    result=sysgmm_result,
    history=df,
    y="growth_rate",
    entity="country",
    time="year",
    horizon=4,
    future_exog=future_controls,
)
```

For dynamic-panel models, lagged dependent-variable terms are detected from coefficient names such as:

* `L1.y`;
* `L2.y`;
* `L.y`;
* `y_lag1`;
* `lag1_y`;
* `L1_y`.

The function recursively updates lagged dependent variables using previous forecasts.

## Forecast backtesting

```python
from systemgmmkit.ml import backtest_forecast

scores = backtest_forecast(
    result_factory=my_estimator,
    data=df,
    y="growth_rate",
    entity="country",
    time="year",
    horizon=4,
    min_train_periods=10,
)
```

This supports expanding-window forecast validation for panel-data workflows.

## GMM specification-search scaffold

```python
from systemgmmkit.ml import GMMGridSearch

search = GMMGridSearch(
    build_spec=build_system_gmm_spec,
    run_model=run_system_gmm,
    param_grid=[
        {"gmm_lags": (2, 2), "collapse": True},
        {"gmm_lags": (2, 3), "collapse": True},
        {"gmm_lags": (2, 4), "collapse": True},
    ],
    y="growth_rate",
    entity="country",
    time="year",
    diagnostic_rules={
        "hansen_p": (">", 0.05),
        "ar2_p": (">", 0.05),
    },
)

search_result = search.fit(df)
```

The search layer repeatedly calls existing validated estimators. It does not implement a new GMM estimator.

## Smoke demonstration

A reviewer-facing smoke script is available:

```bash
python scripts/ml/run_ml_workflow_smoke.py --outdir artifacts/ml_workflow
```

The script writes reproducible workflow artifacts including:

* synthetic static and dynamic panel data;
* predictions and residuals;
* panel cross-validation scores;
* model comparison output;
* GMM grid-search output;
* recursive forecasts;
* forecast backtest metrics;
* a machine-readable summary file.

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
| SGM-Viz dashboards         | PASS_TESTED_EXPORT    |
| Standard graphics gallery  | PASS_TESTED_EXPORT    |
| Result plot accessors      | PASS_TESTED_EXPORT    |
| ML workflow smoke script   | PASS_TESTED_WORKFLOW  |
| Easy dynamic-GMM wrappers  | PASS_TESTED_API       |

Validation claims apply to the maintained benchmark specifications and validation workflows in the repository. The controlled `xtabond2` benchmark is used for strict certification. The CMAPSS FD001 application is used as an external validation case.

Users should still inspect their own model diagnostics, instrument counts, sample construction, lag-window choices, and identification assumptions.

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
* restricted global GMM lag windows;
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
Panel-Data Econometrics and Dynamic-Panel GMM Workflows in Python.

Version 0.5.11.

https://github.com/Akanom/systemgmmkit
```

BibTeX:

```bibtex
@software{akanbi_systemgmmkit,
  author = {Akanbi, Oluwajuwon Mayomi},
  title = {systemgmmkit: Panel-Data Econometrics and Dynamic-Panel GMM Workflows in Python},
  year = {2026},
  url = {https://github.com/Akanom/systemgmmkit},
  version = {0.5.11}
}
```

Replace or supplement this citation with DOI information once a Zenodo archive or software paper is available.

---

# License

MIT License.

See `LICENSE` for details.
