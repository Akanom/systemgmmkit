# systemgmmkit

`systemgmmkit` is a generic Python workflow package for panel-data econometrics.

It supports reusable model specification, panel validation, static panel estimation, dynamic-panel GMM estimation, diagnostics interpretation, reproducible model reporting, and regression-table export.

The package is designed for applied panel-data projects in economics, finance, management, operations, productivity analysis, political economy, industrial organization, firm-level research, country panels, regional panels, household panels, and other longitudinal-data settings.

---

## Core capabilities

`systemgmmkit` currently supports:

* Validation of balanced and unbalanced panel datasets before estimation.
* Static panel estimation using native Python backends:

  * pooled OLS-style models;
  * one-way fixed effects;
  * two-way fixed effects;
  * one-way Random Effects;
  * Panel IV / 2SLS with optional fixed effects.
* Dynamic-panel GMM model construction and estimation:

  * Arellano-Bond Difference GMM;
  * Blundell-Bond System GMM;
  * collapsed instruments;
  * restricted lag windows;
  * one-step and two-step configurations where supported by the backend.
* Native Difference GMM and native System GMM estimation.
* Optional `pydynpd` backend integration for dynamic-panel GMM.
* Strict coefficient-parity validation between the native GMM backend and `pydynpd` on the current validation harness.
* Model-card style reporting for reproducibility.
* Regression-table export to Markdown, CSV, and LaTeX.
* Stata parity-check do-file templates for `xtreg, fe` and `xtabond2` replication workflows.

---

## Current validation status

The native Difference GMM and native System GMM estimators pass strict coefficient parity against `pydynpd` on the current validation harness.

The current validation harness includes:

* Difference GMM baseline with controls;
* System GMM baseline with controls;
* System GMM three-way interaction model with controls;
* System GMM three-way interaction model without controls;
* System GMM decomposition model with controls.

For these tested specifications, the native backend matches `pydynpd` on:

* effective observation count;
* number of instruments;
* coefficient signs;
* strict coefficient parity;
* tested baseline, interaction, no-control, and decomposition structures.

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

If you only need the core package without optional backends, use:

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

## Native dynamic-panel GMM

`systemgmmkit` includes a native dynamic-panel GMM backend for Difference GMM and System GMM.

The native backend has been validated against `pydynpd` on the current validation harness and passes strict coefficient parity for the tested specifications.

Supported native GMM features include:

* Difference GMM;
* System GMM;
* collapsed instruments;
* restricted lag windows;
* one-step and two-step estimation paths;
* pydynpd-compatible System GMM instrument ordering and weighting logic;
* effective observation count reporting;
* instrument-count reporting;
* structured result objects.

The native backend is intended to provide a transparent Python implementation that can be inspected, tested, and extended without relying only on an external backend.

---

## pydynpd backend adapter

`run_pydynpd()` returns a structured `PydynpdGMMResult` object.

The adapter:

* builds `pydynpd`-compatible command strings;
* groups IV-style instruments into a single `iv(...)` command block;
* captures printed backend output;
* extracts coefficients, standard errors, p-values, observation counts, instrument counts, and common GMM diagnostics where available;
* applies narrow compatibility shims for older `pydynpd` / NumPy combinations;
* serves as the Python reference backend for native GMM parity validation.

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

* structured model specifications;
* model-card style summaries;
* diagnostic interpretation;
* exportable regression tables;
* parity-check scaffolding;
* Stata replication-template generation;
* backend comparison workflows.

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

## Current production status

Version `0.4.1` adds native Random Effects, Panel IV/2SLS, table export, parity-test scaffolding, and native dynamic-panel GMM estimation.

Native Difference GMM and native System GMM now pass strict coefficient parity against `pydynpd` on the current validation harness, including the tested baseline, interaction, no-control, and decomposition specifications.

Native System GMM should still be validated across a broader multi-dataset test suite before being described as generally certified across all panel structures.

Windmeijer-corrected robust standard errors and exact Stata `xtabond2` equivalence remain under validation.

---

## Recommended validation roadmap

Before claiming broader production certification across panel designs, the package should be tested on:

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

This roadmap protects the package from overclaiming and supports academically defensible validation.

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

Add the project license here.

---

## Citation

If you use `systemgmmkit` in academic or applied research, cite the package version, backend used, and model specification details.

Recommended reporting format:

```text
Estimation was performed using systemgmmkit version X.Y.Z. Dynamic-panel GMM results used the [native / pydynpd] backend with collapsed instruments, restricted lag windows, and [one-step / two-step] estimation. Specification details, panel structure, and instrument classification are reported in the model documentation.
```
