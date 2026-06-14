from __future__ import annotations

from pathlib import Path

import pandas as pd

from systemgmmkit import DynamicPanelSpec, GMMStyle, IVStyle
from systemgmmkit.native_gmm import run_native_dynamic_panel_gmm


DATA = Path("artifacts/parity/xtabond2/system_gmm_benchmark.csv")


def test_fod_difference_gmm_native_keeps_xtdpdgmm_transformed_rows() -> None:
    df = pd.read_csv(DATA).sort_values(["id", "t"]).reset_index(drop=True)

    spec = DynamicPanelSpec(
        dependent="y",
        regressors=["L1.y", "x", "w"],
        gmm=[
            GMMStyle(variable="y", min_lag=1, max_lag=2),
            GMMStyle(variable="x", min_lag=0, max_lag=1),
        ],
        iv=[
            IVStyle(variable="w", eq="diff"),
        ],
        time_dummies=False,
        system=False,
        collapse=True,
        transformation="fod",
        steps="onestep",
        name="fod_diff_predet_x_onestep_sample_guard",
    )

    res = run_native_dynamic_panel_gmm(
        spec,
        df,
        entity="id",
        time="t",
        windmeijer=False,
    )

    # Effective native transformed-equation rows:
    # 96 groups × 12 usable rows.
    #
    # xtdpdgmm reports e(N)=1248 for the marked sample, but with regressors
    # [L1.y, x, w], the first FOD row has no observable transformed L1.y.
    # Native therefore correctly estimates on the effective transformed design
    # matrix with 1152 rows.
    assert res.nobs == 1152
