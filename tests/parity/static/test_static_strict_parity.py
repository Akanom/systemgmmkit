from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm


def make_panel(seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    for i in range(30):
        alpha = rng.normal()
        for t in range(6):
            x1 = rng.normal()
            x2 = rng.normal()
            y = 1.0 + 1.5 * x1 - 0.7 * x2 + alpha + rng.normal(scale=0.2)
            rows.append({"entity": i, "time": t, "y": y, "x1": x1, "x2": x2})
    return pd.DataFrame(rows)


def test_pooled_ols_strict_manual_statsmodels_parity():
    df = make_panel()

    X = sm.add_constant(df[["x1", "x2"]])
    ref = sm.OLS(df["y"], X).fit()

    beta = np.linalg.lstsq(X.to_numpy(), df["y"].to_numpy(), rcond=None)[0]

    assert abs(beta[0] - ref.params["const"]) < 1e-10
    assert abs(beta[1] - ref.params["x1"]) < 1e-10
    assert abs(beta[2] - ref.params["x2"]) < 1e-10


def test_first_difference_strict_manual_parity():
    from systemgmmkit import first_difference

    df = make_panel()

    res = first_difference(df, y="y", x=["x1", "x2"], entity="entity", time="time")

    d = df.sort_values(["entity", "time"]).copy()
    d[["dy", "dx1", "dx2"]] = d.groupby("entity")[["y", "x1", "x2"]].diff()
    d = d.dropna()

    beta = np.linalg.lstsq(d[["dx1", "dx2"]].to_numpy(), d["dy"].to_numpy(), rcond=None)[0]

    assert abs(res.params["x1"] - beta[0]) < 1e-10
    assert abs(res.params["x2"] - beta[1]) < 1e-10
