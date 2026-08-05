from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from systemgmmkit import DynamicPanelSpec, GMMStyle, IVStyle, build_system_gmm_spec
from systemgmmkit.native_gmm import (
    _build_native_matrices,
    _native_exact_time_lag_pairs,
    _native_level_equation_mask_from_row_meta,
    _native_panel_time_grid,
)


def test_level_equation_mask_consumes_explicit_metadata() -> None:
    row_meta = [
        {"entity": 1, "time": 2, "equation": "diff"},
        {"entity": 1, "time": 4, "equation": "diff"},
        {"entity": 1, "time": 1, "equation": "level"},
        {"entity": 1, "time": 2, "equation": "level"},
        {"entity": 1, "time": 4, "equation": "level"},
    ]

    mask = _native_level_equation_mask_from_row_meta(row_meta, expected_rows=5)

    np.testing.assert_array_equal(mask, np.array([False, False, True, True, True]))


@pytest.mark.parametrize(
    ("row_meta", "message"),
    [
        ([{"equation": "diff"}], "both diff and level"),
        ([{"equation": "diff"}, {"equation": "unknown"}], "row 1"),
    ],
)
def test_level_equation_mask_rejects_ambiguous_metadata(
    row_meta: list[dict[str, object]],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        _native_level_equation_mask_from_row_meta(row_meta, expected_rows=len(row_meta))


def test_exact_time_lag_pairs_skip_entity_gaps() -> None:
    row_meta = [
        {"time": 1},
        {"time": 2},
        {"time": 4},
        {"time": 5},
    ]

    current, previous = _native_exact_time_lag_pairs(
        np.arange(4),
        row_meta,
        [0, 1, 2, 3, 4, 5],
        lag=2,
    )

    # t=4 pairs with t=2.  The adjacent residual at t=5 must not pair with
    # t=2 merely because t=3 is absent.
    np.testing.assert_array_equal(current, np.array([2]))
    np.testing.assert_array_equal(previous, np.array([1]))


def test_exact_time_lag_pairs_respect_globally_absent_integer_period() -> None:
    row_meta = [{"time": 1}, {"time": 3}]

    current, previous = _native_exact_time_lag_pairs(
        np.arange(2),
        row_meta,
        [1, 3],
        lag=1,
    )

    assert current.size == 0
    assert previous.size == 0


def test_integral_time_grid_fails_before_unsafe_expansion() -> None:
    with pytest.raises(ValueError, match="Recode the time variable"):
        _native_panel_time_grid([1, 1_000_001], n_entities=10)


def test_contiguous_time_grid_fails_before_unsafe_panel_reindex() -> None:
    with pytest.raises(ValueError, match="10000000 entity-period rows"):
        _native_panel_time_grid(list(range(1_000)), n_entities=10_000)


def test_other_variable_missingness_does_not_erase_available_lag_source() -> None:
    rows = [
        {
            "id": entity,
            "t": t,
            "y": 100.0 * entity + t + 1.0,
            "x": 10.0 * entity + t + 0.5,
            "w": t + 1.0,
        }
        for entity in range(2)
        for t in range(7)
    ]
    data = pd.DataFrame(rows)
    data.loc[(data["id"] == 0) & (data["t"] == 3), "x"] = np.nan
    spec = build_system_gmm_spec(
        dependent="y",
        regressors=["x", "w"],
        endogenous=["x"],
        exogenous=["w"],
        dependent_lag_limits=(2, 3),
        collapse=True,
    )

    _, _, instruments, _, _, _, instrument_names, row_meta = _build_native_matrices(
        spec,
        data,
        entity="id",
        time="t",
    )

    row = next(
        position
        for position, metadata in enumerate(row_meta)
        if metadata["entity"] == 0 and metadata["time"] == 4 and metadata["equation"] == "diff"
    )
    y_lag_column = instrument_names.index("D:y:L2")

    # y at t=3 remains a usable future instrument even though x at t=3 is
    # missing.  The previous all-variable dropna path incorrectly erased it.
    assert instruments[row, y_lag_column] == pytest.approx(4.0)


@pytest.mark.parametrize("preparation_engine", ["reference", "accelerated"])
def test_inserted_panel_gap_does_not_fabricate_lagged_gmm_source(
    preparation_engine: str,
) -> None:
    rows = [
        {
            "id": entity,
            "t": t,
            "y": 100.0 * entity + t + 1.0,
            "x": 10.0 * entity + t + 0.5,
            "w": t + 1.0,
        }
        for entity in range(2)
        for t in range(8)
        if not (entity == 0 and t == 3)
    ]
    data = pd.DataFrame(rows)
    data.loc[(data["id"] == 1) & (data["t"] == 3), "x"] = np.nan
    spec = DynamicPanelSpec(
        dependent="y",
        regressors=["L1.y", "x", "w"],
        gmm=[
            GMMStyle(variable="L1.y", min_lag=2, max_lag=3),
            GMMStyle(variable="x", min_lag=2, max_lag=3),
        ],
        iv=[IVStyle(variable="w", eq="level")],
        system=True,
        collapse=True,
        transformation="fd",
        steps="twostep",
        name="inserted_gap_contract",
    )

    _, _, instruments, _, _, _, instrument_names, row_meta = _build_native_matrices(
        spec,
        data,
        entity="id",
        time="t",
        preparation_engine=preparation_engine,
    )

    row = next(
        position
        for position, metadata in enumerate(row_meta)
        if metadata["entity"] == 0 and metadata["time"] == 6 and metadata["equation"] == "diff"
    )
    lagged_y_column = instrument_names.index("D:L1.y:L3")

    # L1.y at the physically absent t=3 row must remain missing (and therefore
    # zero in the collapsed instrument matrix).  Lagging after time-grid padding
    # previously fabricated this value from y at t=2.
    assert instruments[row, lagged_y_column] == pytest.approx(0.0)

    observed_row = next(
        position
        for position, metadata in enumerate(row_meta)
        if metadata["entity"] == 1 and metadata["time"] == 6 and metadata["equation"] == "diff"
    )
    # Conversely, t=3 exists for entity 1.  Missing x at that row must not erase
    # the independently available L1.y source, which equals y at t=2.
    assert instruments[observed_row, lagged_y_column] == pytest.approx(103.0)


@pytest.mark.parametrize("preparation_engine", ["reference", "accelerated"])
def test_globally_absent_period_does_not_fabricate_lagged_gmm_source(
    preparation_engine: str,
) -> None:
    data = pd.DataFrame(
        [
            {
                "id": entity,
                "t": t,
                "y": 100.0 * entity + t + 1.0,
                "x": 10.0 * entity + t + 0.5,
                "w": t + 1.0,
            }
            for entity in range(2)
            for t in range(8)
            if t != 3
        ]
    )
    spec = DynamicPanelSpec(
        dependent="y",
        regressors=["L1.y", "x", "w"],
        gmm=[
            GMMStyle(variable="L1.y", min_lag=2, max_lag=3),
            GMMStyle(variable="x", min_lag=2, max_lag=3),
        ],
        iv=[IVStyle(variable="w", eq="level")],
        time_dummies=True,
        system=True,
        collapse=True,
        transformation="fd",
        steps="twostep",
        name="global_gap_contract",
    )

    _, _, instruments, names, _, _, instrument_names, row_meta = _build_native_matrices(
        spec,
        data,
        entity="id",
        time="t",
        preparation_engine=preparation_engine,
    )

    row = next(
        position
        for position, metadata in enumerate(row_meta)
        if metadata["entity"] == 0 and metadata["time"] == 6 and metadata["equation"] == "diff"
    )
    lagged_y_column = instrument_names.index("D:L1.y:L2")

    # At t=6, lag two of the L1.y source targets t=4, whose own first lag is
    # the globally absent t=3 period. Rank-based global time handling previously
    # fabricated that source from y at t=2.
    assert instruments[row, lagged_y_column] == pytest.approx(0.0)
    assert "D:L1.y:L3" not in instrument_names
    assert "t_3" not in names
    assert "T:t_3" not in instrument_names
