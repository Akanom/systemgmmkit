# systemgmmkit examples

This folder contains minimal runnable examples for the public `systemgmmkit` API.

## Examples

| File | Purpose |
|---|---|
| `00_quick_user_path.py` | Simplest top-level workflow with OLS, post-estimation, `lincom`, and `wald_test` |
| `01_fixed_effects_quickstart.py` | Two-way fixed effects quickstart with synthetic panel data |
| `02_difference_gmm_quickstart.py` | Difference GMM quickstart with synthetic dynamic-panel data |
| `03_system_gmm_backend_auto.py` | System GMM quickstart using `backend="auto"` |

## Run examples

From the repository root:

```bash
python -m pip install -e ".[dev,all]"
python examples/00_quick_user_path.py
python examples/01_fixed_effects_quickstart.py
python examples/02_difference_gmm_quickstart.py
python examples/03_system_gmm_backend_auto.py
```

## Validation note

The examples are designed to demonstrate the public API. They are not a substitute for empirical validation, Stata replication, or estimator-specific diagnostic review.
