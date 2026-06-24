import numpy as np
import pandas as pd

from systemgmmkit.ml import (
    PanelTimeSeriesSplit,
    panel_train_test_split,
    predict,
    regression_metrics,
    residuals,
)


class DummyResult:
    params = pd.Series({"x": 2.0, "_con": 1.0})


def test_predict_linear_with_constant():
    df = pd.DataFrame({"x": [1.0, 2.0, 3.0]})
    pred = predict(DummyResult(), df)
    assert pred.tolist() == [3.0, 5.0, 7.0]


def test_residuals_from_data():
    df = pd.DataFrame({"y": [3.0, 5.0, 8.0], "x": [1.0, 2.0, 3.0]})
    res = residuals(DummyResult(), df, y="y")
    assert res.tolist() == [0.0, 0.0, 1.0]


def test_regression_metrics():
    m = regression_metrics([1, 2, 3], [1, 2, 4])
    assert m["n"] == 3.0
    assert m["mae"] > 0
    assert "rmse" in m
    assert "r2" in m


def test_panel_train_test_split():
    df = pd.DataFrame({
        "id": [1, 1, 1, 2, 2, 2],
        "t": [1, 2, 3, 1, 2, 3],
        "y": [1, 2, 3, 2, 3, 4],
    })
    train, test = panel_train_test_split(df, time="t", test_size=1)
    assert set(train["t"]) == {1, 2}
    assert set(test["t"]) == {3}


def test_panel_time_series_split():
    df = pd.DataFrame({
        "id": np.repeat([1, 2], 5),
        "t": list(range(1, 6)) * 2,
        "y": np.arange(10),
    })
    cv = PanelTimeSeriesSplit(n_splits=2, min_train_periods=2, test_periods=1)
    splits = list(cv.split(df, time="t"))
    assert len(splits) == 2
    assert all(len(train) > 0 and len(test) > 0 for train, test in splits)
