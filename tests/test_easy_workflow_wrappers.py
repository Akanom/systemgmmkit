from __future__ import annotations

import pandas as pd

from systemgmmkit.ml import (
    quick_forecast,
    quick_ml,
    quick_postestimation,
)


class LinearResult:
    def __init__(self) -> None:
        self.params = pd.Series({"x": 2.0, "_con": 1.0})
        self.cov = pd.DataFrame(
            [[0.04, 0.0], [0.0, 0.01]],
            index=self.params.index,
            columns=self.params.index,
        )
        self.diagnostics = {
            "hansen_p": 0.25,
            "ar2_p": 0.40,
        }


class DynamicResult:
    def __init__(self) -> None:
        self.params = pd.Series({"L1.y": 0.5, "x": 1.0, "_con": 0.0})
        self.diagnostics = {
            "hansen_p": 0.35,
            "ar2_p": 0.50,
        }


def test_quick_postestimation_returns_common_outputs():
    data = pd.DataFrame({"y": [3.0, 5.0, 7.0], "x": [1.0, 2.0, 3.0]})

    summary = quick_postestimation(
        LinearResult(),
        data,
        y="y",
        variables=["x"],
        lincoms={"slope": "x = 2"},
        wald_tests={"slope_zero": "x = 0"},
        include_vcov=True,
    )

    assert summary.predictions is not None
    assert summary.predictions.tolist() == [3.0, 5.0, 7.0]
    assert summary.metrics["rmse"] == 0.0
    assert summary.confidence_intervals is not None
    assert "x" in summary.confidence_intervals.index
    assert summary.marginal_effects is not None
    assert summary.marginal_effects.loc["x", "effect"] == 2.0
    assert summary.linear_combinations is not None
    assert summary.linear_combinations.loc[0, "name"] == "slope"
    assert summary.wald_tests is not None
    assert summary.wald_tests.loc[0, "name"] == "slope_zero"
    assert summary.covariance is not None
    assert summary.diagnostics["hansen_p"] == 0.25
    assert not summary.errors
    assert "Post-estimation summary" in summary.to_markdown()


def test_quick_forecast_scores_against_future_actuals():
    history = pd.DataFrame(
        {
            "id": [1, 1, 1, 2, 2, 2],
            "t": [1, 2, 3, 1, 2, 3],
            "y": [2.0, 3.0, 4.0, 4.0, 5.0, 6.0],
            "x": [1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
        }
    )
    future = pd.DataFrame(
        {
            "id": [1, 2],
            "t": [4, 4],
            "x": [2.0, 2.0],
            "y": [4.0, 5.0],
        }
    )

    summary = quick_forecast(
        DynamicResult(),
        history,
        y="y",
        entity="id",
        time="t",
        horizon=1,
        future_exog=future,
    )

    assert len(summary.forecast) == 2
    assert summary.metrics["rmse"] == 0.0
    assert not summary.errors
    assert "Forecast summary" in summary.to_markdown()


def test_quick_ml_combines_evaluation_and_optional_forecast():
    history = pd.DataFrame(
        {
            "id": [1, 1, 1],
            "t": [1, 2, 3],
            "y": [2.0, 3.0, 4.0],
            "x": [1.0, 1.0, 1.0],
        }
    )
    future = pd.DataFrame({"id": [1], "t": [4], "x": [2.0], "y": [4.0]})

    summary = quick_ml(
        DynamicResult(),
        history,
        y="y",
        entity="id",
        time="t",
        horizon=1,
        future_exog=future,
    )

    assert summary.postestimation.diagnostics["ar2_p"] == 0.50
    assert summary.forecast is not None
    assert summary.forecast.metrics["n"] == 1.0


def test_easy_workflow_helpers_are_available_from_top_level_package():
    import systemgmmkit as sgk

    assert sgk.quick_postestimation is quick_postestimation
    assert sgk.quick_forecast is quick_forecast
    assert sgk.quick_ml is quick_ml
    assert callable(sgk.auto_dynamic_gmm)
