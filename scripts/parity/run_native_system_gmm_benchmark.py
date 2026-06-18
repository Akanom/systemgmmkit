from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

from systemgmmkit import DynamicPanelSpec, GMMStyle, IVStyle
from systemgmmkit.native_gmm import run_native_dynamic_panel_gmm

BASE_OUT = Path("artifacts/parity/xtabond2")
SPEC_OUT = BASE_OUT / "specs" / "system_gmm_baseline_controls"
DATA = BASE_OUT / "system_gmm_benchmark.csv"


def _native_output_dir(*, windmeijer: bool) -> Path:
    return SPEC_OUT / ("windmeijer" if windmeijer else "uncorrected")


def main() -> None:
    df = pd.read_csv(DATA)

    spec = DynamicPanelSpec(
        dependent="y",
        regressors=["L1.y", "x", "w"],
        gmm=[
            GMMStyle(variable="L1.y", min_lag=2, max_lag=3),
            GMMStyle(variable="x", min_lag=2, max_lag=3),
        ],
        iv=[
            IVStyle(variable="w", eq="level"),
        ],
        time_dummies=False,
        system=os.getenv("SYSTEMGMMKIT_NATIVE_SYSTEM", "1").strip().lower() not in {"0", "false", "no", "off"},
        collapse=True,
        transformation=os.getenv("SYSTEMGMMKIT_NATIVE_TRANSFORMATION", "fd").strip().lower(),
        steps="twostep",
        name="system_gmm_baseline_controls",
    )

    use_windmeijer = os.getenv("SYSTEMGMMKIT_NATIVE_WINDMEIJER", "1").strip().lower()
    windmeijer = use_windmeijer not in {"0", "false", "no", "off"}

    out = _native_output_dir(windmeijer=windmeijer)
    out.mkdir(parents=True, exist_ok=True)

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

    if os.getenv("SYSTEMGMMKIT_DROP_NATIVE_CON_FOR_PARITY") == "1":
        params = params[params["param"] != "_con"].copy()

    params.to_csv(out / "native_params.csv", index=False)

    diagnostics = pd.DataFrame(
        [
            {
                "spec": "system_gmm_baseline_controls",
                "native_nobs": getattr(res, "nobs", None),
                "native_n_instruments": getattr(res, "n_instruments", None),
                "native_backend": getattr(res, "backend", None),
                "native_covariance_type": getattr(res, "covariance_type", None),
                "native_instrument_names": ";".join(
                    getattr(res, "instrument_names", []) or []
                ),
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
    diagnostics.to_csv(out / "native_diagnostics.csv", index=False)

    print(f"Wrote native System GMM benchmark outputs to: {out}")
    print(f"covariance_type: {res.covariance_type}")
    print(params.to_string(index=False))


if __name__ == "__main__":
    main()
