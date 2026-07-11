# systemgmmkit examples

These examples are meant to let a new user run the package end to end, not just
read the API. They use generated panel data so they run on any machine. Formal
Stata/parity checks remain in `artifacts/`.

## Quick path

Run these first if you only want the main ideas:

```bash
python examples/00_quick_user_path.py
python examples/01_fixed_effects_quickstart.py
python examples/02_difference_gmm_quickstart.py
python examples/03_system_gmm_backend_auto.py
```

## Comprehensive examples

| File | What it shows | Main outputs |
|---|---|---|
| `05_static_panel_iv_workflow.py` | OLS, pooled OLS, two-way FE, RE, panel IV/2SLS, holdout comparison, post-estimation | `examples/results/05_*` |
| `06_dynamic_gmm_workflow.py` | Native Difference GMM and native System GMM, including AR(1), AR(2), Hansen/Sargan, instrument count, model card | `examples/results/06_*` |
| `07_ml_forecast_search_workflow.py` | Time-respecting panel split, expanding CV, recursive forecast, backtest, diagnostic-first GMM search | `examples/results/07_*` |
| `08_postestimation_visualization_workflow.py` | Confidence intervals, marginal effects, lincom, Wald tests, residual diagnostics, saved figures | `examples/results/08_*` |

Run them from the repository root:

```bash
python examples/05_static_panel_iv_workflow.py
python examples/06_dynamic_gmm_workflow.py
python examples/07_ml_forecast_search_workflow.py
python examples/08_postestimation_visualization_workflow.py
```

## Older example names

These still run, but now point to the same runnable workflow style:

```bash
python examples/fe_re_iv_gmm_usage.py
python examples/ml_workflow_example.py
```

## Results

The comprehensive examples write small CSV, Markdown, text, and PNG outputs to
`examples/results/`. These outputs are included as examples only: they show what
users should expect from the workflow on reproducible data. They are not meant
to replace estimator validation or the submitted paper evidence.

## Install

From the repository root:

```bash
python -m pip install -e ".[dev,all]"
```
