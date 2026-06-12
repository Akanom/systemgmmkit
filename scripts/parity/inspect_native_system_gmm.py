from __future__ import annotations

import pandas as pd

from systemgmmkit import build_system_gmm_spec
from systemgmmkit.native_gmm import run_native_dynamic_panel_gmm


df = pd.read_csv("artifacts/parity/xtabond2/system_gmm_benchmark.csv")

spec = build_system_gmm_spec(
    dependent="y",
    regressors=["x", "w"],
    endogenous=["x"],
    exogenous=["w"],
    dependent_lag_limits=(2, 3),
    collapse=True,
    time_dummies=False,
)

res = run_native_dynamic_panel_gmm(spec, df, entity="id", time="t")

print("nobs:", res.nobs)
print("n_instruments:", res.n_instruments)
print("params:", list(res.params.index))

for attr in ["instrument_names", "instruments", "Z", "z_names", "diagnostics", "metadata", "row_meta"]:
    print("\nATTR", attr, "=", hasattr(res, attr))
    if hasattr(res, attr):
        value = getattr(res, attr)
        print(value if isinstance(value, (str, int, float, list, tuple, dict)) else type(value))