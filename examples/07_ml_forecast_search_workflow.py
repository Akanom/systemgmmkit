"""Panel-aware ML workflow: split/CV, forecast, backtest, GMM search.

Run:
    python examples/07_ml_forecast_search_workflow.py
"""

from __future__ import annotations

import pandas as pd

from systemgmmkit import OLSSpec, build_difference_gmm_spec, run_difference_gmm, run_ols
from systemgmmkit.ml import (
    GMMGridSearch,
    GMMRankingWeights,
    GMMValidityRules,
    PanelTimeSeriesSplit,
    backtest_forecast,
    compare_models,
    cross_validate_panel,
    forecast,
    panel_train_test_split,
)

from _shared_panel_data import ensure_results_dir, make_dynamic_panel, make_static_panel, write_table_pair


def fit_dynamic_ols(data: pd.DataFrame):
    return run_ols(
        OLSSpec(
            dependent="growth",
            regressors=["L1_growth", "investment", "leverage", "size"],
            controls=["cashflow"],
            covariance="robust",
            name="dynamic_ols_forecast",
        ),
        data.dropna(subset=["L1_growth"]),
        entity="firm_id",
        time="year",
    )


def run_forecast_block() -> None:
    df = make_static_panel().dropna(subset=["L1_growth"]).copy()
    train, test = panel_train_test_split(df, time="year", test_size=2)

    train_result = fit_dynamic_ols(train)
    full_result = fit_dynamic_ols(df)

    cv = cross_validate_panel(
        estimator=fit_dynamic_ols,
        data=df,
        y="growth",
        time="year",
        cv=PanelTimeSeriesSplit(n_splits=3, min_train_periods=5, test_periods=1),
        predict_kwargs={"strict": False},
    )
    write_table_pair(cv, "07_ml_panel_cv_scores")

    comparison = compare_models(
        {"Dynamic OLS": train_result},
        test,
        y="growth",
        predict_kwargs={"strict": False},
    )
    write_table_pair(comparison, "07_ml_holdout_comparison")

    future_exog = (
        df.sort_values(["firm_id", "year"])
        .groupby("firm_id", as_index=False)
        .tail(1)
        .loc[:, ["firm_id", "year", "investment", "leverage", "size", "cashflow"]]
        .copy()
    )
    future_exog["year"] = future_exog["year"] + 1

    one_step_forecast = forecast(
        full_result,
        df,
        y="growth",
        entity="firm_id",
        time="year",
        horizon=1,
        future_exog=future_exog,
        strict=False,
    )
    write_table_pair(one_step_forecast.head(20), "07_ml_one_step_forecast_head")

    backtest = backtest_forecast(
        result_factory=fit_dynamic_ols,
        data=df,
        y="growth",
        entity="firm_id",
        time="year",
        horizon=1,
        min_train_periods=5,
        max_cutoffs=3,
        strict=False,
    )
    write_table_pair(backtest, "07_ml_forecast_backtest")

    print("Panel CV scores")
    print(cv.round(4).to_string(index=False))
    print("\nForecast backtest")
    print(backtest.round(4).to_string(index=False))


def build_gmm_spec(**params):
    lag_window = params.pop("lag_window")
    return build_difference_gmm_spec(
        dependent="y",
        regressors=["x1", "x2", "control"],
        endogenous=["x1"],
        predetermined=["x2"],
        exogenous=["control"],
        lag_limits={
            "y": lag_window,
            "x1": (2, 2),
            "x2": (2, 2),
        },
        collapse=params.pop("collapse"),
        transformation=params.pop("transformation"),
        steps=params.pop("steps"),
        time_dummies=False,
        name=f"diff_gmm_{lag_window[0]}_{lag_window[1]}",
    )


def run_gmm_model(spec, data: pd.DataFrame, *, entity: str, time: str):
    return run_difference_gmm(spec, data, entity=entity, time=time, backend="native")


def run_search_block() -> None:
    df = make_dynamic_panel(n_entities=70, n_periods=10)

    search = GMMGridSearch(
        build_spec=build_gmm_spec,
        run_model=run_gmm_model,
        param_grid=[
            {"lag_window": (2, 2), "collapse": True, "transformation": "fd", "steps": "twostep"},
            {"lag_window": (2, 3), "collapse": True, "transformation": "fd", "steps": "twostep"},
        ],
        y="y",
        entity="entity_id",
        time="year",
        test_size=2,
        validity_rules=GMMValidityRules(
            min_hansen_p=0.05,
            min_ar2_p=0.05,
            max_instrument_ratio=1.0,
        ),
        ranking_weights=GMMRankingWeights(
            prediction=1.0,
            instruments=0.20,
            hansen=0.10,
            ar2=0.10,
        ),
        predict_kwargs={"strict": False},
    )

    result = search.fit(df)
    write_table_pair(result.results, "07_gmm_diagnostic_first_search")

    report_path = ensure_results_dir() / "07_gmm_diagnostic_first_search_report.md"
    report_path.write_text(
        result.report,
        encoding="utf-8",
    )

    print("\nDiagnostic-first GMM search")
    print(result.results.round(4).to_string(index=False))
    print("\nBest admissible spec:")
    print(result.best_spec)


def main() -> None:
    run_forecast_block()
    run_search_block()
    print("\nWrote results under examples/results/07_*")


if __name__ == "__main__":
    main()
