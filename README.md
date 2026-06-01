# systemgmmkit

`systemgmmkit` is a generic Python workflow package for panel-data econometrics.

It supports reusable model specification, panel validation, static panel estimation, dynamic-panel GMM estimation, diagnostics interpretation, reproducible model reporting, and regression-table export.

The package is designed for applied panel-data projects in economics, finance, management, operations, productivity analysis, political economy, industrial organization, firm-level research, country panels, regional panels, household panels, and other longitudinal-data settings.

---

## Core capabilities

`systemgmmkit` currently supports:

- Validation of balanced and unbalanced panel datasets before estimation.
- Static panel estimation using native Python backends:
  - pooled OLS-style models;
  - one-way fixed effects;
  - two-way fixed effects;
  - one-way Random Effects;
  - Panel IV / 2SLS with optional fixed effects.
- Dynamic-panel GMM model construction and estimation:
  - Arellano-Bond Difference GMM;
  - Blundell-Bond System GMM;
  - collapsed instruments;
  - restricted lag windows;
  - one-step and two-step configurations where supported by the backend.
- Native Difference GMM and native System GMM estimation.
- Optional `pydynpd` backend integration for dynamic-panel GMM.
- Strict coefficient-parity validation between the native GMM backend and `pydynpd` on the current validation harness.
- Model-card style reporting for reproducibility.
- Regression-table export to Markdown, CSV, and LaTeX.
- Stata parity-check do-file templates for `xtreg, fe` and `xtabond2` replication workflows.

---

## Current validation status

The native Difference GMM and native System GMM estimators pass strict coefficient parity against `pydynpd` on the current validation harness.

The current validation harness includes:

- Difference GMM baseline with controls;
- System GMM baseline with controls;
- System GMM three-way interaction model with controls;
- System GMM three-way interaction model without controls;
- System GMM decomposition model with controls.

For these tested specifications, the native backend matches `pydynpd` on:

- effective observation count;
- number of instruments;
- coefficient signs;
- strict coefficient parity;
- tested baseline, interaction, no-control, and decomposition structures.

This is a strong validation milestone for the native Python GMM implementation. However, it should not yet be interpreted as universal equivalence across all possible panel structures, transformations, lag windows, missing-data patterns, or external statistical packages.

---

## Stata-alignment policy

`systemgmmkit` should be treated as Stata-aligned, not automatically Stata-identical.

Results can align with Stata `xtreg, fe` and `xtabond2` only when the same sample, panel structure, transformation, lag windows, instrument matrix, collapsed-instrument setting, time dummies, covariance assumptions, finite-sample corrections, and estimation options are used.

The native Difference GMM and native System GMM estimators now pass strict coefficient parity against `pydynpd` on the current validation harness. This validates the native dynamic-panel GMM implementation against the package’s Python reference backend for the tested specifications.

Exact Stata parity still requires dedicated replication tests against `xtabond2`. Passing `pydynpd` parity should not be presented as universal Stata equivalence.

---

## Installation

Development installation:

```bash
python -m pip install -e ".[dev,all]"
```

Runtime installation:

```bash
python -m pip install -e ".[all]"
```

Core local installation without optional extras:

```bash
python -m pip install -e .
```

---

## Generic fixed-effects model

```python
from systemgmmkit import build_fixed_effects_spec, run_fixed_effects

spec = build_fixed_effects_spec(
    dependent="y",
    regressors=["x1", "x2"],
    controls=["control1", "control2"],
    interactions=["x1_x2"],
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

## Generic Random Effects

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

## Generic Panel IV / 2SLS

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

## Generic System GMM

```python
from systemgmmkit import build_pydynpd_command, build_system_gmm_spec

spec = build_system_gmm_spec(
    dependent="y",
    regressors=["x1", "x2"],
    controls=["control1", "control2"],
    interactions=["x1_x2"],
    endogenous=["x1"],
    predetermined=["x2"],
    exogenous=["control1", "control2", "x1_x2"],
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

print(build_pydynpd_command(spec))
```

System GMM follows the Blundell-Bond dynamic-panel structure and combines transformed-equation moments with level-equation moments.

---

## Variable classification and lag-window control

Dynamic-panel GMM models require explicit assumptions about each regressor’s relationship to the error term.

`systemgmmkit` separates variables into three main econometric groups:

- `endogenous`: variables that may be correlated with current and past shocks;
- `predetermined`: variables that may be affected by past shocks but are assumed not to be correlated with current shocks;
- `exogenous`: variables treated as standard IV-style instruments.

Variable-specific GMM lag windows are controlled through `lag_limits`.

This design allows users to specify different lag structures for the lagged dependent variable, endogenous regressors, predetermined regressors, and interaction terms.

---

### Basic example: variable-specific lag windows

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

- `growth_rate` uses lags 2 to 3 as GMM-style instruments for the lagged dependent variable;
- `lPA` uses lag 2 only;
- `s_techshare` uses lag 2 only;
- `frag_index_orth` uses lags 2 to 3;
- `polity2` uses lags 1 to 2;
- `econ_dev_index`, `human_dev_index`, and `lpop` are treated as standard exogenous IV-style instruments.

---

### Endogenous variables

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

- `x1` is treated as endogenous and instrumented using lags 2 to 4;
- `x2` is treated as predetermined and instrumented using lags 1 to 3;
- `control1` is treated as exogenous and enters as an IV-style instrument.

---

### Predetermined variables

Use `predetermined` for variables that may respond to past shocks but are assumed not to be correlated with the current-period error term.

```python
spec = build_system_gmm_spec(
    dependent="investment",
    regressors=[
        "lagged_sales",
        "cash_flow",
        "firm_size",
    ],
    endogenous=[
        "cash_flow",
    ],
    predetermined=[
        "lagged_sales",
    ],
    exogenous=[
        "firm_size",
    ],
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

### Exogenous variables

Use `exogenous` for variables treated as standard IV-style instruments.

Strictly exogenous controls do not usually need GMM lag windows. If a variable is placed in `exogenous`, it is treated as an IV-style instrument rather than as a GMM-style lagged instrument.

```python
spec = build_system_gmm_spec(
    dependent="growth",
    regressors=[
        "lagged_growth",
        "aid",
        "trade_openness",
        "population",
    ],
    endogenous=[
        "aid",
    ],
    predetermined=[],
    exogenous=[
        "trade_openness",
        "population",
    ],
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

### Lagged exogenous regressors

If a user wants a lagged exogenous regressor, the lagged column should be created before estimation.

```python
df["L1_trade"] = df.groupby("country")["trade"].shift(1)
df["L2_inflation"] = df.groupby("country")["inflation"].shift(2)

spec = build_system_gmm_spec(
    dependent="growth_rate",
    regressors=[
        "lPA",
        "L1_trade",
        "L2_inflation",
    ],
    endogenous=[
        "lPA",
    ],
    predetermined=[],
    exogenous=[
        "L1_trade",
        "L2_inflation",
    ],
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

### Exogenous variables with GMM-style lag instruments

If a variable should be instrumented using its own lagged values, it should not be treated as plain exogenous.

Instead, classify it as `predetermined` or `endogenous`, depending on the econometric assumption, and assign a lag window in `lag_limits`.

```python
spec = build_system_gmm_spec(
    dependent="growth_rate",
    regressors=[
        "lPA",
        "trade",
        "inflation",
        "education",
    ],
    endogenous=[
        "lPA",
    ],
    predetermined=[
        "trade",
        "inflation",
    ],
    exogenous=[
        "education",
    ],
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

### Interaction terms

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
    endogenous=[
        "lPA",
        "s_techshare",
    ],
    predetermined=[
        "frag_index_orth",
        "polity2",
        "s_tech_frag",
        "s_tech_polity",
        "s_frag_polity",
        "s_tech_frag_polity",
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

### Practical guidance

Users should choose variable classifications and lag windows based on the research design, not mechanically.

Recommended practice:

- use restricted lag windows to reduce instrument proliferation;
- use collapsed instruments in most applied System GMM workflows;
- avoid treating too many variables as endogenous unless theoretically justified;
- document why each variable is treated as endogenous, predetermined, or exogenous;
- compare instrument counts against the number of groups;
- check Hansen/Sargan and AR diagnostics where available;
- validate important specifications against a reference backend or external software where possible.

---

### Summary table

| User intention | Recommended approach |
|---|---|
| Endogenous regressor with GMM lags | Put variable in `endogenous` and set `lag_limits[var]` |
| Predetermined regressor with GMM lags | Put variable in `predetermined` and set `lag_limits[var]` |
| Strictly exogenous control | Put variable in `exogenous`; no GMM lag window required |
| Lagged exogenous regressor | Create `L1_` / `L2_` columns before estimation and include them in `exogenous` |
| Exogenous variable to be instrumented by its own lags | Reclassify as `predetermined` or `endogenous` and set `lag_limits[var]` |
| Interaction term with potentially endogenous components | Treat conservatively as `predetermined` or `endogenous` |
| Short panel with many instruments | Use `collapse=True` and narrow lag windows |
| Stata / pydynpd replication | Match sample, lag windows, transformation, collapse setting, IV treatment, time dummies, and covariance assumptions |

---

### Important caution

Variable classification is an econometric assumption.

`systemgmmkit` can construct the requested model, but it cannot determine whether a variable is truly endogenous, predetermined, or exogenous. That decision must be justified by theory, institutional knowledge, timing assumptions, and robustness checks.

---

## Generic Difference GMM

```python
from systemgmmkit import build_difference_gmm_spec

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
```

Difference GMM follows the Arellano-Bond dynamic-panel structure and uses lagged levels as instruments for transformed equations.

---

## Native dynamic-panel GMM

`systemgmmkit` includes a native dynamic-panel GMM backend for Difference GMM and System GMM.

The native backend has been validated against `pydynpd` on the current validation harness and passes strict coefficient parity for the tested specifications.

Supported native GMM features include:

- Difference GMM;
- System GMM;
- collapsed instruments;
- restricted lag windows;
- one-step and two-step estimation paths;
- pydynpd-compatible System GMM instrument ordering and weighting logic;
- effective observation count reporting;
- instrument-count reporting;
- structured result objects.

The native backend is intended to provide a transparent Python implementation that can be inspected, tested, and extended without relying only on an external backend.

---

## pydynpd backend adapter

`run_pydynpd()` returns a structured `PydynpdGMMResult` object.

The adapter:

- builds `pydynpd`-compatible command strings;
- groups IV-style instruments into a single `iv(...)` command block;
- captures printed backend output;
- extracts coefficients, standard errors, p-values, observation counts, instrument counts, and common GMM diagnostics where available;
- applies narrow compatibility shims for older `pydynpd` / NumPy combinations;
- serves as the Python reference backend for native GMM parity validation.

The compatibility shims are intentionally narrow. They are not intended to alter the econometric meaning of `pydynpd` results; they only handle backend compatibility issues such as scalar extraction behavior under newer NumPy versions.

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

`systemgmmkit` emphasizes reproducible panel-data workflows.

The package supports:

- structured model specifications;
- model-card style summaries;
- diagnostic interpretation;
- exportable regression tables;
- parity-check scaffolding;
- Stata replication-template generation;
- backend comparison workflows.

For dynamic-panel GMM, users should record at minimum:

- dependent variable;
- regressors;
- endogenous variables;
- predetermined variables;
- exogenous variables;
- lag windows;
- transformation;
- collapsed-instrument setting;
- time-dummy treatment;
- one-step or two-step configuration;
- covariance assumptions;
- backend used;
- software versions.

---

## Current production status

The current development branch adds native Random Effects, Panel IV/2SLS, table export, parity-test scaffolding, and native dynamic-panel GMM estimation.

Native Difference GMM and native System GMM now pass strict coefficient parity against `pydynpd` on the current validation harness, including the tested baseline, interaction, no-control, and decomposition specifications.

Native System GMM should still be validated across a broader multi-dataset test suite before being described as generally certified across all panel structures.

Windmeijer-corrected robust standard errors and exact Stata `xtabond2` equivalence remain under validation.

---

## Recommended validation roadmap

Before claiming broader production certification across panel designs, the package should be tested on:

- balanced panels;
- unbalanced panels;
- short-`T` panels;
- longer-`T` panels;
- high-`N`, low-`T` panels;
- panels with missing observations;
- different lag windows;
- models with no controls;
- models with many controls;
- interaction-heavy specifications;
- decomposition specifications;
- alternative instrument classifications;
- Stata `xtabond2` replication benchmarks.

This roadmap protects the package from overclaiming and supports academically defensible validation.

---

## Development principles

`systemgmmkit` is built around the following principles:

- generic design, not domain-specific hard-coding;
- transparent econometric specification;
- explicit backend behavior;
- reproducible reporting;
- strict parity testing where feasible;
- conservative claims about external-software equivalence;
- clear distinction between Python-backend parity and Stata parity;
- practical usability for applied empirical researchers.

---

## License

This project is licensed under the terms specified in the [LICENSE](LICENSE) file.

---

## Citation

If you use `systemgmmkit` in academic or applied research, cite the package version or Git commit, backend used, and model specification details.

Recommended reporting format:

```text
Estimation was performed using systemgmmkit version X.Y.Z, commit <commit-hash>. Dynamic-panel GMM results used the [native / pydynpd] backend with collapsed instruments, restricted lag windows, and [one-step / two-step] estimation. Specification details, panel structure, and instrument classification are reported in the model documentation.
```
