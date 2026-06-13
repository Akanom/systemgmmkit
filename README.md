# systemgmmkit

[![PyPI version](https://img.shields.io/pypi/v/systemgmmkit.svg)](https://pypi.org/project/systemgmmkit/)
[![Python versions](https://img.shields.io/pypi/pyversions/systemgmmkit.svg)](https://pypi.org/project/systemgmmkit/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://github.com/Akanom/systemgmmkit/actions/workflows/ci.yml/badge.svg)](https://github.com/Akanom/systemgmmkit/actions/workflows/ci.yml)
[![Publish](https://github.com/Akanom/systemgmmkit/actions/workflows/publish.yml/badge.svg)](https://github.com/Akanom/systemgmmkit/actions/workflows/publish.yml)
[![Downloads](https://img.shields.io/pepy/dm/systemgmmkit)](https://pepy.tech/project/systemgmmkit)
`systemgmmkit` is a Python workflow package for panel-data econometrics.

It supports reusable model specification, panel validation, static panel estimation, dynamic-panel GMM estimation, backend routing, diagnostics interpretation, reproducible reporting, and regression-table export.

The package is designed for applied panel-data projects in economics, finance, management, operations, productivity analysis, political economy, industrial organization, firm-level research, country panels, regional panels, household panels, and other longitudinal-data settings.

---

## Core idea

The core idea is simple:

> Define the panel model once. Validate the panel structure. Run the estimator through `systemgmmkit`. Export the results consistently.

For dynamic-panel GMM, users should call the public `systemgmmkit` API:

```python
from systemgmmkit import run_system_gmm, run_difference_gmm
```

The package then routes estimation through the appropriate backend.

---

## Core capabilities

`systemgmmkit` currently supports:

* validation of balanced and unbalanced panel datasets before estimation;
* pooled OLS-style panel models;
* one-way fixed effects;
* two-way fixed effects;
* one-way random effects;
* panel IV / 2SLS with optional fixed effects;
* Arellano-Bond Difference GMM;
* Blundell-Bond System GMM;
* collapsed instruments;
* restricted lag windows;
* one-step and two-step configurations where supported by the backend;
* public dynamic-GMM backend routing through `run_dynamic_panel_gmm()`;
* public `run_system_gmm()` and `run_difference_gmm()` convenience functions;
* optional validated backend adapter integration for System GMM;
* native Difference GMM estimation;
* native System GMM estimation with verified `xtabond2` parity across baseline, no-controls, three-way interaction, and decomposition benchmark specifications, including Windmeijer-corrected two-step standard-error parity and signed AR(1)/AR(2) diagnostic parity;
* model-card style reporting for reproducibility;
* regression-table export to Markdown, CSV, and LaTeX;
* Stata parity-check scaffolding for `xtreg, fe` and `xtabond2` replication workflows.

---

## Current validation status

| Estimator                       | Current status                                      | Interpretation |
| ------------------------------- | --------------------------------------------------- | -------------- |
| Static panel estimators         | Active development                                  | Pooled OLS, Fixed Effects, Random Effects, and Panel IV / 2SLS are available for applied workflow use and should be validated against reference packages for critical work. |
| Native Difference GMM           | Strict parity passed on current benchmark           | Native Difference GMM matches the current validation backend and Stata oracle within numerical tolerance on the tested benchmark. |
| Native System GMM               | `xtabond2` baseline strict parity and multi-spec AR parity passed | Native System GMM matches `xtabond2` on the maintained collapsed two-step System GMM benchmark for sample size, instrument count, coefficients, raw residual moments (`Z'u`), group-scaled two-step weighting matrix (`A2 / n_groups`), Hansen J, Windmeijer-corrected two-step standard errors, and signed AR(1)/AR(2) diagnostics with p-values. |
| System GMM via `backend="auto"` | Stable public workflow route                        | `backend="auto"` remains the recommended public workflow route unless the user needs explicit native/adapter comparison. Users who need exact replication should report the selected backend and validation benchmark. |

The current validation harness confirms strict parity for native Difference GMM on the benchmark specification.

Native System GMM now passes a dedicated `xtabond2` baseline parity benchmark. The verified benchmark covers coefficient estimates, observation counts, instrument counts, raw residual moments (`Z'u`), the group-scaled two-step weighting matrix (`A2 / n_groups`), the Hansen J statistic, Windmeijer-corrected two-step standard errors, and signed Arellano-Bond AR(1)/AR(2) diagnostics with p-values.

This should be interpreted as a strong benchmark-specific parity result, not as a universal claim of Stata identity across every possible dataset, lag window, missing-data pattern, instrument classification, covariance assumption, or finite-sample correction. Broader validation remains ongoing for additional unbalanced panels, missing-data structures, alternative lag windows, alternative instrument classifications, and wider empirical designs.

---

## Dynamic GMM backend policy

`systemgmmkit` is the user-facing package for dynamic-panel GMM workflows.

Users should call the public API:

```python
from systemgmmkit import run_system_gmm, run_difference_gmm
```

The package then routes estimation through the selected backend.

| User option           | Difference GMM behavior                                       | System GMM behavior |
| --------------------- | ------------------------------------------------------------- | ------------------- |
| `backend="auto"`      | Uses the validated native `systemgmmkit` Difference GMM path. | Uses the package's configured stable System GMM route. This is the recommended default workflow unless the user needs a specific backend. |
| `backend="validated"` | Uses the validated native `systemgmmkit` Difference GMM path. | Routes through the validated backend adapter where available. |
| `backend="native"`    | Uses the native `systemgmmkit` engine.                        | Uses the native `systemgmmkit` engine. The current `xtabond2` parity benchmark is passed for collapsed two-step System GMM sample size, instrument count, coefficients, moments, group-scaled A2, Hansen J, Windmeijer-corrected two-step standard errors, and signed AR(1)/AR(2) diagnostics with p-values. |
| `backend="pydynpd"`   | Explicitly routes through the backend adapter.                | Explicitly routes through the backend adapter. |

This design keeps `systemgmmkit` as the stable public interface while allowing explicit backend selection for replication, benchmarking, and sensitivity analysis.

For empirical System GMM work, a typical public workflow is:

```python
result = run_system_gmm(
    spec,
    data,
    entity="id",
    time="time",
    backend="auto",
)
```

For strict native replication of the current `xtabond2` parity benchmark, use `backend="native"` and match the sample, lag windows, collapsed-instrument setting, IV treatment, time-dummy treatment, transformation, covariance assumptions, and estimation options.

---

## System GMM construction update

The native System GMM implementation now uses row-level metadata during matrix construction.

Each constructed row carries:

* entity identifier;
* time identifier;
* equation type: differenced equation or level equation;
* original row index;
* underlying error-term composition.

This allows System GMM weighting to be constructed by entity and equation metadata rather than by assuming a balanced panel layout.

The construction logic has been validated across:

* balanced panels;
* unbalanced panels;
* panels with missing internal periods;
* shorter panels;
* specifications with and without time dummies;
* specifications with and without standard IV controls;
* single and multiple GMM-style instrument blocks.

This construction architecture now supports the current native System GMM `xtabond2` baseline parity result. It should still be interpreted conservatively: the benchmark verifies a specific collapsed two-step System GMM specification, not universal equivalence across all possible panel designs and covariance corrections.

---

## Stata-alignment policy

`systemgmmkit` should be treated as Stata-aligned, not automatically Stata-identical.

Results can align with Stata `xtreg, fe` and `xtabond2` only when the same sample, panel structure, transformation, lag windows, instrument matrix, collapsed-instrument setting, time dummies, covariance assumptions, finite-sample corrections, and estimation options are used.

Passing Python-backend parity should not be presented as universal Stata equivalence.

Exact Stata parity requires dedicated replication tests against `xtabond2`.

---

## Installation

Install from PyPI:

```bash
python -m pip install systemgmmkit
```

Install with optional backend and reporting extras:

```bash
python -m pip install "systemgmmkit[all]"
```

Development installation from a local clone:

```bash
python -m pip install -e ".[dev,all]"
```

Core local installation without optional extras:

```bash
python -m pip install -e .
```

Windows PowerShell development setup:

```powershell
cd "<REPO_ROOT>"

py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip setuptools wheel
python -m pip install -e ".[dev,all]"
python -m pytest -q
```

---

## Quick start: Fixed Effects

```python
from systemgmmkit import build_fixed_effects_spec, run_fixed_effects

spec = build_fixed_effects_spec(
    dependent="y",
    regressors=["x1", "x2"],
    controls=["control1", "control2"],
    entity_effects=True,
    time_effects=True,
    covariance="clustered",
    cluster="entity",
    name="two_way_fe",
)

result = run_fixed_effects(
    spec,
    df,
    entity="entity_id",
    time="year",
)

print(result.to_markdown())
```

---

## Quick start: Random Effects

```python
from systemgmmkit import RandomEffectsSpec, run_random_effects

spec = RandomEffectsSpec(
    dependent="y",
    regressors=["x1", "x2"],
    covariance="robust",
)

result = run_random_effects(
    spec,
    df,
    entity="entity_id",
    time="year",
)

print(result.to_markdown())
```

---

## Quick start: Panel IV / 2SLS

```python
from systemgmmkit import PanelIVSpec, run_panel_2sls

spec = PanelIVSpec(
    dependent="y",
    exog=["control1", "control2"],
    endogenous=["x1"],
    instruments=["z1", "z2"],
    entity_effects=True,
    time_effects=True,
    covariance="robust",
)

result = run_panel_2sls(
    spec,
    df,
    entity="entity_id",
    time="year",
)

print(result.to_markdown())
```

---

## Quick start: Difference GMM

```python
from systemgmmkit import build_difference_gmm_spec, run_difference_gmm

spec = build_difference_gmm_spec(
    dependent="y",
    regressors=["x1", "x2"],
    endogenous=["x1"],
    predetermined=["x2"],
    exogenous=[],
    lag_limits={
        "y": (2, 3),
        "x1": (2, 2),
        "x2": (2, 2),
    },
    collapse=True,
    steps="twostep",
    name="generic_difference_gmm",
)

result = run_difference_gmm(
    spec,
    df,
    entity="entity_id",
    time="year",
    backend="auto",
)
```

Difference GMM follows the Arellano-Bond dynamic-panel structure and uses lagged levels as instruments for transformed equations.

---

## Quick start: System GMM

```python
from systemgmmkit import build_system_gmm_spec, run_system_gmm

spec = build_system_gmm_spec(
    dependent="y",
    regressors=["x1", "x2", "control1", "control2"],
    endogenous=["x1"],
    predetermined=["x2"],
    exogenous=["control1", "control2"],
    lag_limits={
        "y": (2, 3),
        "x1": (2, 2),
        "x2": (2, 2),
    },
    collapse=True,
    time_dummies=True,
    steps="twostep",
    name="generic_system_gmm",
)

result = run_system_gmm(
    spec,
    df,
    entity="entity_id",
    time="year",
    backend="auto",
)
```

System GMM follows the Blundell-Bond dynamic-panel structure and combines transformed-equation moments with level-equation moments.

Native System GMM now passes a dedicated `xtabond2` benchmark for collapsed two-step System GMM sample size, instrument count, coefficients, residual moments, group-scaled two-step weighting matrix, Hansen J, Windmeijer-corrected two-step standard errors, and signed AR(1)/AR(2) diagnostics with p-values. Broader specification coverage remains under validation, so users should report the backend, model specification, instrument count, covariance type, AR diagnostics, and validation context for critical empirical work.

---

## Variable classification and lag-window control

Dynamic-panel GMM models require explicit assumptions about each regressor’s relationship to the error term.

`systemgmmkit` separates variables into three econometric groups:

* `endogenous`: variables that may be correlated with current and past shocks;
* `predetermined`: variables that may be affected by past shocks but are assumed not to be correlated with current shocks;
* `exogenous`: variables treated as standard IV-style instruments.

Variable-specific GMM lag windows are controlled through `lag_limits`.

This design allows users to specify different lag structures for the lagged dependent variable, endogenous regressors, predetermined regressors, and interaction terms.

---

## Example: variable-specific lag windows

```python
from systemgmmkit import build_system_gmm_spec

spec = build_system_gmm_spec(
    dependent="growth_rate",
    regressors=[
        "lPA",
        "s_techshare",
        "frag_index_orth",
        "polity2",
        "econ_dev_index",
        "human_dev_index",
        "lpop",
    ],
    endogenous=[
        "lPA",
        "s_techshare",
    ],
    predetermined=[
        "frag_index_orth",
        "polity2",
    ],
    exogenous=[
        "econ_dev_index",
        "human_dev_index",
        "lpop",
    ],
    lag_limits={
        "growth_rate": (2, 3),
        "lPA": (2, 2),
        "s_techshare": (2, 2),
        "frag_index_orth": (2, 3),
        "polity2": (1, 2),
    },
    collapse=True,
    time_dummies=True,
    steps="twostep",
    name="custom_lag_system_gmm",
)
```

In this example:

* `growth_rate` uses lags 2 to 3 as GMM-style instruments for the lagged dependent variable;
* `lPA` uses lag 2 only;
* `s_techshare` uses lag 2 only;
* `frag_index_orth` uses lags 2 to 3;
* `polity2` uses lags 1 to 2;
* `econ_dev_index`, `human_dev_index`, and `lpop` are treated as standard exogenous IV-style instruments.

---

## Endogenous variables

Use `endogenous` for regressors that may be correlated with current and past shocks.

```python
spec = build_system_gmm_spec(
    dependent="y",
    regressors=["x1", "x2", "control1"],
    endogenous=["x1"],
    predetermined=["x2"],
    exogenous=["control1"],
    lag_limits={
        "y": (2, 3),
        "x1": (2, 4),
        "x2": (1, 3),
    },
    collapse=True,
    steps="twostep",
)
```

Here:

* `x1` is treated as endogenous and instrumented using lags 2 to 4;
* `x2` is treated as predetermined and instrumented using lags 1 to 3;
* `control1` is treated as exogenous and enters as an IV-style instrument.

---

## Predetermined variables

Use `predetermined` for variables that may respond to past shocks but are assumed not to be correlated with the current-period error term.

```python
spec = build_system_gmm_spec(
    dependent="investment",
    regressors=["lagged_sales", "cash_flow", "firm_size"],
    endogenous=["cash_flow"],
    predetermined=["lagged_sales"],
    exogenous=["firm_size"],
    lag_limits={
        "investment": (2, 3),
        "cash_flow": (2, 2),
        "lagged_sales": (1, 2),
    },
    collapse=True,
    steps="twostep",
)
```

This allows `cash_flow` and `lagged_sales` to have different instrument lag windows.

---

## Exogenous variables

Use `exogenous` for variables treated as standard IV-style instruments.

Strictly exogenous controls do not usually need GMM lag windows. If a variable is placed in `exogenous`, it is treated as an IV-style instrument rather than as a GMM-style lagged instrument.

```python
spec = build_system_gmm_spec(
    dependent="growth",
    regressors=["lagged_growth", "aid", "trade_openness", "population"],
    endogenous=["aid"],
    predetermined=[],
    exogenous=["trade_openness", "population"],
    lag_limits={
        "growth": (2, 3),
        "aid": (2, 2),
    },
    collapse=True,
    steps="twostep",
)
```

Here, `trade_openness` and `population` enter as standard exogenous IV-style instruments.

---

## Lagged exogenous regressors

If a user wants a lagged exogenous regressor, the lagged column should be created before estimation.

```python
df["L1_trade"] = df.groupby("country")["trade"].shift(1)
df["L2_inflation"] = df.groupby("country")["inflation"].shift(2)

spec = build_system_gmm_spec(
    dependent="growth_rate",
    regressors=["lPA", "L1_trade", "L2_inflation"],
    endogenous=["lPA"],
    predetermined=[],
    exogenous=["L1_trade", "L2_inflation"],
    lag_limits={
        "growth_rate": (2, 3),
        "lPA": (2, 2),
    },
    collapse=True,
    steps="twostep",
)
```

This is the preferred approach when the lagged value itself is part of the regression equation.

---

## Exogenous variables with GMM-style lag instruments

If a variable should be instrumented using its own lagged values, it should not be treated as plain exogenous.

Instead, classify it as `predetermined` or `endogenous`, depending on the econometric assumption, and assign a lag window in `lag_limits`.

```python
spec = build_system_gmm_spec(
    dependent="growth_rate",
    regressors=["lPA", "trade", "inflation", "education"],
    endogenous=["lPA"],
    predetermined=["trade", "inflation"],
    exogenous=["education"],
    lag_limits={
        "growth_rate": (2, 3),
        "lPA": (2, 2),
        "trade": (1, 2),
        "inflation": (2, 4),
    },
    collapse=True,
    steps="twostep",
)
```

This produces variable-specific lag windows while keeping the variable classification explicit.

---

## Interaction terms

Interaction terms should be classified according to the econometric assumption applied to the interaction.

If the interaction contains variables that may be endogenous or predetermined, the interaction should usually be treated conservatively as predetermined or endogenous.

```python
spec = build_system_gmm_spec(
    dependent="growth_rate",
    regressors=[
        "lPA",
        "s_techshare",
        "frag_index_orth",
        "polity2",
        "s_tech_frag",
        "s_tech_polity",
        "s_frag_polity",
        "s_tech_frag_polity",
        "econ_dev_index",
        "human_dev_index",
        "lpop",
    ],
    endogenous=["lPA", "s_techshare"],
    predetermined=[
        "frag_index_orth",
        "polity2",
        "s_tech_frag",
        "s_tech_polity",
        "s_frag_polity",
        "s_tech_frag_polity",
    ],
    exogenous=["econ_dev_index", "human_dev_index", "lpop"],
    lag_limits={
        "growth_rate": (2, 3),
        "lPA": (2, 2),
        "s_techshare": (2, 2),
        "frag_index_orth": (2, 2),
        "polity2": (2, 2),
        "s_tech_frag": (2, 2),
        "s_tech_polity": (2, 2),
        "s_frag_polity": (2, 2),
        "s_tech_frag_polity": (2, 2),
    },
    collapse=True,
    time_dummies=True,
    steps="twostep",
    name="interaction_system_gmm",
)
```

This structure is useful for applied panel-data designs with institutional moderators, fragmentation measures, policy interactions, or other theoretically motivated interaction terms.

---

## Practical guidance

Users should choose variable classifications and lag windows based on the research design, not mechanically.

Recommended practice:

* use restricted lag windows to reduce instrument proliferation;
* use collapsed instruments in most applied System GMM workflows;
* avoid treating too many variables as endogenous unless theoretically justified;
* document why each variable is treated as endogenous, predetermined, or exogenous;
* compare instrument counts against the number of groups;
* check Hansen/Sargan and AR diagnostics where available;
* validate important specifications against a reference backend or external software where possible.

---

## Summary table

| User intention                                          | Recommended approach                                                                                                 |
| ------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| Endogenous regressor with GMM lags                      | Put variable in `endogenous` and set `lag_limits[var]`.                                                              |
| Predetermined regressor with GMM lags                   | Put variable in `predetermined` and set `lag_limits[var]`.                                                           |
| Strictly exogenous control                              | Put variable in `exogenous`; no GMM lag window required.                                                             |
| Lagged exogenous regressor                              | Create `L1_` / `L2_` columns before estimation and include them in `exogenous`.                                      |
| Exogenous variable to be instrumented by its own lags   | Reclassify as `predetermined` or `endogenous` and set `lag_limits[var]`.                                             |
| Interaction term with potentially endogenous components | Treat conservatively as `predetermined` or `endogenous`.                                                             |
| Short panel with many instruments                       | Use `collapse=True` and narrow lag windows.                                                                          |
| Stata / backend replication                             | Match sample, lag windows, transformation, collapse setting, IV treatment, time dummies, and covariance assumptions. |

---

## Important caution

Variable classification is an econometric assumption.

`systemgmmkit` can construct the requested model, but it cannot determine whether a variable is truly endogenous, predetermined, or exogenous. That decision must be justified by theory, institutional knowledge, timing assumptions, and robustness checks.

---

## Native dynamic-panel GMM backend

`systemgmmkit` includes a native dynamic-panel GMM backend for Difference GMM and System GMM.

Supported native GMM features include:

* Difference GMM;
* System GMM with verified `xtabond2` baseline parity for the current collapsed two-step benchmark, including Windmeijer-corrected two-step standard-error parity and signed AR(1)/AR(2) diagnostic parity;
* collapsed instruments;
* restricted lag windows;
* one-step and two-step estimation paths;
* backend-compatible instrument ordering where supported;
* effective observation count reporting;
* instrument-count reporting;
* structured result objects.

The native backend is intended to provide a transparent Python implementation that can be inspected, tested, and extended without relying only on an external backend.

The native System GMM parity benchmark currently verifies:

* coefficient estimates against `xtabond2`;
* raw residual moments (`Z'u`) after instrument-order mapping;
* two-step weighting matrix alignment after group scaling (`A2 / n_groups`);
* Hansen J statistic alignment;
* Windmeijer-corrected two-step standard-error alignment against Stata `e(V)`;
* signed AR(1)/AR(2) diagnostic alignment against `xtabond2`;
* automated parity-report generation for the benchmark.

The remaining high-priority validation work is broader benchmark coverage across unbalanced panels, missing-data structures, alternative lag windows, alternative instrument classifications, and additional empirical designs.

---

## Backend adapter

The backend adapter returns a structured result object.

The adapter:

* builds backend-compatible command strings;
* groups IV-style instruments into a single `iv(...)` command block;
* captures printed backend output;
* extracts coefficients, standard errors, p-values, observation counts, instrument counts, and common GMM diagnostics where available;
* applies narrow compatibility shims for older backend / NumPy combinations;
* serves as the Python reference backend for native GMM parity validation.

The compatibility shims are intentionally narrow. They are not intended to alter the econometric meaning of backend results; they only handle backend compatibility issues such as scalar extraction behavior under newer NumPy versions.

---

## Regression-table export

```python
from systemgmmkit import export_regression_table

export_regression_table(
    [fe_result, re_result, iv_result],
    "results.md",
    fmt="markdown",
)

export_regression_table(
    [fe_result, re_result, iv_result],
    "results.csv",
    fmt="csv",
)

export_regression_table(
    [fe_result, re_result, iv_result],
    "results.tex",
    fmt="latex",
)
```

---

## Reproducibility and reporting

For dynamic-panel GMM, users should record at minimum:

* dependent variable;
* regressors;
* endogenous variables;
* predetermined variables;
* exogenous variables;
* lag windows;
* transformation;
* collapsed-instrument setting;
* time-dummy treatment;
* one-step or two-step configuration;
* covariance assumptions;
* backend used;
* software versions.

---

## Validation roadmap

Before claiming broader production certification across panel designs, the package should continue to be tested on:

* balanced panels;
* unbalanced panels;
* short-`T` panels;
* longer-`T` panels;
* high-`N`, low-`T` panels;
* panels with missing observations;
* different lag windows;
* models with no controls;
* models with many controls;
* interaction-heavy specifications;
* decomposition specifications;
* alternative instrument classifications;
* Stata `xtabond2` replication benchmarks.

High-priority remaining validation items:

* broader System GMM parity across additional empirical specifications;
* broader Windmeijer-corrected standard-error parity across additional empirical specifications;
* broader robustness of Sargan, Hansen, and AR diagnostics across additional panel structures;
* documentation of exact Stata-compatible options and known non-equivalence cases.

This roadmap protects the package from overclaiming and supports academically defensible validation.

---

## Native System GMM parity status

Native System GMM has certified benchmark-specific parity against Stata `xtabond2` for the committed baseline, no-controls, three-way interaction, and decomposition specifications.

Certified quantities include coefficient estimates, parameter counts, observation counts, instrument counts, Hansen p-values, two-step Windmeijer-corrected standard errors, and signed AR(1)/AR(2) diagnostics with p-values.

The committed baseline specification is certified as `PASS_STRICT_XTABOND2_SYSTEM_GMM_BASELINE`. The no-controls, three-way interaction, and decomposition specifications pass the AR diagnostic parity check under the committed validation thresholds.

See `artifacts/parity/xtabond2/xtabond2_native_system_gmm_parity.md`, `artifacts/parity/xtabond2/ar_diagnostics_comparison.md`, and `artifacts/parity/xtabond2/native_xtabond2_ar_diagnostics_validation.csv` for the certification evidence and reproduction context.

---

## Development principles

`systemgmmkit` is built around the following principles:

* generic design, not domain-specific hard-coding;
* transparent econometric specification;
* explicit backend behavior;
* reproducible reporting;
* strict parity testing where feasible;
* conservative claims about external-software equivalence;
* clear distinction between Python-backend parity and Stata parity;
* practical usability for applied empirical researchers.

---

## License

This project is licensed under the terms specified in the [LICENSE](LICENSE) file.

---

## Citation

If you use `systemgmmkit` in academic or applied research, cite the package version or Git commit, backend used, and model specification details.

Recommended reporting format:

```text
Estimation was performed using systemgmmkit version X.Y.Z, commit <commit-hash>. Dynamic-panel GMM results used the [native / validated backend] route with collapsed instruments, restricted lag windows, and [one-step / two-step] estimation. Specification details, panel structure, and instrument classification are reported in the model documentation.
```

