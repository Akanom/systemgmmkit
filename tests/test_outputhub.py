from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from systemgmmkit import (
    DynamicPanelSpec,
    FixedEffectsSpec,
    NativeGMMResult,
    OLSSpec,
    PanelIVSpec,
    RandomEffectsSpec,
    add_to_outputhub,
    first_difference,
    outputhub_diagnostics_frame,
    run_fixed_effects,
    run_ols,
    run_panel_2sls,
    run_random_effects,
    to_outputhub_model,
)

outputhub = pytest.importorskip("universal_output_hub")


def _pooled_result():
    rng = np.random.default_rng(481)
    data = pd.DataFrame({"y": rng.normal(size=80), "x": rng.normal(size=80)})
    return run_ols(OLSSpec(dependent="y", regressors=["x"], name="pooled_demo"), data)


def _gmm_result() -> NativeGMMResult:
    names = pd.Index(["L1.y", "x"])
    return NativeGMMResult(
        spec=DynamicPanelSpec(
            dependent="y",
            regressors=list(names),
            system=True,
            name="system_demo",
        ),
        nobs=120,
        n_instruments=8,
        params=pd.Series([0.4, 0.7], index=names),
        std_errors=pd.Series([0.1, 0.2], index=names),
        zstats=pd.Series([4.0, 3.5], index=names),
        pvalues=pd.Series([0.001, 0.002], index=names),
        residuals=pd.Series([0.1, -0.1]),
        covariance_type="robust-clustered-two-step-windmeijer",
        backend="native-gmm",
        notes=[],
        n_groups=30,
        hansen_p=0.41,
        sargan_p=0.22,
        ar1_p=0.01,
        ar2_p=0.63,
        overid_df=6,
    )


def _panel_data() -> pd.DataFrame:
    rng = np.random.default_rng(904)
    entity = np.repeat(np.arange(20), 6)
    time = np.tile(np.arange(6), 20)
    z = rng.normal(size=len(entity))
    x1 = 0.8 * z + rng.normal(scale=0.4, size=len(entity))
    x2 = rng.normal(size=len(entity))
    effects = np.repeat(rng.normal(scale=0.5, size=20), 6)
    y = 0.7 * x1 - 0.3 * x2 + effects + rng.normal(scale=0.2, size=len(entity))
    return pd.DataFrame({"entity": entity, "time": time, "y": y, "x1": x1, "x2": x2, "z": z})


def test_outputhub_model_maps_pooled_result_contract():
    result = _pooled_result()
    model = to_outputhub_model(result, name="Pooled model")

    assert model.name == "Pooled model"
    assert model.depvar == "y"
    assert model.source == "systemgmmkit"
    assert model.metadata["estimator"] == "pooled_ols"
    assert model.statistics["N"] == result.nobs
    pd.testing.assert_series_equal(model.params, result.params.rename("coef"))
    pd.testing.assert_series_equal(model.std_errors, result.std_errors.rename("se"))
    pd.testing.assert_series_equal(model.pvalues, result.pvalues.rename("pvalue"))


def test_add_gmm_result_attaches_model_and_diagnostics_table():
    result = _gmm_result()
    hub = outputhub.OutputHub("Dynamic-panel report")
    model = add_to_outputhub(hub, result, include_diagnostics=True)

    assert hub.models == [model]
    assert model.metadata["estimator"] == "system_gmm"
    assert model.statistics["Entities"] == 30
    assert model.statistics["Instruments"] == 8
    assert model.diagnostics["Hansen p"] == 0.41
    assert len(hub.tables) == 1
    assert hub.tables[0].name == "System Demo diagnostics"
    assert set(hub.tables[0].data["diagnostic"]) >= {
        "Hansen p",
        "Sargan p",
        "AR(1) p",
        "AR(2) p",
    }


def test_outputhub_models_cover_static_panel_result_families():
    data = _panel_data()
    results = [
        run_fixed_effects(
            FixedEffectsSpec(
                dependent="y",
                regressors=["x1", "x2"],
                time_effects=False,
                covariance="robust",
            ),
            data,
            entity="entity",
            time="time",
        ),
        run_random_effects(
            RandomEffectsSpec(dependent="y", regressors=["x1", "x2"]),
            data,
            entity="entity",
            time="time",
        ),
        run_panel_2sls(
            PanelIVSpec(
                dependent="y",
                exog=["x2"],
                endogenous=["x1"],
                instruments=["z"],
            ),
            data,
            entity="entity",
            time="time",
        ),
    ]
    expected_estimators = ["fixed_effects", "random_effects", "panel_iv_2sls"]

    models = [to_outputhub_model(result) for result in results]

    assert [model.metadata["estimator"] for model in models] == expected_estimators
    assert all(model.depvar == "y" for model in models)
    assert models[1].statistics["Entities"] == 20
    assert "First-stage R-squared (x1)" in models[2].diagnostics


def test_outputhub_diagnostics_frame_is_empty_for_plain_ols():
    frame = outputhub_diagnostics_frame(_pooled_result())
    assert list(frame.columns) == ["diagnostic", "value"]
    assert frame.empty


def test_outputhub_model_supports_first_difference_result_aliases():
    data = pd.DataFrame(
        {
            "entity": np.repeat(np.arange(12), 5),
            "time": np.tile(np.arange(5), 12),
            "x": np.tile(np.arange(5, dtype=float), 12),
        }
    )
    data["y"] = 1.5 * data["x"] + np.repeat(np.arange(12), 5)
    result = first_difference(data, y="y", x=["x"], entity="entity", time="time")
    model = to_outputhub_model(result)

    assert model.depvar == "y"
    assert model.metadata["estimator"] == "first_difference_ols"
    assert model.statistics["N"] == result.nobs
    assert model.params.index.tolist() == ["x"]


def test_outputhub_adapter_rejects_incompatible_objects():
    with pytest.raises(TypeError, match="must expose params"):
        to_outputhub_model(object())

    with pytest.raises(TypeError, match="add_model"):
        add_to_outputhub(object(), _pooled_result())
