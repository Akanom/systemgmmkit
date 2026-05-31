# systemgmmkit

`systemgmmkit` is a small research workflow package for fixed-effects and dynamic panel Difference/System GMM work in Python.

It does **not** try to replace mature econometric engines. Instead, it gives you a clean layer around System GMM workflows:

- validate panel data before estimation;
- estimate static one-/two-way fixed-effects models using a native LSDV backend or optional `linearmodels`;
- classify dynamic-panel variables as endogenous, predetermined, or exogenous;
- build `pydynpd` command strings from structured Python objects;
- reduce instrument-proliferation risk through lag-depth and collapse defaults;
- generate thesis-ready diagnostic summaries;
- provide reusable specifications for aid-growth FE and System GMM models.

## Stata equivalence policy

The package should be treated as **Stata-aligned**, not automatically Stata-identical. Results can be synonymous with Stata `xtreg, fe` and `xtabond2` only when the same sample, transformations, instrument matrix, lag windows, collapsed instruments, time dummies, finite-sample corrections, and covariance assumptions are used. Minor numerical differences can still occur because Python and Stata use different backend implementations and matrix tolerances.

## Why this package exists

Python already has packages that implement System GMM, especially `pydynpd`. The practical gap is not only estimation. The gap is **reproducible specification management**: keeping lag structures, instrument classifications, controls, interactions, diagnostics, and reporting consistent across models.

This package targets that gap.

## Install locally

```bash
cd systemgmmkit
python -m pip install -e ".[all]"
```

## Minimal System GMM usage

```python
import pandas as pd
from systemgmmkit import DynamicPanelSpec, GMMStyle, IVStyle, build_pydynpd_command

spec = DynamicPanelSpec(
    dependent="growth_rate",
    regressors=[
        "L1.growth_rate",
        "lPA",
        "s_techshare",
        "frag_index_orth",
        "polity2",
        "econ_dev_index",
        "human_dev_index",
        "lpop",
    ],
    gmm=[
        GMMStyle("growth_rate", min_lag=2, max_lag=3),
        GMMStyle("lPA", min_lag=2, max_lag=2),
        GMMStyle("s_techshare", min_lag=2, max_lag=2),
        GMMStyle("frag_index_orth", min_lag=2, max_lag=2),
        GMMStyle("polity2", min_lag=2, max_lag=2),
    ],
    iv=[IVStyle("econ_dev_index"), IVStyle("human_dev_index"), IVStyle("lpop")],
    time_dummies=True,
    system=True,
    collapse=True,
    transformation="fod",
    steps="twostep",
)

command = build_pydynpd_command(spec)
print(command)
```


## Fixed-effects usage

```python
import pandas as pd
from systemgmmkit import FixedEffectsSpec, run_fixed_effects

df = pd.read_csv("analysis_merged_data_copy.csv")

fe_spec = FixedEffectsSpec(
    dependent="growth_rate",
    regressors=["lPA", "s_techshare", "frag_index_orth", "polity2"],
    entity_effects=True,
    time_effects=True,
    covariance="clustered",
    cluster="entity",
)

result = run_fixed_effects(fe_spec, df, entity="country_id", time="period4")
print(result.to_markdown())
```

## Run via pydynpd backend

```python
from systemgmmkit import run_pydynpd

result = run_pydynpd(spec, df, panel_ids=["country_id", "period4"])
```

`pydynpd` must be installed:

```bash
python -m pip install systemgmmkit[pydynpd]
```

## Thesis aid-growth presets

```python
from systemgmmkit.presets import (
    aid_growth_fe_techshare_spec,
    aid_growth_ta_decomposition_spec,
    aid_growth_techshare_spec,
    aid_growth_techshare_suite,
)

fe_spec = aid_growth_fe_techshare_spec(include_controls=True, include_three_way=True)
gmm_spec = aid_growth_techshare_spec(include_controls=True, include_three_way=True)
decomp_spec = aid_growth_ta_decomposition_spec(include_controls=True, include_three_way=True)
suite = aid_growth_techshare_suite(include_controls=True, include_three_way=True)
```

## Important status

This is version `0.2.0`: a package scaffold, fixed-effects estimator, and System GMM specification/reporting layer. The estimation backend delegates to `pydynpd` when installed. Full native System GMM estimation, Windmeijer correction, and xtabond2 parity tests are future milestones, not yet claimed.

## GitHub production workflow

Use this repository as a normal Python package, not as a one-off notebook export.

```bash
git checkout -b feature/<feature-name>
python -m pip install -e ".[dev,all]"
ruff check .
pytest
python -m build
git add .
git commit -m "feat: add <feature-name>"
git push -u origin feature/<feature-name>
```

Open a pull request. Merge only after CI passes.

See [`docs/PRODUCTION.md`](docs/PRODUCTION.md) for the release workflow.
