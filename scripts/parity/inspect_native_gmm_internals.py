from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from systemgmmkit import DynamicPanelSpec, GMMStyle, IVStyle
from systemgmmkit.native_gmm import run_native_dynamic_panel_gmm

OUT = Path("artifacts/parity/xtabond2")
DATA = OUT / "system_gmm_benchmark.csv"


def main() -> None:
    df = pd.read_csv(DATA)

    spec = DynamicPanelSpec(
        dependent="y",
        regressors=["L1.y", "x", "w"],
        gmm=[
            GMMStyle(variable="y", min_lag=2, max_lag=3),
            GMMStyle(variable="x", min_lag=2, max_lag=3),
        ],
        iv=[IVStyle(variable="w")],
        time_dummies=False,
        system=True,
        collapse=True,
        transformation="fod",
        steps="twostep",
        name="system_gmm_baseline_controls",
    )

    res = run_native_dynamic_panel_gmm(spec, df, entity="id", time="t")

    residuals = res.residuals.to_numpy(dtype=float)

    rows = [
        {
            "spec": spec.name,
            "nobs": res.nobs,
            "n_instruments": res.n_instruments,
            "n_params": len(res.params),
            "overid_df": res.n_instruments - len(res.params),
            "residual_norm": float(np.linalg.norm(residuals)),
            "residual_ss": float(residuals @ residuals),
            "params": ";".join(res.params.index),
            "instrument_names": ";".join(res.instrument_names or []),
            "hansen_p": res.hansen_p,
            "sargan_p": res.sargan_p,
            "ar1_p": res.ar1_p,
            "ar2_p": res.ar2_p,
        }
    ]

    out = pd.DataFrame(rows)
    out.to_csv(OUT / "native_gmm_internal_diagnostics.csv", index=False)

    print(out.to_string(index=False))
    print(f"Wrote {OUT / 'native_gmm_internal_diagnostics.csv'}")


if __name__ == "__main__":
    main()
