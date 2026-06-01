import numpy as np
import pandas as pd

from systemgmmkit import (
    FixedEffectsSpec,
    build_fixed_effects_spec,
    build_panel_model_suite,
    run_fixed_effects_native,
)


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
    assert res.backend == "native-lsdv"


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
