from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from systemgmmkit import DynamicPanelSpec, GMMStyle, IVStyle, native_gmm


def _panel(*, n_entities: int = 8, n_periods: int = 9) -> pd.DataFrame:
    rng = np.random.default_rng(20260728)
    rows: list[dict[str, float | int]] = []
    for entity in range(n_entities):
        previous = float(rng.normal())
        for period in range(n_periods):
            x = float(rng.normal())
            w = float(rng.normal())
            y = 0.55 * previous + 0.7 * x - 0.2 * w + float(rng.normal(scale=0.3))
            rows.append({"id": entity, "time": period, "y": y, "x": x, "w": w})
            previous = y
    return pd.DataFrame(rows)


def _spec(*, transformation: str, system: bool) -> DynamicPanelSpec:
    return DynamicPanelSpec(
        dependent="y",
        regressors=["L1.y", "x", "w"],
        gmm=[
            GMMStyle(variable="L1.y", min_lag=2, max_lag=3),
            GMMStyle(variable="x", min_lag=2, max_lag=3),
        ],
        iv=[IVStyle(variable="w", eq="level")],
        time_dummies=False,
        system=system,
        collapse=True,
        transformation=transformation,
        steps="twostep",
        name=f"{transformation}_{'system' if system else 'difference'}",
    )


def _assert_prepared_equal(reference: tuple, accelerated: tuple) -> None:
    np.testing.assert_array_equal(reference[0], accelerated[0])
    np.testing.assert_array_equal(reference[1], accelerated[1])
    np.testing.assert_array_equal(reference[2], accelerated[2])
    assert reference[3] == accelerated[3]
    pd.testing.assert_index_equal(reference[4], accelerated[4], exact=True)
    assert reference[5] == accelerated[5]
    assert reference[6] == accelerated[6]
    assert reference[7] == accelerated[7]


def _prepare(spec: DynamicPanelSpec, data: pd.DataFrame, engine: str) -> tuple:
    return native_gmm._build_native_matrices(
        spec,
        data,
        entity="id",
        time="time",
        preparation_engine=engine,
    )


@pytest.mark.parametrize("transformation", ["fd", "fod"])
@pytest.mark.parametrize("system", [False, True])
@pytest.mark.parametrize("ordered", [True, False])
def test_accelerated_preparation_is_exact_for_balanced_and_unsorted_panels(
    transformation: str,
    system: bool,
    ordered: bool,
) -> None:
    data = _panel()
    if not ordered:
        data = data.sample(frac=1.0, random_state=281).copy()

    reference = _prepare(_spec(transformation=transformation, system=system), data, "reference")
    accelerated = _prepare(_spec(transformation=transformation, system=system), data, "accelerated")

    _assert_prepared_equal(reference, accelerated)


@pytest.mark.parametrize("transformation", ["fd", "fod"])
@pytest.mark.parametrize("system", [False, True])
def test_accelerated_preparation_is_exact_for_gaps_and_short_entities(
    transformation: str,
    system: bool,
) -> None:
    data = _panel()
    data = data.loc[
        ~(
            ((data["id"] == 1) & data["time"].isin([2, 5]))
            | ((data["id"] == 3) & (data["time"] >= 7))
        )
    ].copy()
    singleton = _panel(n_entities=1, n_periods=1).assign(id=99)
    data = pd.concat([data, singleton], ignore_index=True).sample(frac=1.0, random_state=918)

    spec = _spec(transformation=transformation, system=system)
    _assert_prepared_equal(_prepare(spec, data, "reference"), _prepare(spec, data, "accelerated"))


def test_accelerated_preparation_is_exact_for_datetime_time_index() -> None:
    data = _panel()
    data["time"] = pd.Timestamp("2015-01-01") + pd.to_timedelta(data["time"] * 365, unit="D")
    data = data.loc[~((data["id"] == 2) & (data["time"] == data["time"].iloc[4]))]
    spec = _spec(transformation="fd", system=True)

    _assert_prepared_equal(_prepare(spec, data, "reference"), _prepare(spec, data, "accelerated"))


def test_accelerated_preparation_preserves_alternative_fod_lag_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SYSTEMGMMKIT_FOD_LAGGED_REGRESSOR_MODE", "lag_transformed")
    data = _panel()
    spec = _spec(transformation="fod", system=True)

    _assert_prepared_equal(_prepare(spec, data, "reference"), _prepare(spec, data, "accelerated"))


def test_accelerated_preparation_reuses_lagged_sources(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    data = _panel(n_entities=4, n_periods=8)
    spec = _spec(transformation="fd", system=True)
    original = native_gmm._lagged_series
    calls = {"reference": 0, "accelerated": 0}
    active_engine = "reference"

    def tracked(series: pd.Series, lag: int) -> pd.Series:
        calls[active_engine] += 1
        return original(series, lag)

    monkeypatch.setattr(native_gmm, "_lagged_series", tracked)
    _prepare(spec, data, "reference")
    active_engine = "accelerated"
    _prepare(spec, data, "accelerated")

    assert calls["accelerated"] < calls["reference"]
    assert calls["accelerated"] == 4


@pytest.mark.parametrize("transformation", ["fd", "fod"])
@pytest.mark.parametrize("system", [False, True])
def test_accelerated_end_to_end_result_is_bitwise_equal(
    transformation: str,
    system: bool,
) -> None:
    data = _panel(n_entities=12, n_periods=10)
    spec = _spec(transformation=transformation, system=system)

    reference = native_gmm.run_native_dynamic_panel_gmm(
        spec,
        data,
        entity="id",
        time="time",
        windmeijer=True,
        preparation_engine="reference",
    )
    accelerated = native_gmm.run_native_dynamic_panel_gmm(
        spec,
        data,
        entity="id",
        time="time",
        windmeijer=True,
        preparation_engine="accelerated",
    )

    np.testing.assert_array_equal(reference.params.to_numpy(), accelerated.params.to_numpy())
    np.testing.assert_array_equal(
        reference.std_errors.to_numpy(), accelerated.std_errors.to_numpy()
    )
    np.testing.assert_array_equal(reference.residuals.to_numpy(), accelerated.residuals.to_numpy())
    assert reference.instrument_names == accelerated.instrument_names
    assert reference.nobs == accelerated.nobs
    assert reference.n_instruments == accelerated.n_instruments
    assert reference.n_groups == accelerated.n_groups
    assert reference.hansen_j_stat == accelerated.hansen_j_stat
    assert reference.hansen_p == accelerated.hansen_p
    assert reference.sargan_j_stat == accelerated.sargan_j_stat
    assert reference.sargan_p == accelerated.sargan_p
    assert reference.ar1_z == accelerated.ar1_z
    assert reference.ar1_p == accelerated.ar1_p
    assert reference.ar2_z == accelerated.ar2_z
    assert reference.ar2_p == accelerated.ar2_p


def test_reference_remains_the_default_preparation_engine() -> None:
    data = _panel()
    spec = _spec(transformation="fd", system=True)
    default = native_gmm._build_native_matrices(spec, data, entity="id", time="time")
    explicit = _prepare(spec, data, "reference")

    _assert_prepared_equal(default, explicit)


@pytest.mark.parametrize("value", ["auto", "numba", "", 1, None])
def test_preparation_engine_rejects_unsupported_values(value: object) -> None:
    data = _panel()
    spec = _spec(transformation="fd", system=True)
    error = TypeError if not isinstance(value, str) else ValueError

    with pytest.raises(error, match="preparation_engine"):
        native_gmm._build_native_matrices(
            spec,
            data,
            entity="id",
            time="time",
            preparation_engine=value,  # type: ignore[arg-type]
        )


def test_duplicate_entity_time_keys_fail_in_both_engines() -> None:
    data = _panel()
    duplicate = pd.concat([data, data.iloc[[0]]], ignore_index=True)
    spec = _spec(transformation="fd", system=True)

    for engine in ("reference", "accelerated"):
        with pytest.raises(ValueError, match="duplicate"):
            _prepare(spec, duplicate, engine)
