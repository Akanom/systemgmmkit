# systemgmmkit

`systemgmmkit` is a **generic panel-data workflow package** for Python. It supports reusable model specification, validation, reporting, fixed-effects estimation, and Difference/System GMM workflows.

It is **not limited to aid-growth models**. Aid-growth specifications are kept only as optional domain examples in `systemgmmkit.domain_presets`.

## What the package does

- validate balanced and unbalanced panel datasets before estimation;
- estimate static panel models using a native backend:
  - pooled OLS by setting `entity_effects=False` and `time_effects=False`;
  - one-way fixed effects;
  - two-way fixed effects;
- build generic dynamic-panel GMM specifications:
  - Arellano-Bond Difference GMM via `system=False`;
  - Blundell-Bond System GMM via `system=True`;
  - one-step, two-step, and iterated command options where supported by the backend;
  - collapsed instruments and restricted lag windows;
- classify regressors into GMM-style internally instrumented variables and IV/exogenous variables;
- generate diagnostic and model-card style reporting;
- run through the optional `pydynpd` backend when installed.

## Stata equivalence policy

The package should be treated as **Stata-aligned**, not automatically Stata-identical. Results can align with Stata `xtreg, fe` and `xtabond2` only when the same sample, transformations, lag windows, collapsed instruments, time dummies, covariance assumptions, and finite-sample corrections are used.

## Install locally

```bash
python -m pip install -e ".[all]"
```

## Generic fixed effects

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

result = run_fixed_effects(spec, df, entity="country_id", time="year")
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

## Run via pydynpd backend

```python
from systemgmmkit import run_pydynpd

result = run_pydynpd(spec, df, panel_ids=["entity_id", "time_id"])
```

Install backend support:

```bash
python -m pip install "systemgmmkit[pydynpd]"
```

## Domain examples

Aid-growth examples are available but deliberately separated from the generic core:

```python
from systemgmmkit.domain_presets import aid_growth_techshare_spec
```

## Current production status

Version `0.3.0` is a generic panel-model specification and workflow package. Native fixed-effects estimation is included. Difference/System GMM estimation delegates to `pydynpd` when installed. Full native System GMM, Windmeijer correction, random effects, IV panel estimators, and xtabond2 parity tests remain future milestones.
