import numpy as np
import pandas as pd

from systemgmmkit import OLSSpec, run_ols
from systemgmmkit.ml import (
    GMMGridSearch,
    PanelTimeSeriesSplit,
    cross_validate_panel,
    fitted_values,
    predict,
    residuals,
)


def make_ols_data():
    n = 40
    x = np.linspace(1.0, 10.0, n)
    z = np.linspace(2.0, 6.0, n)
    y = 1.0 + 2.0 * x - 0.5 * z
    return pd.DataFrame({"y": y, "x": x, "z": z})


def test_ml_predict_works_with_real_ols_result():
    df = make_ols_data()

    spec = OLSSpec(
        dependent="y",
        regressors=["x", "z"],
        covariance="robust",
    )

    result = run_ols(spec, df)

    pred = predict(result, df)
    fit = fitted_values(result, df)
    err = residuals(result, df, y="y")

    assert len(pred) == len(df)
    assert len(fit) == len(df)
    assert len(err) == len(df)
    assert np.isfinite(pred).all()
    assert np.isfinite(fit).all()
    assert np.isfinite(err).all()


class SystemGMMKitLikeResult:
    def __init__(self):
        self.params = pd.Series({"x": 2.0, "w": -1.0, "_con": 0.5})
        self.diagnostics = {
            "hansen_p": 0.25,
            "ar2_p": 0.40,
            "n_instruments": 8,
        }


def test_cross_validate_panel_with_systemgmmkit_like_result():
    df = pd.DataFrame({
        "id": [1, 1, 1, 1, 2, 2, 2, 2],
        "t":  [1, 2, 3, 4, 1, 2, 3, 4],
        "y":  [2, 4, 6, 8, 3, 5, 7, 9],
        "x":  [1, 2, 3, 4, 1, 2, 3, 4],
        "w":  [0, 0, 0, 0, 1, 1, 1, 1],
    })

    def estimator(data):
        return SystemGMMKitLikeResult()

    scores = cross_validate_panel(
        estimator=estimator,
        data=df,
        y="y",
        time="t",
        cv=PanelTimeSeriesSplit(n_splits=2, min_train_periods=2, test_periods=1),
    )

    assert len(scores) == 2
    assert "rmse" in scores.columns
    assert scores["test_n"].min() > 0


def test_gmm_grid_search_scaffold():
    df = pd.DataFrame({
        "id": [1, 1, 1, 1, 2, 2, 2, 2],
        "t":  [1, 2, 3, 4, 1, 2, 3, 4],
        "y":  [2, 4, 6, 8, 3, 5, 7, 9],
        "x":  [1, 2, 3, 4, 1, 2, 3, 4],
        "w":  [0, 0, 0, 0, 1, 1, 1, 1],
    })

    def build_spec(**kwargs):
        return kwargs

    def run_model(spec, data, *, entity, time):
        return SystemGMMKitLikeResult()

    search = GMMGridSearch(
        build_spec=build_spec,
        run_model=run_model,
        param_grid=[
            {"lag_window": (2, 2), "collapse": True},
            {"lag_window": (2, 3), "collapse": True},
        ],
        y="y",
        entity="id",
        time="t",
        diagnostic_rules={
            "hansen_p": (">", 0.05),
            "ar2_p": (">", 0.05),
        },
        test_size=1,
    )

    result = search.fit(df)

    assert len(result.results) == 2
    assert result.best_result is not None
    assert result.best_spec is not None
    assert result.results["passes_diagnostics"].all()
