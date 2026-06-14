from __future__ import annotations

from pathlib import Path

import pandas as pd

from systemgmmkit import DynamicPanelSpec, GMMStyle, IVStyle
from systemgmmkit.native_gmm import run_native_dynamic_panel_gmm


DATA = Path("artifacts/parity/xtabond2/system_gmm_benchmark.csv")
ORACLE_DIR = Path("artifacts/parity/xtdpdgmm/fod_diff")


def _norm_term(x: object) -> str:
    s = str(x).strip()
    return {"L.y": "L1.y", "l1.y": "L1.y"}.get(s, s)


def _native_params(*, x_lags: tuple[int, int], steps: str) -> pd.DataFrame:
    df = pd.read_csv(DATA).sort_values(["id", "t"]).reset_index(drop=True)

    spec = DynamicPanelSpec(
        dependent="y",
        regressors=["L1.y", "x", "w"],
        gmm=[
            GMMStyle(variable="y", min_lag=1, max_lag=2),
            GMMStyle(variable="x", min_lag=x_lags[0], max_lag=x_lags[1]),
        ],
        iv=[
            IVStyle(variable="w", eq="diff"),
        ],
        time_dummies=False,
        system=False,
        collapse=True,
        transformation="fod",
        steps=steps,
        name=f"fod_diff_coef_guard_{steps}_{x_lags[0]}_{x_lags[1]}",
    )

    res = run_native_dynamic_panel_gmm(
        spec,
        df,
        entity="id",
        time="t",
        windmeijer=False,
    )

    out = pd.DataFrame(
        {
            "term": list(res.params.index),
            "native_coef": res.params.to_numpy(dtype=float),
        }
    )
    out = out[out["term"] != "_con"].copy()
    out["term_norm"] = out["term"].map(_norm_term)
    return out


def _assert_matches_stata(spec_name: str, *, x_lags: tuple[int, int], steps: str) -> None:
    stata = pd.read_csv(ORACLE_DIR / f"stata_{spec_name}.csv")
    stata["term_norm"] = stata["term"].map(_norm_term)

    native = _native_params(x_lags=x_lags, steps=steps)

    merged = stata.merge(native, on="term_norm", how="inner")
    assert merged["term_norm"].nunique() == 3

    merged["abs_diff"] = (
        pd.to_numeric(merged["stata_coef"], errors="coerce")
        - pd.to_numeric(merged["native_coef"], errors="coerce")
    ).abs()

    assert float(merged["abs_diff"].max()) < 1e-5


def test_fod_difference_gmm_endogenous_x_coefficients_match_xtdpdgmm() -> None:
    _assert_matches_stata(
        "fod_diff_endog_x_onestep",
        x_lags=(1, 2),
        steps="onestep",
    )
    _assert_matches_stata(
        "fod_diff_endog_x_twostep",
        x_lags=(1, 2),
        steps="twostep",
    )


def test_fod_difference_gmm_predetermined_x_coefficients_match_xtdpdgmm() -> None:
    _assert_matches_stata(
        "fod_diff_predet_x_onestep",
        x_lags=(0, 1),
        steps="onestep",
    )
    _assert_matches_stata(
        "fod_diff_predet_x_twostep",
        x_lags=(0, 1),
        steps="twostep",
    )
