from __future__ import annotations

import numpy as np
import pandas as pd
import pytest


def make_dynamic_panel(
    seed: int = 3030,
    n_entities: int = 60,
    n_periods: int = 9,
    unbalanced: bool = False,
    missing_periods: bool = False,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []

    for i in range(n_entities):
        y_prev = rng.normal()

        for t in range(n_periods):
            x = rng.normal()
            w = rng.normal()
            y = 0.50 * y_prev + 0.75 * x - 0.35 * w + 0.20 * i + 0.05 * t + rng.normal(scale=0.5)

            rows.append(
                {
                    "id": i,
                    "t": t,
                    "y": y,
                    "x": x,
                    "w": w,
                }
            )

            y_prev = y

    df = pd.DataFrame(rows)

    if unbalanced:
        keep = np.random.default_rng(seed + 1).random(len(df)) > 0.12
        df = df.loc[keep].copy()

    if missing_periods:
        df = df[~((df["id"] % 7 == 0) & (df["t"].isin([3, 5])))].copy()

    return df.reset_index(drop=True)


def _run_system_gmm(df: pd.DataFrame, *, collapse: bool, min_lag: int, max_lag: int):
    from systemgmmkit import build_system_gmm_spec
    from systemgmmkit.native_gmm import run_native_dynamic_panel_gmm

    spec = build_system_gmm_spec(
        dependent="y",
        regressors=["x", "w"],
        endogenous=["x"],
        exogenous=["w"],
        dependent_lag_limits=(min_lag, max_lag),
        collapse=collapse,
    )

    return run_native_dynamic_panel_gmm(spec, df, entity="id", time="t")


def _assert_basic_system_gmm_result(res):
    assert res is not None
    assert getattr(res, "nobs", 0) > 0
    assert getattr(res, "n_instruments", 0) > 0
    assert getattr(res, "n_instruments", 0) < getattr(res, "nobs", 1)
    assert hasattr(res, "params")
    assert "L1.y" in res.params.index
    assert "x" in res.params.index
    assert res.backend == "native-gmm"


def test_system_gmm_balanced_collapsed_lag_2_3():
    df = make_dynamic_panel()
    res = _run_system_gmm(df, collapse=True, min_lag=2, max_lag=3)
    _assert_basic_system_gmm_result(res)


def test_system_gmm_balanced_uncollapsed_lag_2_3():
    df = make_dynamic_panel()
    res = _run_system_gmm(df, collapse=False, min_lag=2, max_lag=3)
    _assert_basic_system_gmm_result(res)


def test_system_gmm_unbalanced_collapsed_lag_2_3():
    df = make_dynamic_panel(unbalanced=True)

    # The benchmark must contain genuine within-entity gaps, not merely
    # different panel start/end dates.
    observed_deltas = df.sort_values(["id", "t"]).groupby("id")["t"].diff()
    assert (observed_deltas > 1).any()

    res = _run_system_gmm(df, collapse=True, min_lag=2, max_lag=3)
    _assert_basic_system_gmm_result(res)

    # Pin the deterministic native benchmark so changes to gap handling,
    # sample trimming, or instrument construction cannot pass as a smoke test.
    assert res.nobs == 361
    assert res.n_instruments == 13
    assert res.params["L1.y"] == pytest.approx(0.8323129572, abs=1e-8)
    assert res.params["x"] == pytest.approx(-0.5234111149, abs=1e-8)
    assert res.params["w"] == pytest.approx(-0.2565999659, abs=1e-8)
    # Physical gaps must remain missing in lagged GMM sources, and exact-time
    # AR pairing must not treat adjacent residual rows as consecutive periods.
    assert res.ar2_p == pytest.approx(0.5820916844, abs=1e-9)
    assert res.sargan_stat == pytest.approx(res.sargan_j_stat, abs=1e-12)


def test_system_gmm_missing_periods_collapsed_lag_2_3():
    df = make_dynamic_panel(missing_periods=True)
    res = _run_system_gmm(df, collapse=True, min_lag=2, max_lag=3)
    _assert_basic_system_gmm_result(res)
    assert res.sargan_stat == pytest.approx(res.sargan_j_stat, abs=1e-12)


def test_system_gmm_lag_window_variant_2_2():
    df = make_dynamic_panel()
    res = _run_system_gmm(df, collapse=True, min_lag=2, max_lag=2)
    _assert_basic_system_gmm_result(res)


def test_system_gmm_lag_window_variant_2_4():
    df = make_dynamic_panel()
    res = _run_system_gmm(df, collapse=True, min_lag=2, max_lag=4)
    _assert_basic_system_gmm_result(res)


def test_system_gmm_instrument_count_increases_when_uncollapsed():
    df = make_dynamic_panel()

    collapsed = _run_system_gmm(df, collapse=True, min_lag=2, max_lag=3)
    uncollapsed = _run_system_gmm(df, collapse=False, min_lag=2, max_lag=3)

    _assert_basic_system_gmm_result(collapsed)
    _assert_basic_system_gmm_result(uncollapsed)

    assert uncollapsed.n_instruments >= collapsed.n_instruments


def test_system_gmm_larger_lag_window_has_at_least_as_many_instruments():
    df = make_dynamic_panel()

    lag_22 = _run_system_gmm(df, collapse=True, min_lag=2, max_lag=2)
    lag_24 = _run_system_gmm(df, collapse=True, min_lag=2, max_lag=4)

    _assert_basic_system_gmm_result(lag_22)
    _assert_basic_system_gmm_result(lag_24)

    assert lag_24.n_instruments >= lag_22.n_instruments


def test_system_gmm_diagnostics_contract_if_available():
    df = make_dynamic_panel()
    res = _run_system_gmm(df, collapse=True, min_lag=2, max_lag=3)

    _assert_basic_system_gmm_result(res)

    for attr in ["ar1_p", "ar2_p", "hansen_p"]:
        if hasattr(res, attr):
            value = getattr(res, attr)
            assert value is None or 0 <= value <= 1


def test_system_gmm_ar_diagnostics_are_exposed_by_default(monkeypatch):
    monkeypatch.delenv("SYSTEMGMMKIT_REPORT_SYSTEM_AR", raising=False)
    monkeypatch.delenv("SYSTEMGMMKIT_REPORT_EXPERIMENTAL_SYSTEM_AR", raising=False)

    df = make_dynamic_panel()
    res = _run_system_gmm(df, collapse=True, min_lag=2, max_lag=3)

    _assert_basic_system_gmm_result(res)
    assert res.ar1_p is not None
    assert res.ar2_p is not None
    assert 0 <= res.ar1_p <= 1
    assert 0 <= res.ar2_p <= 1


def test_system_gmm_ar_diagnostics_can_be_hidden_for_legacy_parity(monkeypatch):
    monkeypatch.setenv("SYSTEMGMMKIT_REPORT_SYSTEM_AR", "0")

    df = make_dynamic_panel()
    res = _run_system_gmm(df, collapse=True, min_lag=2, max_lag=3)

    _assert_basic_system_gmm_result(res)
    assert res.ar1_p is None
    assert res.ar2_p is None
