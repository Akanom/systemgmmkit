from __future__ import annotations

from typing import Any, Callable

import numpy as np
import pandas as pd
import pytest

from systemgmmkit import (
    FixedEffectsSpec,
    PanelIVSpec,
    run_fixed_effects_native,
    run_panel_2sls,
)
from systemgmmkit.fixed_effects import _build_lsdv_design
from systemgmmkit.panel_iv import _designs


def _panel(seed: int = 20260728) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows: list[dict[str, float | int]] = []
    for entity in range(24):
        alpha = float(rng.normal(scale=0.6))
        for period in range(7):
            x1 = float(rng.normal())
            x2 = float(rng.normal())
            instrument = float(rng.normal())
            endogenous = 0.7 * instrument + 0.25 * alpha + float(rng.normal(scale=0.4))
            y = (
                1.0
                + 0.8 * x1
                - 0.35 * x2
                + 1.2 * endogenous
                + alpha
                + 0.1 * period
                + float(rng.normal(scale=0.25))
            )
            rows.append(
                {
                    "entity": entity,
                    "time": period,
                    "y": y,
                    "x1": x1,
                    "x2": x2,
                    "x_duplicate": 2.0 * x1,
                    "endogenous": endogenous,
                    "instrument": instrument,
                }
            )
    data = pd.DataFrame(rows)
    data.loc[data.index[13], "x2"] = np.nan
    data = data.drop(index=[26, 74, 119]).sample(frac=1.0, random_state=2718)
    return data


def _assert_common_result_identity(reference: Any, accelerated: Any) -> None:
    for name in ("params", "std_errors", "pvalues", "residuals", "fitted_values"):
        pd.testing.assert_series_equal(getattr(reference, name), getattr(accelerated, name))
    for name in ("nobs", "rank", "df_resid", "covariance_type", "backend", "notes"):
        assert getattr(reference, name) == getattr(accelerated, name)


def test_fixed_effects_prepared_designs_are_exactly_equal() -> None:
    data = _panel()
    spec = FixedEffectsSpec("y", ["x1", "x2"], entity_effects=True, time_effects=True)

    reference = _build_lsdv_design(
        data,
        entity="entity",
        time="time",
        spec=spec,
        preparation_engine="reference",
    )
    accelerated = _build_lsdv_design(
        data,
        entity="entity",
        time="time",
        spec=spec,
        preparation_engine="accelerated",
    )

    pd.testing.assert_series_equal(reference[0], accelerated[0])
    pd.testing.assert_frame_equal(reference[1], accelerated[1])
    pd.testing.assert_frame_equal(reference[2], accelerated[2])
    assert reference[3] == accelerated[3]


def test_fixed_effects_engines_return_identical_results() -> None:
    data = _panel()
    spec = FixedEffectsSpec("y", ["x1", "x2"], entity_effects=True, time_effects=True)

    reference = run_fixed_effects_native(
        spec, data, entity="entity", time="time", preparation_engine="reference"
    )
    accelerated = run_fixed_effects_native(
        spec, data, entity="entity", time="time", preparation_engine="accelerated"
    )

    _assert_common_result_identity(reference, accelerated)
    pd.testing.assert_series_equal(reference.tstats, accelerated.tstats)


def test_collinear_fixed_effects_design_falls_back_to_reference_selection() -> None:
    data = _panel()
    spec = FixedEffectsSpec(
        "y", ["x1", "x_duplicate", "x2"], entity_effects=True, time_effects=True
    )

    reference = run_fixed_effects_native(
        spec, data, entity="entity", time="time", preparation_engine="reference"
    )
    accelerated = run_fixed_effects_native(
        spec, data, entity="entity", time="time", preparation_engine="accelerated"
    )

    _assert_common_result_identity(reference, accelerated)
    assert "x_duplicate" not in accelerated.params
    assert any("x_duplicate" in note for note in accelerated.notes)


def test_panel_iv_prepared_designs_are_exactly_equal() -> None:
    data = _panel()
    spec = PanelIVSpec(
        "y",
        exog=["x1", "x2"],
        endogenous=["endogenous"],
        instruments=["instrument"],
        entity_effects=True,
        time_effects=True,
    )

    reference = _designs(
        spec,
        data,
        entity="entity",
        time="time",
        preparation_engine="reference",
    )
    accelerated = _designs(
        spec,
        data,
        entity="entity",
        time="time",
        preparation_engine="accelerated",
    )

    for left, right in zip(reference[:4], accelerated[:4]):
        if isinstance(left, pd.Series):
            pd.testing.assert_series_equal(left, right)
        else:
            pd.testing.assert_frame_equal(left, right)
    assert reference[4] == accelerated[4]


def test_panel_iv_engines_return_identical_results() -> None:
    data = _panel()
    spec = PanelIVSpec(
        "y",
        exog=["x1", "x2"],
        endogenous=["endogenous"],
        instruments=["instrument"],
        entity_effects=True,
        time_effects=True,
    )

    reference = run_panel_2sls(
        spec, data, entity="entity", time="time", preparation_engine="reference"
    )
    accelerated = run_panel_2sls(
        spec, data, entity="entity", time="time", preparation_engine="accelerated"
    )

    _assert_common_result_identity(reference, accelerated)
    pd.testing.assert_series_equal(reference.zstats, accelerated.zstats)
    assert reference.first_stage_r2 == accelerated.first_stage_r2


def test_collinear_panel_iv_design_falls_back_to_reference_selection() -> None:
    data = _panel()
    spec = PanelIVSpec(
        "y",
        exog=["x1", "x_duplicate", "x2"],
        endogenous=["endogenous"],
        instruments=["instrument"],
        entity_effects=True,
        time_effects=True,
    )

    reference = run_panel_2sls(
        spec, data, entity="entity", time="time", preparation_engine="reference"
    )
    accelerated = run_panel_2sls(
        spec, data, entity="entity", time="time", preparation_engine="accelerated"
    )

    _assert_common_result_identity(reference, accelerated)
    assert "x_duplicate" not in accelerated.params
    assert any("x_duplicate" in note for note in accelerated.notes)


@pytest.mark.parametrize(
    "runner,spec",
    [
        (
            run_fixed_effects_native,
            FixedEffectsSpec("y", ["x1"], entity_effects=True, time_effects=False),
        ),
        (
            run_panel_2sls,
            PanelIVSpec("y", exog=["x1"], endogenous=["endogenous"], instruments=["instrument"]),
        ),
    ],
)
@pytest.mark.parametrize(
    "value,error",
    [("unsupported", ValueError), (None, TypeError)],
)
def test_static_preparation_engine_rejects_unsupported_values(
    runner: Callable[..., Any], spec: Any, value: object, error: type[Exception]
) -> None:
    with pytest.raises(error, match="preparation_engine"):
        runner(
            spec,
            _panel(),
            entity="entity",
            time="time",
            preparation_engine=value,
        )
