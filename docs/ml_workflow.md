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
