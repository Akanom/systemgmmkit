# ML-Style Workflow Layer

`systemgmmkit.ml` adds machine-learning-style workflow utilities around already validated econometric estimators.

The design principle is simple:

Keep accepted estimators stable; build workflow capabilities around them.

## Included tools

- `predict`
- `fitted_values`
- `residuals`
- `regression_metrics`
- `panel_train_test_split`
- `PanelTimeSeriesSplit`
- `cross_validate_panel`
- `GMMGridSearch`

## Basic usage

    from systemgmmkit.ml import predict, fitted_values, residuals

    pred = predict(result, data)
    fit = fitted_values(result, data)
    err = residuals(result, data, y="growth_rate")

## Panel cross-validation

    from systemgmmkit.ml import PanelTimeSeriesSplit, cross_validate_panel

    cv = PanelTimeSeriesSplit(
        n_splits=5,
        min_train_periods=10,
        test_periods=1,
    )

    scores = cross_validate_panel(
        estimator=my_estimator,
        data=df,
        y="growth_rate",
        time="year",
        cv=cv,
    )

The split is time-respecting. It does not randomly split panel rows.

## GMM specification search

    from systemgmmkit.ml import GMMGridSearch

    search = GMMGridSearch(
        build_spec=build_system_gmm_spec,
        run_model=run_system_gmm,
        param_grid=[
            {"lag_window": (2, 2), "collapse": True},
            {"lag_window": (2, 3), "collapse": True},
            {"lag_window": (2, 4), "collapse": True},
        ],
        y="growth_rate",
        entity="country",
        time="year",
        diagnostic_rules={
            "hansen_p": (">", 0.05),
            "ar2_p": (">", 0.05),
        },
    )

    result = search.fit(df)

## Why this matters

Most econometric packages stop after estimation. This layer supports the workflow after estimation:

1. predict
2. evaluate
3. compare
4. search specifications
5. communicate results

The validated econometric core remains unchanged.

## Model comparison

`compare_models` compares already fitted model results on a shared evaluation dataset.

    from systemgmmkit.ml import compare_models

    table = compare_models(
        models={
            "OLS": ols_result,
            "Fixed Effects": fe_result,
            "System GMM": sysgmm_result,
        },
        data=test_df,
        y="growth_rate",
    )

The output includes standard prediction metrics:

- MAE
- MSE
- RMSE
- MAPE
- SMAPE
- R²

If available, scalar model diagnostics are also included with a `diag_` prefix, for example:

- `diag_hansen_p`
- `diag_ar2_p`
- `diag_n_instruments`

This allows users to compare predictive performance and econometric validity in one table.

## Forecasting

`forecast` generates recursive forecasts from an already fitted result object.

    from systemgmmkit.ml import forecast

    fc = forecast(
        result=sysgmm_result,
        history=df,
        y="growth_rate",
        entity="country",
        time="year",
        horizon=4,
        future_exog=future_controls,
    )

For dynamic panel models, lagged dependent-variable terms are detected from coefficient names such as:

- `L1.y`
- `L2.y`
- `L.y`
- `y_lag1`
- `lag1_y`
- `L1_y`

The function recursively updates lagged dependent variables using previous forecasts.

If `future_exog` is not supplied, the latest observed exogenous values are held constant for each entity.

## Forecast backtesting

`backtest_forecast` evaluates recursive forecasts over expanding time cutoffs.

    from systemgmmkit.ml import backtest_forecast

    scores = backtest_forecast(
        result_factory=my_estimator,
        data=df,
        y="growth_rate",
        entity="country",
        time="year",
        horizon=4,
        min_train_periods=10,
    )

The `result_factory` should return an already fitted model result for the training data.

Example:

    def my_estimator(data):
        spec = build_system_gmm_spec(...)
        return run_system_gmm(
            spec,
            data,
            entity="country",
            time="year",
        )

    scores = backtest_forecast(
        result_factory=my_estimator,
        data=df,
        y="growth_rate",
        entity="country",
        time="year",
        horizon=4,
    )

The output contains one row per cutoff and forecast horizon, including:

- cutoff
- horizon
- train_n
- test_n
- MAE
- MSE
- RMSE
- MAPE
- SMAPE
- R²

## Smoke demonstration

A reviewer-facing smoke script is provided:

    python scripts/ml/run_ml_workflow_smoke.py

By default, it writes outputs to:

    artifacts/ml_workflow/

The smoke script demonstrates:

- real OLS prediction, fitted values, and residuals
- panel time-series cross-validation
- model comparison
- GMM specification-search scaffold
- recursive forecasting
- forecast backtesting

The script is intended as a reproducible demonstration that the ML workflow layer operates around accepted estimators without modifying estimator internals.
