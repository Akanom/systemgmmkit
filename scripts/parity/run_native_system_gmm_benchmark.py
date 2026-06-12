from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

from systemgmmkit import DynamicPanelSpec, GMMStyle, IVStyle
from systemgmmkit.native_gmm import run_native_dynamic_panel_gmm


OUT = Path("artifacts/parity/xtabond2")
DATA = OUT / "system_gmm_benchmark.csv"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(DATA)

    spec = DynamicPanelSpec(
        dependent="y",
        regressors=["L1.y", "x", "w"],
        gmm=[
            GMMStyle(variable="y", min_lag=2, max_lag=3),
            GMMStyle(variable="x", min_lag=2, max_lag=3),
        ],
        iv=[
            IVStyle(variable="w"),
        ],
        time_dummies=False,
        system=True,
        collapse=True,
        transformation="fod",
        steps="twostep",
        name="system_gmm_baseline_controls",
    )

    res = run_native_dynamic_panel_gmm(spec, df, entity="id", time="t")

    params = pd.DataFrame(
        {
            "param": list(res.params.index),
            "native_coef": res.params.to_numpy(dtype=float),
            "native_std_err": res.std_errors.reindex(res.params.index).to_numpy(dtype=float),
            "native_z": res.zstats.reindex(res.params.index).to_numpy(dtype=float),
            "native_p_value": res.pvalues.reindex(res.params.index).to_numpy(dtype=float),
        }
    )

    if os.getenv("SYSTEMGMMKIT_DROP_NATIVE_CON_FOR_PARITY") == "1":
        params = params[params["param"] != "_con"].copy()

    params.to_csv(OUT / "native_system_gmm_params.csv", index=False)

    diagnostics = pd.DataFrame(
        [
            {
                "spec": "system_gmm_baseline_controls",
                "native_nobs": getattr(res, "nobs", None),
                "native_n_instruments": getattr(res, "n_instruments", None),
                "native_backend": getattr(res, "backend", None),
                "native_covariance_type": getattr(res, "covariance_type", None),
                "native_instrument_names": ";".join(getattr(res, "instrument_names", []) or []),
                "native_hansen_p": getattr(res, "hansen_p", None),
                "native_ar1_p": getattr(res, "ar1_p", None),
                "native_ar2_p": getattr(res, "ar2_p", None),
                "native_j_stat": getattr(res, "j_stat", None),
                "native_has_constant_param": "_con" in list(res.params.index),
            }
        ]
    )
    diagnostics.to_csv(OUT / "native_system_gmm_diagnostics.csv", index=False)

    print("Wrote native System GMM benchmark outputs")


if __name__ == "__main__":
    main()
