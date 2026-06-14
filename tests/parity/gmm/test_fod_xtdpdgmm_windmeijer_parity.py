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


def _native_summary(*, x_lags: tuple[int, int]) -> pd.DataFrame:
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
        steps="twostep",
        name=f"fod_diff_windmeijer_guard_{x_lags[0]}_{x_lags[1]}",
    )

    res = run_native_dynamic_panel_gmm(
        spec,
        df,
        entity="id",
        time="t",
        windmeijer=True,
    )

    out = pd.DataFrame(
        {
            "term": list(res.params.index),
            "native_coef": res.params.to_numpy(dtype=float),
            "native_std_err": res.std_errors.to_numpy(dtype=float),
        }
    )
    out = out[out["term"] != "_con"].copy()
    out["term_norm"] = out["term"].map(_norm_term)
    return out


def _assert_twostep_windmeijer_matches_stata(
    spec_name: str,
    *,
    x_lags: tuple[int, int],
) -> None:
    stata = pd.read_csv(ORACLE_DIR / f"stata_{spec_name}.csv")
    stata["term_norm"] = stata["term"].map(_norm_term)

    native = _native_summary(x_lags=x_lags)

    merged = stata.merge(native, on="term_norm", how="inner")
    assert merged["term_norm"].nunique() == 3

    merged["coef_abs_diff"] = (
        pd.to_numeric(merged["stata_coef"], errors="coerce")
        - pd.to_numeric(merged["native_coef"], errors="coerce")
    ).abs()

    merged["se_abs_diff"] = (
        pd.to_numeric(merged["stata_std_err"], errors="coerce")
        - pd.to_numeric(merged["native_std_err"], errors="coerce")
    ).abs()

    assert float(merged["coef_abs_diff"].max()) < 1e-5
    assert float(merged["se_abs_diff"].max()) < 1e-2


def test_fod_difference_gmm_endogenous_x_windmeijer_se_near_xtdpdgmm() -> None:
    _assert_twostep_windmeijer_matches_stata(
        "fod_diff_endog_x_twostep",
        x_lags=(1, 2),
    )


def test_fod_difference_gmm_predetermined_x_windmeijer_se_near_xtdpdgmm() -> None:
    _assert_twostep_windmeijer_matches_stata(
        "fod_diff_predet_x_twostep",
        x_lags=(0, 1),
    )
