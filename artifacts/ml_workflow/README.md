# systemgmmkit ML Workflow Smoke Demo

This folder contains outputs from the ML-style workflow smoke script.

The smoke script demonstrates the additive workflow layer around already accepted estimators.

## Outputs

| File | Purpose |
|---|---|
| `static_panel.csv` | Synthetic static panel dataset |
| `dynamic_panel.csv` | Synthetic dynamic panel dataset |
| `ols_predictions_residuals.csv` | Prediction, fitted values, and residuals from real OLS |
| `panel_cv_scores.csv` | Panel time-series cross-validation scores |
| `model_comparison.csv` | ML-style comparison of fitted econometric models |
| `gmm_grid_search.csv` | GMM specification-search scaffold output |
| `forecast.csv` | Recursive dynamic-panel forecast output |
| `forecast_backtest.csv` | Expanding-window forecast backtest scores |
| `summary.json` | Machine-readable smoke-run summary |

## Status

PASS

## Design principle

The workflow layer does not modify estimator internals. It wraps already fitted results with prediction, validation, comparison, forecasting, and backtesting utilities.
