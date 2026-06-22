# systemgmmkit ML Workflow Smoke Artifacts

This directory contains reviewer-facing smoke outputs for the additive
`systemgmmkit.ml` workflow layer.

Generated files:

- `static_panel.csv`: synthetic static panel used for OLS workflow checks.
- `dynamic_panel.csv`: synthetic dynamic panel used for forecasting checks.
- `ols_predictions_residuals.csv`: predictions, fitted values, and residuals.
- `panel_cv_scores.csv`: panel time-series cross-validation metrics.
- `model_comparison.csv`: ML-style comparison of fitted model results.
- `gmm_grid_search.csv`: GMM specification-search scaffold output.
- `forecast.csv`: recursive dynamic-panel forecast output.
- `forecast_backtest.csv`: expanding-window forecast backtest metrics.
- `summary.json`: machine-readable run summary.

The smoke script does not alter validated estimator internals.
