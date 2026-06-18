from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from systemgmmkit import DynamicPanelSpec, GMMStyle, IVStyle
from systemgmmkit.native_gmm import run_native_dynamic_panel_gmm


def find_col(columns: Iterable[str], candidates: list[str]) -> str | None:
    lookup = {str(c).lower(): str(c) for c in columns}
    for cand in candidates:
        if cand.lower() in lookup:
            return lookup[cand.lower()]
    return None


def read_panel(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".parquet":
        df = pd.read_parquet(path)
    else:
        df = pd.read_csv(path)

    entity = find_col(df.columns, ["id", "unit", "unit_id", "unit_number", "engine", "engine_id"])
    time = find_col(df.columns, ["t", "time", "cycle", "cycles", "time_in_cycles"])

    if entity is None or time is None:
        raise RuntimeError(
            f"Could not detect entity/time columns. Available columns: {list(df.columns)}"
        )

    if entity != "id":
        df["id"] = df[entity]
    if time != "t":
        df["t"] = df[time]

    df["id"] = pd.to_numeric(df["id"], errors="coerce")
    df["t"] = pd.to_numeric(df["t"], errors="coerce")
    df = df.dropna(subset=["id", "t"]).copy()
    df["id"] = df["id"].astype(int)
    df["t"] = df["t"].astype(int)

    return df.sort_values(["id", "t"]).reset_index(drop=True)


MODELS = {
    "risk": {
        "dependent": "risk",
        "lagged_native": "L1.risk",
        "lagged_stata": "L.risk",
        "controls": ["degradation_index", "sensor_mean_z", "pc2", "op_setting1", "op_setting2"],
        "gmm": ["L1.risk", "degradation_index", "sensor_mean_z", "pc2"],
        "gmm_stata": ["L.risk", "degradation_index", "sensor_mean_z", "pc2"],
        "iv": ["op_setting1", "op_setting2"],
    },
    "degradation": {
        "dependent": "degradation_index",
        "lagged_native": "L1.degradation_index",
        "lagged_stata": "L.degradation_index",
        "controls": ["sensor_mean_z", "pc2", "pc3", "op_setting1", "op_setting2"],
        "gmm": ["L1.degradation_index", "sensor_mean_z", "pc2", "pc3"],
        "gmm_stata": ["L.degradation_index", "sensor_mean_z", "pc2", "pc3"],
        "iv": ["op_setting1", "op_setting2"],
    },
}


def run_native(df: pd.DataFrame, out_root: Path, model_name: str, model: dict) -> None:
    required = ["id", "t", model["dependent"], *model["controls"]]
    missing = [c for c in required if c not in df.columns]
    if missing:
        print(f"SKIP {model_name}: missing columns {missing}")
        return

    model_dir = out_root / model_name
    model_dir.mkdir(parents=True, exist_ok=True)

    spec = DynamicPanelSpec(
        dependent=model["dependent"],
        regressors=[model["lagged_native"], *model["controls"]],
        gmm=[
            GMMStyle(variable=v, min_lag=2, max_lag=3)
            for v in model["gmm"]
        ],
        iv=[
            IVStyle(variable=v, eq="level")
            for v in model["iv"]
        ],
        system=True,
        collapse=True,
        transformation="fd",
        steps="twostep",
        time_dummies=False,
        name=f"fd001_{model_name}_system_gmm_publication_validation",
    )

    os.environ["SYSTEMGMMKIT_REPORT_EXPERIMENTAL_SYSTEM_AR"] = "1"
    os.environ.pop("SYSTEMGMMKIT_XTABOND2_AR_M2_COV_MODE", None)
    os.environ.pop("SYSTEMGMMKIT_XTABOND2_AR_VXW_COV_MODE", None)
    os.environ.pop("SYSTEMGMMKIT_XTABOND2_AR_COV_MODE", None)
    os.environ.pop("SYSTEMGMMKIT_XTABOND2_AR_A_MODE", None)
    os.environ.pop("SYSTEMGMMKIT_XTABOND2_AR_LAG_MODE", None)

    res = run_native_dynamic_panel_gmm(
        spec,
        df,
        entity="id",
        time="t",
        windmeijer=True,
    )

    params = pd.DataFrame(
        {
            "param": list(res.params.index),
            "native_coef": res.params.to_numpy(dtype=float),
            "native_std_err": res.std_errors.reindex(res.params.index).to_numpy(dtype=float),
            "native_z": res.zstats.reindex(res.params.index).to_numpy(dtype=float),
            "native_p_value": res.pvalues.reindex(res.params.index).to_numpy(dtype=float),
            "covariance_type": getattr(res, "covariance_type", None),
        }
    )
    params.to_csv(model_dir / "native_params.csv", index=False)

    diagnostics = pd.DataFrame(
        [
            {
                "spec": f"fd001_{model_name}_system_gmm_publication_validation",
                "native_nobs": getattr(res, "nobs", np.nan),
                "native_n_instruments": getattr(res, "n_instruments", np.nan),
                "native_backend": getattr(res, "backend", None),
                "native_covariance_type": getattr(res, "covariance_type", None),
                "native_hansen_p": getattr(res, "hansen_p", np.nan),
                "native_hansen_j_stat": getattr(res, "hansen_j_stat", np.nan),
                "native_sargan_p": getattr(res, "sargan_p", np.nan),
                "native_sargan_j_stat": getattr(res, "sargan_j_stat", np.nan),
                "native_overid_df": getattr(res, "overid_df", np.nan),
                "native_ar1_z": getattr(res, "ar1_z", np.nan),
                "native_ar1_p": getattr(res, "ar1_p", np.nan),
                "native_ar2_z": getattr(res, "ar2_z", np.nan),
                "native_ar2_p": getattr(res, "ar2_p", np.nan),
                "native_j_stat": getattr(res, "j_stat", np.nan),
                "native_instrument_names": ";".join(getattr(res, "instrument_names", []) or []),
            }
        ]
    )
    diagnostics.to_csv(model_dir / "native_diagnostics.csv", index=False)

    print()
    print("=" * 100)
    print(f"NATIVE COMPLETE: {model_name}")
    print("=" * 100)
    print(params.to_string(index=False))
    print(diagnostics.to_string(index=False))


def write_stata_do(df: pd.DataFrame, out_root: Path, model_name: str, model: dict) -> None:
    required = ["id", "t", model["dependent"], *model["controls"]]
    missing = [c for c in required if c not in df.columns]
    if missing:
        return

    model_dir = out_root / model_name
    model_dir.mkdir(parents=True, exist_ok=True)

    stata_df = df[required].copy()
    for col in required:
        stata_df[col] = pd.to_numeric(stata_df[col], errors="coerce")
    stata_df = stata_df.dropna(subset=required).sort_values(["id", "t"]).reset_index(drop=True)

    stata_input = model_dir / "stata_input.csv"
    stata_df.to_csv(stata_input, index=False)

    dep = model["dependent"]
    regressors = " ".join([model["lagged_stata"], *model["controls"]])
    gmm_clause = " ".join(model["gmm_stata"])
    iv_clause = " ".join(model["iv"])

    input_path = str(stata_input).replace("\\", "/")
    params_path = str(model_dir / "stata_params.csv").replace("\\", "/")
    diag_path = str(model_dir / "stata_diagnostics.csv").replace("\\", "/")

    do_text = f'''
clear all
set more off

capture which xtabond2
if _rc {{
    ssc install xtabond2, replace
}}

import delimited using "{input_path}", clear varnames(1)
xtset id t

xtabond2 {dep} {regressors}, ///
    gmm({gmm_clause}, lag(2 3) collapse eq(both)) ///
    iv({iv_clause}, eq(level)) ///
    twostep robust small

matrix b = e(b)
matrix V = e(V)
local cn : colfullnames b
local k = colsof(b)

preserve
clear
set obs `k'

gen str80 param = ""
gen double stata_coef = .
gen double stata_std_err = .

forvalues j = 1/`k' {{
    local pname : word `j' of `cn'
    replace param = "`pname'" in `j'
    replace stata_coef = b[1, `j'] in `j'
    replace stata_std_err = sqrt(V[`j', `j']) in `j'
}}

replace param = subinstr(param, "L.", "L1.", .)
replace param = "_con" if param == "_cons"

export delimited using "{params_path}", replace
restore

scalar s_N = .
capture scalar s_N = e(N)

scalar s_N_g = .
capture scalar s_N_g = e(N_g)

scalar s_j = .
capture scalar s_j = e(j)

scalar s_hansen = .
capture scalar s_hansen = e(hansen)

scalar s_hansenp = .
capture scalar s_hansenp = e(hansenp)

scalar s_sargan = .
capture scalar s_sargan = e(sargan)

scalar s_sarganp = .
capture scalar s_sarganp = e(sarganp)

scalar s_ar1 = .
capture scalar s_ar1 = e(ar1)

scalar s_ar1p = .
capture scalar s_ar1p = e(ar1p)

scalar s_ar2 = .
capture scalar s_ar2 = e(ar2)

scalar s_ar2p = .
capture scalar s_ar2p = e(ar2p)

clear
set obs 1

gen str80 spec = "fd001_{model_name}_system_gmm_publication_validation"
gen double stata_nobs = s_N
gen double stata_n_groups = s_N_g
gen double stata_n_instruments = s_j
gen double stata_hansen = s_hansen
gen double stata_hansen_p = s_hansenp
gen double stata_sargan = s_sargan
gen double stata_sargan_p = s_sarganp
gen double stata_ar1 = s_ar1
gen double stata_ar1_p = s_ar1p
gen double stata_ar2 = s_ar2
gen double stata_ar2_p = s_ar2p

export delimited using "{diag_path}", replace
'''

    do_path = model_dir / "stata_xtabond2.do"
    do_path.write_text(do_text.strip() + "\n", encoding="utf-8")

    print(f"WROTE STATA DO: {do_path}")


def main() -> None:
    data_path = Path(os.environ["SYSTEMGMMKIT_CMAPSS_DATA"])
    publication_root = Path(os.environ["SYSTEMGMMKIT_PUBLICATION_ROOT"])

    out_root = publication_root / "artifacts" / "parity" / "publication" / "cmapss_fd001"
    out_root.mkdir(parents=True, exist_ok=True)

    df = read_panel(data_path)

    print("FD001 prepared panel loaded")
    print("rows:", len(df))
    print("entities:", df["id"].nunique())
    print("time min/max:", int(df["t"].min()), int(df["t"].max()))
    print("columns:", list(df.columns))

    for model_name, model in MODELS.items():
        run_native(df, out_root, model_name, model)
        write_stata_do(df, out_root, model_name, model)

    print()
    print("NEXT STATA COMMANDS:")
    print(f'do "{str(out_root / "risk" / "stata_xtabond2.do").replace(chr(92), "/")}"')
    print(f'do "{str(out_root / "degradation" / "stata_xtabond2.do").replace(chr(92), "/")}"')


if __name__ == "__main__":
    main()
