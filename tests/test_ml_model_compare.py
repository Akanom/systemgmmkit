import numpy as np
import pandas as pd

from systemgmmkit import OLSSpec, run_ols
from systemgmmkit.ml import compare_models


class GoodResult:
    params = pd.Series({"x": 2.0, "_con": 1.0})
    diagnostics = {
        "hansen_p": 0.25,
        "ar2_p": 0.40,
        "n_instruments": 8,
    }


class WorseResult:
    params = pd.Series({"x": 1.0, "_con": 0.0})
    diagnostics = {
        "hansen_p": 0.10,
        "ar2_p": 0.20,
        "n_instruments": 12,
    }


class BadResult:
    params = pd.Series({"missing_column": 1.0})


def test_compare_models_orders_by_rmse_and_includes_diagnostics():
    df = pd.DataFrame({
        "y": [3.0, 5.0, 7.0],
        "x": [1.0, 2.0, 3.0],
    })

    table = compare_models(
        {
            "Worse": WorseResult(),
            "Good": GoodResult(),
        },
        df,
        y="y",
    )

    assert table.iloc[0]["model"] == "Good"
    assert "rmse" in table.columns
    assert "diag_hansen_p" in table.columns
    assert "diag_ar2_p" in table.columns
    assert "diag_n_instruments" in table.columns


def test_compare_models_keeps_failed_model_when_raise_on_error_false():
    df = pd.DataFrame({
        "y": [1.0, 2.0, 3.0],
        "x": [1.0, 2.0, 3.0],
    })

    table = compare_models(
        {
            "Good": GoodResult(),
            "Bad": BadResult(),
        },
        df,
        y="y",
    )

    bad = table.loc[table["model"] == "Bad"].iloc[0]
    assert "KeyError" in bad["error"]


def test_compare_models_with_real_ols_results():
    n = 40
    x = np.linspace(1.0, 10.0, n)
    z = np.linspace(2.0, 6.0, n)
    y = 1.0 + 2.0 * x - 0.5 * z

    df = pd.DataFrame({"y": y, "x": x, "z": z})

    spec_full = OLSSpec(
        dependent="y",
        regressors=["x", "z"],
        covariance="robust",
    )
    spec_short = OLSSpec(
        dependent="y",
        regressors=["x"],
        covariance="robust",
    )

    res_full = run_ols(spec_full, df)
    res_short = run_ols(spec_short, df)

    table = compare_models(
        {
            "OLS full": res_full,
            "OLS short": res_short,
        },
        df,
        y="y",
    )

    assert len(table) == 2
    assert "rmse" in table.columns
    assert table["error"].fillna("").eq("").all()
    assert np.isfinite(table["rmse"]).all()
