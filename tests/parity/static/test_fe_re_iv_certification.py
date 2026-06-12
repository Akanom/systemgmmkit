from __future__ import annotations

import numpy as np
import pandas as pd


def make_static_panel(seed: int = 2026) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []

    for i in range(40):
        alpha = rng.normal()
        for t in range(7):
            tau = 0.15 * t
            z = rng.normal()
            x2 = rng.normal()
            x1 = 0.7 * z + 0.3 * alpha + rng.normal(scale=0.3)
            y = 1.2 * x1 - 0.8 * x2 + alpha + tau + rng.normal(scale=0.2)
            rows.append({"entity": i, "time": t, "y": y, "x1": x1, "x2": x2, "z": z})

    return pd.DataFrame(rows)


def within_transform(df: pd.DataFrame, cols: list[str], entity: str) -> pd.DataFrame:
    return df[cols] - df.groupby(entity)[cols].transform("mean")


def test_fixed_effects_entity_directional_manual_parity():
    from systemgmmkit.fixed_effects import FixedEffectsSpec, run_fixed_effects

    df = make_static_panel()

    spec = FixedEffectsSpec(
        dependent="y",
        regressors=["x1", "x2"],
        entity_effects=True,
        time_effects=False,
    )

    res = run_fixed_effects(spec, df, entity="entity", time="time")

    y_w = within_transform(df, ["y"], "entity")["y"].to_numpy()
    x_w = within_transform(df, ["x1", "x2"], "entity").to_numpy()
    beta = np.linalg.lstsq(x_w, y_w, rcond=None)[0]

    assert abs(res.params["x1"] - beta[0]) < 0.005
    assert abs(res.params["x2"] - beta[1]) < 0.02
    assert res.nobs == len(df)


def test_two_way_fixed_effects_directional_manual_parity():
    from systemgmmkit.fixed_effects import FixedEffectsSpec, run_fixed_effects

    df = make_static_panel()

    spec = FixedEffectsSpec(
        dependent="y",
        regressors=["x1", "x2"],
        entity_effects=True,
        time_effects=True,
    )

    res = run_fixed_effects(spec, df, entity="entity", time="time")

    cols = ["y", "x1", "x2"]
    overall = df[cols].mean()
    entity_mean = df.groupby("entity")[cols].transform("mean")
    time_mean = df.groupby("time")[cols].transform("mean")
    tw = df[cols] - entity_mean - time_mean + overall

    beta = np.linalg.lstsq(tw[["x1", "x2"]].to_numpy(), tw["y"].to_numpy(), rcond=None)[0]

    assert abs(res.params["x1"] - beta[0]) < 0.005
    assert abs(res.params["x2"] - beta[1]) < 0.02
    assert res.nobs == len(df)


def test_random_effects_execution_certification_contract():
    from systemgmmkit.random_effects import RandomEffectsSpec, run_random_effects

    df = make_static_panel()

    spec = RandomEffectsSpec(
        dependent="y",
        regressors=["x1", "x2"],
    )

    res = run_random_effects(spec, df, entity="entity", time="time")

    assert "x1" in res.params
    assert "x2" in res.params
    assert res.nobs == len(df)
    assert getattr(res, "backend", None) is not None


def test_panel_iv_2sls_manual_second_stage_contract():
    from systemgmmkit.panel_iv import PanelIVSpec, run_panel_2sls

    df = make_static_panel()

    spec = PanelIVSpec(
        dependent="y",
        exog=["x2"],
        endogenous=["x1"],
        instruments=["z"],
        entity_effects=False,
        time_effects=False,
    )

    res = run_panel_2sls(spec, df, entity="entity", time="time")

    X1 = np.column_stack([np.ones(len(df)), df[["x2", "z"]].to_numpy()])
    x1_hat = X1 @ np.linalg.lstsq(X1, df["x1"].to_numpy(), rcond=None)[0]

    X2 = np.column_stack([np.ones(len(df)), df["x2"].to_numpy(), x1_hat])
    beta = np.linalg.lstsq(X2, df["y"].to_numpy(), rcond=None)[0]

    assert "x1" in res.params
    assert "x2" in res.params
    assert abs(res.params["x1"] - beta[2]) < 1e-8
    assert abs(res.params["x2"] - beta[1]) < 1e-8
    assert res.nobs == len(df)
