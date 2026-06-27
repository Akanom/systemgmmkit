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
- `quick_postestimation`
- `quick_forecast`
- `quick_ml`
- `GMMGridSearch`
- `DynamicGMMHybridSearch`
- `auto_dynamic_gmm`
- `dynamic_gmm_candidate_grid`

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

## Simple wrapper UI

For common fitted-result workflows, the quick helpers bundle the usual steps
without changing estimator behavior.

    from systemgmmkit import lincom, wald_test
    from systemgmmkit.ml import quick_postestimation, quick_forecast, quick_ml

    post = quick_postestimation(
        result,
        df,
        y="growth_rate",
    )

    post.metrics
    post.confidence_intervals
    post.marginal_effects

    total_effect = lincom(result, "investment + trade_open")
    joint_test = wald_test(result, "investment = 0, trade_open = 0")

    post_with_tests = quick_postestimation(
        result,
        df,
        y="growth_rate",
        lincoms={"total_effect": "investment + trade_open"},
        wald_tests={"joint_zero": "investment = 0, trade_open = 0"},
    )

    fc = quick_forecast(
        result,
        history=df,
        y="growth_rate",
        entity="country",
        time="year",
        horizon=4,
        future_exog=future_controls,
    )

    workflow = quick_ml(
        result,
        df,
        y="growth_rate",
        entity="country",
        time="year",
        horizon=4,
        future_exog=future_controls,
    )

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

`GMMGridSearch` remains a generic scaffold: users supply the specification
builder and model runner, and the search layer only orchestrates fitting,
diagnostics, prediction metrics, ranking, and reporting.

For the simplest native Dynamic GMM workflow, use the one-call helper. It
searches around the public `system_gmm` and `difference_gmm` easy APIs without
changing estimator internals.

    from systemgmmkit.ml import auto_dynamic_gmm

    result = auto_dynamic_gmm(
        df,
        y="growth_rate",
        entity="country",
        time="year",
        regressors=["investment", "trade_open"],
        endogenous=["investment"],
        exogenous=["trade_open"],
        test_size=2,
    )

    best_result = result.best_result
    best_spec = result.best_spec
    report = result.to_markdown()

For more control, instantiate the hybrid loop directly.

    from systemgmmkit.ml import DynamicGMMHybridSearch

    search = DynamicGMMHybridSearch(
        y="growth_rate",
        entity="country",
        time="year",
        regressors=["investment", "trade_open"],
        endogenous=["investment"],
        exogenous=["trade_open"],
        lag_windows=[(2, 2), (2, 3), (3, 4)],
        models=["system", "difference"],
        steps=["twostep", "onestep"],
        transformations=["fod", "fd"],
        test_size=2,
    )

    result = search.fit(df)

    best_result = result.best_result
    best_spec = result.best_spec
    report = result.to_markdown()

The hybrid loop rejects candidates before ranking when diagnostics fail,
including AR(2), Hansen, convergence, and excessive instrument-count checks.
Prediction quality is used only after econometric validity screening.

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
