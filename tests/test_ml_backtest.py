import numpy as np
import pandas as pd

from systemgmmkit.ml import backtest_forecast


class DynamicResult:
    params = pd.Series(
        {
            "L1.y": 0.5,
            "x": 1.0,
            "_con": 0.0,
        }
    )


class StaticResult:
    params = pd.Series(
        {
            "x": 2.0,
            "_con": 1.0,
        }
    )


def make_panel():
    rows = []
    for ent in [1, 2]:
        y_prev = float(ent)
        for t in range(1, 8):
            x = 10.0
            y = 0.5 * y_prev + x
            rows.append({"id": ent, "t": t, "y": y, "x": x})
            y_prev = y
    return pd.DataFrame(rows)


def test_backtest_forecast_dynamic_result_factory():
    df = make_panel()

    def result_factory(data):
        return DynamicResult()

    out = backtest_forecast(
        result_factory=result_factory,
        data=df,
        y="y",
        entity="id",
        time="t",
        horizon=2,
        min_train_periods=3,
        max_cutoffs=2,
    )

    assert len(out) == 4
    assert set(out["horizon"]) == {1, 2}
    assert out["error"].fillna("").eq("").all()
    assert np.isfinite(out["rmse"]).all()


def test_backtest_forecast_accepts_data_keyword_factory():
    df = make_panel()

    def result_factory(*, data):
        assert len(data) > 0
        return DynamicResult()

    out = backtest_forecast(
        result_factory=result_factory,
        data=df,
        y="y",
        entity="id",
        time="t",
        horizon=1,
        min_train_periods=3,
        max_cutoffs=2,
    )

    assert len(out) == 2
    assert out["test_n"].min() > 0


def test_backtest_forecast_static_model():
    df = pd.DataFrame(
        {
            "id": [1, 1, 1, 1, 2, 2, 2, 2],
            "t":  [1, 2, 3, 4, 1, 2, 3, 4],
            "x":  [1, 2, 3, 4, 1, 2, 3, 4],
            "y":  [3, 5, 7, 9, 3, 5, 7, 9],
        }
    )

    def result_factory(data):
        return StaticResult()

    out = backtest_forecast(
        result_factory=result_factory,
        data=df,
        y="y",
        entity="id",
        time="t",
        horizon=1,
        min_train_periods=2,
    )

    assert out["rmse"].max() == 0.0


def test_backtest_forecast_explicit_cutoffs():
    df = make_panel()

    def result_factory(data):
        return DynamicResult()

    out = backtest_forecast(
        result_factory=result_factory,
        data=df,
        y="y",
        entity="id",
        time="t",
        horizon=1,
        cutoffs=[3, 4],
    )

    assert out["cutoff"].tolist() == [3, 4]
