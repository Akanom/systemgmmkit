# systemgmmkit

`systemgmmkit` is a generic Python workflow package for panel-data econometrics.

It supports reusable model specification, panel validation, fixed-effects estimation, Random Effects estimation, Panel IV/2SLS estimation, Difference GMM and System GMM command construction, diagnostics interpretation, reproducible model reporting, and basic regression-table export.

The package is designed for applied panel-data projects in economics, finance, management, operations, productivity analysis, political economy, industrial organization, firm-level research, country panels, regional panels, household panels, and other longitudinal-data settings.

## Core capabilities

- Validate balanced and unbalanced panel datasets before estimation.
- Estimate static panel models using the native backend:
  - pooled OLS-style models;
  - one-way fixed effects;
  - two-way fixed effects;
  - one-way Random Effects;
  - Panel IV / 2SLS with optional fixed effects.
- Build dynamic-panel GMM specifications:
  - Arellano-Bond Difference GMM;
  - Blundell-Bond System GMM;
  - collapsed instruments;
  - restricted lag windows;
  - one-step, two-step, and iterated configuration where supported by the backend.
- Run dynamic-panel GMM through the optional `pydynpd` backend when installed.
- Run an experimental native one-step dynamic-panel GMM estimator for small validation workflows.
- Generate model-card style reporting for reproducibility.
- Export regression summaries to Markdown, CSV, or LaTeX.
- Generate Stata parity-check do-file templates for `xtreg, fe` and `xtabond2` replication work.

## Stata-alignment policy

The package should be treated as Stata-aligned, not automatically Stata-identical.

Results can align with Stata `xtreg, fe` and `xtabond2` only when the same sample, transformation, lag windows, instrument matrix, collapsed-instrument setting, time dummies, covariance assumptions, and finite-sample corrections are used.

Exact Stata parity should be verified using dedicated replication tests. Native dynamic-panel GMM remains experimental until parity tests are documented.

## Installation

Development installation:

```bash
python -m pip install -e ".[dev,all]"
```

Runtime installation:

```bash
python -m pip install -e ".[all]"
```

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

result = run_fixed_effects(spec, df, entity="entity_id", time="year")
print(result.to_markdown())
```

## Generic Random Effects

```python
from systemgmmkit import RandomEffectsSpec, run_random_effects

spec = RandomEffectsSpec(
    dependent="y",
    regressors=["x1", "x2"],
    covariance="robust",
)

result = run_random_effects(spec, df, entity="entity_id", time="year")
print(result.to_markdown())
```

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

result = run_panel_2sls(spec, df, entity="entity_id", time="year")
print(result.to_markdown())
```

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
    lag_limits={"y": (2, 3), "x1": (2, 2), "x2": (2, 2)},
    collapse=True,
    time_dummies=True,
    steps="twostep",
    name="generic_system_gmm",
)

print(build_pydynpd_command(spec))
```

## Generic Difference GMM

```python
from systemgmmkit import build_difference_gmm_spec

spec = build_difference_gmm_spec(
    dependent="y",
    regressors=["x1", "x2"],
    endogenous=["x1"],
    predetermined=["x2"],
    exogenous=[],
    collapse=True,
    name="generic_difference_gmm",
)
```

## Regression-table export

```python
from systemgmmkit import export_regression_table

export_regression_table([fe_result, re_result, iv_result], "results.md", fmt="markdown")
export_regression_table([fe_result, re_result, iv_result], "results.csv", fmt="csv")
export_regression_table([fe_result, re_result, iv_result], "results.tex", fmt="latex")
```

## Current production status

Version `0.4.0` adds native Random Effects, Panel IV/2SLS, table export, parity-test scaffolding, and an experimental native one-step dynamic-panel GMM engine.

Native System GMM and Windmeijer-corrected robust standard errors are not yet certified as Stata-equivalent. Treat them as experimental until parity tests against `xtabond2` pass.
