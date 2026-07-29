import numpy as np
import pandas as pd

from systemgmmkit import (
    FixedEffectsSpec,
    build_fixed_effects_spec,
    build_panel_model_suite,
    run_fixed_effects_native,
)
from systemgmmkit.fixed_effects import _build_lsdv_design


def test_fixed_effects_native_recovers_simple_slope_with_entity_and_time_effects():
    rows = []
    for i in range(8):
        for t in range(5):
            x = i * 0.3 + t * 0.7 + ((i + t) % 3) * 0.2
            y = 2.5 * x + i * 1.1 + t * -0.4
            rows.append({"id": i, "t": t, "y": y, "x": x})

    df = pd.DataFrame(rows)

    spec = FixedEffectsSpec(
        dependent="y",
        regressors=["x"],
        entity_effects=True,
        time_effects=True,
    )

    res = run_fixed_effects_native(spec, df, entity="id", time="t")

    assert np.isclose(res.params["x"], 2.5, atol=1e-8)
    assert res.nobs == len(df)
    assert res.backend == "native-within"


def test_fixed_effects_native_uses_compact_within_backend_for_many_entities():
    rows = []
    rng = np.random.default_rng(20260718)
    for i in range(250):
        alpha = rng.normal()
        for t in range(8):
            tau = 0.2 * t
            x1 = rng.normal() + 0.1 * alpha
            x2 = rng.normal() - 0.05 * t
            y = 1.4 * x1 - 0.6 * x2 + alpha + tau + rng.normal(scale=0.05)
            rows.append({"id": i, "t": t, "y": y, "x1": x1, "x2": x2})

    df = pd.DataFrame(rows)
    spec = FixedEffectsSpec(
        dependent="y",
        regressors=["x1", "x2"],
        entity_effects=True,
        time_effects=True,
    )

    res = run_fixed_effects_native(spec, df, entity="id", time="t")

    assert res.backend == "native-within"
    assert list(res.params.index) == ["const", "x1", "x2"]
    assert abs(res.params["x1"] - 1.4) < 0.01
    assert abs(res.params["x2"] + 0.6) < 0.01
    assert res.rank <= df["id"].nunique() + df["t"].nunique() + 2


def test_fixed_effects_native_matches_lsdv_slopes_on_unbalanced_two_way_panel():
    rows = []
    rng = np.random.default_rng(20260719)
    for i in range(20):
        alpha = rng.normal()
        for t in range(6):
            if (i + 2 * t) % 7 == 0:
                continue
            tau = -0.1 * t
            x1 = rng.normal() + 0.2 * alpha
            x2 = rng.normal() + 0.1 * t
            y = 0.9 * x1 + 0.4 * x2 + alpha + tau + rng.normal(scale=0.02)
            rows.append({"id": i, "t": t, "y": y, "x1": x1, "x2": x2})

    df = pd.DataFrame(rows)
    spec = FixedEffectsSpec(
        dependent="y",
        regressors=["x1", "x2"],
        entity_effects=True,
        time_effects=True,
    )

    res = run_fixed_effects_native(spec, df, entity="id", time="t")
    y_lsdv, x_lsdv, _, _ = _build_lsdv_design(df, entity="id", time="t", spec=spec)
    beta_lsdv, *_ = np.linalg.lstsq(
        x_lsdv.to_numpy(dtype=float),
        y_lsdv.to_numpy(dtype=float),
        rcond=None,
    )
    lsdv_params = pd.Series(beta_lsdv, index=x_lsdv.columns)

    assert np.allclose(
        res.params[["x1", "x2"]].to_numpy(dtype=float),
        lsdv_params[["x1", "x2"]].to_numpy(dtype=float),
        atol=1e-8,
    )


def test_generic_fixed_effects_builder_excludes_dynamic_lag_by_default():
    spec = build_fixed_effects_spec(
        dependent="y",
        regressors=["x1", "x2"],
        controls=["control"],
        interactions=["x1_x2"],
        entity_effects=True,
        time_effects=True,
    )

    assert "L1.y" not in spec.regressors
    assert spec.regressors == ["x1", "x2", "control", "x1_x2"]
    assert spec.entity_effects is True
    assert spec.time_effects is True


def test_generic_suite_pairs_fe_with_dynamic_gmm():
    suite = build_panel_model_suite(
        name="investment_model",
        dependent="investment",
        regressors=["q", "cashflow"],
        controls=["size"],
        endogenous=["q"],
        predetermined=["cashflow"],
        exogenous=["size"],
        system=True,
    )

    assert suite.name == "investment_model"
    assert suite.fixed_effects.dependent == "investment"
    assert suite.dynamic_gmm.dependent == "investment"
    assert suite.dynamic_gmm.system is True
