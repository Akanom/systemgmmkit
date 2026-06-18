from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

from systemgmmkit import DynamicPanelSpec, GMMStyle, IVStyle
from systemgmmkit.native_gmm import run_native_dynamic_panel_gmm

OUT = Path("artifacts/parity/xtabond2/specs/system_gmm_three_way_controls")
DATA = OUT / "system_gmm_three_way_controls_benchmark.csv"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    if not DATA.exists():
        raise FileNotFoundError(
            f"Missing benchmark data: {DATA}. "
            "Run scripts/parity/build_xtabond2_system_gmm_three_way_controls_do.py first."
        )

    df = pd.read_csv(DATA)

    spec = DynamicPanelSpec(
        dependent="y",
        regressors=[
            "L1.y",
            "x",
            "frag",
            "polity",
            "x_frag",
            "x_polity",
            "frag_polity",
            "x_frag_polity",
            "w",
        ],
        gmm=[
            GMMStyle(variable="y", min_lag=2, max_lag=3),
            GMMStyle(variable="x", min_lag=2, max_lag=3),
            GMMStyle(variable="x_frag_polity", min_lag=2, max_lag=3),
        ],
        iv=[
            IVStyle(variable="w"),
            IVStyle(variable="frag"),
            IVStyle(variable="polity"),
            IVStyle(variable="x_frag"),
            IVStyle(variable="x_polity"),
            IVStyle(variable="frag_polity"),
        ],
        time_dummies=False,
        system=True,
        collapse=True,
        transformation="fod",
        steps="twostep",
        name="system_gmm_three_way_controls",
    )

    use_windmeijer = os.getenv("SYSTEMGMMKIT_NATIVE_WINDMEIJER", "1").strip().lower()
    windmeijer = use_windmeijer not in {"0", "false", "no", "off"}

    res = run_native_dynamic_panel_gmm(
        spec,
        df,
        entity="id",
        time="t",
        windmeijer=windmeijer,
    )

    params = pd.DataFrame(
        {
            "param": list(res.params.index),
            "native_coef": res.params.to_numpy(dtype=float),
            "native_std_err": res.std_errors.reindex(res.params.index).to_numpy(dtype=float),
            "native_z": res.zstats.reindex(res.params.index).to_numpy(dtype=float),
            "native_p_value": res.pvalues.reindex(res.params.index).to_numpy(dtype=float),
            "covariance_type": res.covariance_type,
        }
    )

    params.to_csv(OUT / "native_params.csv", index=False)

    diagnostics = pd.DataFrame(
        [
            {
                "spec": "system_gmm_three_way_controls",
                "native_nobs": getattr(res, "nobs", None),
                "native_n_instruments": getattr(res, "n_instruments", None),
                "native_backend": getattr(res, "backend", None),
                "native_covariance_type": getattr(res, "covariance_type", None),
                "native_instrument_names": ";".join(getattr(res, "instrument_names", []) or []),
                "native_hansen_p": getattr(res, "hansen_p", None),
                "native_hansen_j_stat": getattr(res, "hansen_j_stat", None),
                "native_sargan_p": getattr(res, "sargan_p", None),
                "native_sargan_j_stat": getattr(res, "sargan_j_stat", None),
                "native_overid_df": getattr(res, "overid_df", None),
                "native_ar1_z": getattr(res, "ar1_z", None),
                "native_ar1_p": getattr(res, "ar1_p", None),
                "native_ar2_z": getattr(res, "ar2_z", None),
                "native_ar2_p": getattr(res, "ar2_p", None),
                "native_j_stat": getattr(res, "j_stat", None),
                "native_has_constant_param": "_con" in list(res.params.index),
            }
        ]
    )

    diagnostics.to_csv(OUT / "native_diagnostics.csv", index=False)

    print("Wrote native System GMM three-way controls outputs")
    print(f"covariance_type: {res.covariance_type}")
    print(params.to_string(index=False))


if __name__ == "__main__":
    main()
