from __future__ import annotations

import pandas as pd

from systemgmmkit import DynamicPanelSpec, GMMStyle, IVStyle
from systemgmmkit.native_gmm import run_native_dynamic_panel_gmm

df = pd.read_csv("artifacts/parity/xtabond2/system_gmm_benchmark.csv")

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

print("nobs:", res.nobs)
print("n_instruments:", res.n_instruments)
print("params:", list(res.params.index))
print("instrument_names:", res.instrument_names)
print("hansen_p:", res.hansen_p)
print("sargan_p:", res.sargan_p)
print("ar1_p:", res.ar1_p)
print("ar2_p:", res.ar2_p)
print("z_shape:", res.z_shape)
print("w_shape:", res.w_shape)
print("j_stat:", res.j_stat)
print("ztu_norm:", res.ztu_norm)
print("w_norm:", res.w_norm)