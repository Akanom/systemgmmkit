from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd

from systemgmmkit import (
    OLSSpec,
    PooledOLSSpec,
    lincom,
    marginal_effects,
    run_ols,
    run_pooled_ols,
    wald_test,
)

PKG = Path(__file__).resolve().parents[1]
REAL = Path(r"C:\Users\omoko\OneDrive\Desktop - Copy\Publication_papers")
OUT = REAL / "results" / "systemgmmkit_058dev_realdata_stata_ols"
OUT.mkdir(parents=True, exist_ok=True)

print("Package path:", PKG)
print("Real project path:", REAL)
print("Output path:", OUT)

# ------------------------------------------------------------
# 1. Find real FD001 data, using old workflow naming logic
# ------------------------------------------------------------

candidates = []
for pattern in [
    "**/*fd001*.parquet",
    "**/*FD001*.parquet",
    "**/*fd001*.csv",
    "**/*FD001*.csv",
    "**/*cmapss*.parquet",
    "**/*cmapss*.csv",
]:
    candidates.extend(REAL.glob(pattern))

candidates = sorted(set(candidates), key=lambda p: (len(str(p)), str(p).lower()))

if not candidates:
    raise SystemExit("No FD001/CMAPSS data file found under Publication_papers.")

print("\nCandidate data files:")
for p in candidates[:30]:
    print(" -", p)

preferred = [
    p
    for p in candidates
    if any(k in p.name.lower() for k in ["prepared", "panel", "verification", "fd001"])
]

data_path = Path(
    r"C:\Users\omoko\OneDrive\Desktop - Copy\Publication_papers\data_prepared\fd001_prepared_panel.csv"
)
print("\nUsing data file:", data_path)

if data_path.suffix.lower() == ".parquet":
    df = pd.read_parquet(data_path)
elif data_path.suffix.lower() == ".csv":
    df = pd.read_csv(data_path)
else:
    raise SystemExit(f"Unsupported data suffix: {data_path.suffix}")

print("Raw shape:", df.shape)
print("Raw columns:", list(df.columns))

# ------------------------------------------------------------
# 2. Resolve old FD001 verification columns
# ------------------------------------------------------------


def pick(*names: str) -> str | None:
    lower = {c.lower(): c for c in df.columns}
    for name in names:
        if name.lower() in lower:
            return lower[name.lower()]
    return None


entity = pick("unit", "unit_id", "engine", "engine_id", "id", "entity")
time = pick("cycle", "time", "period", "t")

risk = pick("risk")
degradation = pick("degradation_index")
sensor_mean_z = pick("sensor_mean_z")
pc2 = pick("pc2")
op1 = pick("op_setting1", "setting1", "operational_setting_1")
op2 = pick("op_setting2", "setting2", "operational_setting_2")

resolved = {
    "entity": entity,
    "time": time,
    "risk": risk,
    "degradation_index": degradation,
    "sensor_mean_z": sensor_mean_z,
    "pc2": pc2,
    "op_setting1": op1,
    "op_setting2": op2,
}

print("\nResolved columns:")
for k, v in resolved.items():
    print(f" {k}: {v}")

if any(v is None for v in [entity, time, risk, degradation, sensor_mean_z, pc2, op1, op2]):
    raise SystemExit("Column resolution failed. Paste resolved columns + raw columns output.")

# ------------------------------------------------------------
# 3. Build exact same estimation sample for Python and Stata
# ------------------------------------------------------------

work = df[[entity, time, risk, degradation, sensor_mean_z, pc2, op1, op2]].copy()

# Standardize names for Stata-safe export and exact comparison.
work = work.rename(
    columns={
        entity: "unit_id",
        time: "cycle",
        risk: "risk",
        degradation: "degradation_index",
        sensor_mean_z: "sensor_mean_z",
        pc2: "pc2",
        op1: "op_setting1",
        op2: "op_setting2",
    }
)

for c in ["risk", "degradation_index", "sensor_mean_z", "pc2", "op_setting1", "op_setting2"]:
    work[c] = pd.to_numeric(work[c], errors="coerce")

work = work.dropna(
    subset=[
        "unit_id",
        "cycle",
        "risk",
        "degradation_index",
        "sensor_mean_z",
        "pc2",
        "op_setting1",
        "op_setting2",
    ]
).copy()

# Stable sorting to match old reproducible workflow.
work = work.sort_values(["unit_id", "cycle"]).reset_index(drop=True)
work["obs_id"] = np.arange(1, len(work) + 1)

print("\nEstimation sample shape:", work.shape)
print("Entities:", work["unit_id"].nunique())
print("Cycle min/max:", work["cycle"].min(), work["cycle"].max())

csv_path = OUT / "fd001_real_ols_estimation_sample.csv"
dta_path = OUT / "fd001_real_ols_estimation_sample.dta"

work.to_csv(csv_path, index=False)
work.to_stata(dta_path, write_index=False, version=118)

print("\nWrote sample CSV:", csv_path)
print("Wrote sample DTA:", dta_path)

# ------------------------------------------------------------
# 4. Native systemgmmkit OLS and pooled OLS
# ------------------------------------------------------------

xvars = [
    "degradation_index",
    "sensor_mean_z",
    "pc2",
    "op_setting1",
    "op_setting2",
]

ols_spec = OLSSpec(
    dependent="risk",
    regressors=xvars,
    covariance="robust",
    name="fd001_real_ols_robust",
)

pooled_spec = PooledOLSSpec(
    dependent="risk",
    regressors=xvars,
    covariance="clustered",
    name="fd001_real_pooled_ols_cluster_unit",
)

ols = run_ols(ols_spec, work)
pooled = run_pooled_ols(pooled_spec, work, entity="unit_id", time="cycle")

native_ols = ols.summary_frame().reset_index().rename(columns={"index": "term"})
native_pooled = pooled.summary_frame().reset_index().rename(columns={"index": "term"})

native_ols["model"] = "native_ols_robust"
native_pooled["model"] = "native_pooled_cluster_unit"

native_ols_path = OUT / "native_ols_robust.csv"
native_pooled_path = OUT / "native_pooled_cluster_unit.csv"

native_ols.to_csv(native_ols_path, index=False)
native_pooled.to_csv(native_pooled_path, index=False)

print("\nNative OLS:")
print(native_ols)

print("\nNative pooled clustered OLS:")
print(native_pooled)

# Post-estimation native outputs
mfx = marginal_effects(pooled)
lc = lincom(pooled, {"degradation_index": 1.0, "sensor_mean_z": 1.0})

params = list(pooled.params.index)
R = []
for name in xvars:
    row = [0.0] * len(params)
    row[params.index(name)] = 1.0
    R.append(row)

wt = wald_test(pooled, R=R, use_f=True)

mfx.to_csv(OUT / "native_marginal_effects.csv", index=False)
pd.DataFrame([lc]).to_csv(OUT / "native_lincom_degradation_plus_sensor.csv", index=False)
pd.DataFrame([wt]).to_csv(OUT / "native_wald_all_slopes.csv", index=False)

# ------------------------------------------------------------
# 5. Generate Stata .do using same sample
# ------------------------------------------------------------

do_path = OUT / "fd001_real_ols_stata_compare.do"
stata_ols_path = OUT / "stata_ols_robust.csv"
stata_pooled_path = OUT / "stata_pooled_cluster_unit.csv"
stata_lincom_path = OUT / "stata_lincom_degradation_plus_sensor.csv"
stata_wald_path = OUT / "stata_wald_all_slopes.csv"

do_text = f'''
clear all
set more off
version 14.0

cd "{str(OUT).replace(chr(92), "/")}"

use "{str(dta_path).replace(chr(92), "/")}", clear

xtset unit_id cycle

capture program drop write_model
program define write_model
    syntax using/, MODEL(string)
    tempname posth
    postfile `posth' str40 model str40 term double coef double std_err double t double p_value using "`using'", replace
    matrix b = e(b)
    matrix V = e(V)
    local cnames : colnames b
    local df = e(df_r)
    foreach name of local cnames {{
        local coef = b[1, colnumb(b, "`name'")]
        local se = sqrt(V[colnumb(V, "`name'"), colnumb(V, "`name'")])
        local t = `coef' / `se'
        local p = 2 * ttail(`df', abs(`t'))
        local clean = "`name'"
        if "`clean'" == "_cons" local clean = "_con"
        post `posth' ("`model'") ("`clean'") (`coef') (`se') (`t') (`p')
    }}
    postclose `posth'
end

regress risk degradation_index sensor_mean_z pc2 op_setting1 op_setting2, vce(robust)
write_model using "{stata_ols_path.name}", model("stata_ols_robust")

regress risk degradation_index sensor_mean_z pc2 op_setting1 op_setting2, vce(cluster unit_id)
write_model using "{stata_pooled_path.name}", model("stata_pooled_cluster_unit")

regress risk degradation_index sensor_mean_z pc2 op_setting1 op_setting2, vce(cluster unit_id)

matrix B = e(b)
matrix V = e(V)

scalar lincom_estimate = B[1,"degradation_index"] + B[1,"sensor_mean_z"]
scalar lincom_variance = ///
    V["degradation_index","degradation_index"] + ///
    V["sensor_mean_z","sensor_mean_z"] + ///
    2 * V["degradation_index","sensor_mean_z"]

scalar lincom_std_error = sqrt(lincom_variance)
scalar lincom_statistic = lincom_estimate / lincom_std_error
scalar lincom_df = e(df_r)
scalar lincom_p_value = 2 * ttail(lincom_df, abs(lincom_statistic))
scalar lincom_crit = invttail(lincom_df, 0.025)
scalar lincom_ci_lower = lincom_estimate - lincom_crit * lincom_std_error
scalar lincom_ci_upper = lincom_estimate + lincom_crit * lincom_std_error

clear
set obs 1
gen estimate = lincom_estimate
gen std_error = lincom_std_error
gen statistic = lincom_statistic
gen p_value = lincom_p_value
gen ci_lower = lincom_ci_lower
gen ci_upper = lincom_ci_upper
export delimited using "{stata_lincom_path.name}", replace
erase "stata_lincom_degradation_plus_sensor_temp.dta"

use "{str(dta_path).replace(chr(92), "/")}", clear
regress risk degradation_index sensor_mean_z pc2 op_setting1 op_setting2, vce(cluster unit_id)
test degradation_index sensor_mean_z pc2 op_setting1 op_setting2
clear
set obs 1
gen statistic = r(F)
gen df_constraints = r(df)
gen df_resid = r(df_r)
gen p_value = r(p)
gen distribution = "F"
export delimited using "{stata_wald_path.name}", replace

exit, clear
'''

do_path.write_text(do_text, encoding="utf-8")
print("\nWrote Stata do-file:", do_path)

# ------------------------------------------------------------
# 6. Try to run Stata batch exactly like previous parity workflow
# ------------------------------------------------------------

stata_candidates = [
    shutil.which("StataMP-64.exe"),
    shutil.which("StataSE-64.exe"),
    shutil.which("StataBE-64.exe"),
    shutil.which("stata-mp"),
    shutil.which("stata-se"),
    shutil.which("stata"),
    r"C:\Program Files\Stata18\StataMP-64.exe",
    r"C:\Program Files\Stata17\StataMP-64.exe",
    r"C:\Program Files\Stata16\StataMP-64.exe",
    r"C:\Program Files\Stata15\StataMP-64.exe",
    r"C:\Program Files\Stata14\StataMP-64.exe",
]

stata_exe = None
for c in stata_candidates:
    if c and Path(c).exists():
        stata_exe = str(c)
        break

if stata_exe is None:
    print("\nWARNING: Stata executable not found automatically.")
    print("Run this manually in Stata:")
    print(f'do "{do_path}"')
    raise SystemExit(0)

print("\nRunning Stata:", stata_exe)

cmd = [stata_exe, "/e", "do", str(do_path)]
subprocess.run(cmd, check=True)

print("Stata batch completed.")

# ------------------------------------------------------------
# 7. Compare native vs Stata
# ------------------------------------------------------------


def load_stata(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"Expected Stata output not found: {path}")
    try:
        out = pd.read_csv(path)
    except UnicodeDecodeError:
        out = pd.read_stata(path)
    out["term"] = out["term"].astype(str)
    return out


stata_ols = load_stata(stata_ols_path)
stata_pooled = load_stata(stata_pooled_path)


def compare(native: pd.DataFrame, stata: pd.DataFrame, label: str) -> pd.DataFrame:
    n = native.copy()
    s = stata.copy()

    n = n.rename(
        columns={
            "coef": "native_coef",
            "std_err": "native_std_err",
            "t": "native_t",
            "p_value": "native_p_value",
        }
    )

    s = s.rename(
        columns={
            "coef": "stata_coef",
            "std_err": "stata_std_err",
            "t": "stata_t",
            "p_value": "stata_p_value",
        }
    )

    keep_n = ["term", "native_coef", "native_std_err", "native_t", "native_p_value"]
    keep_s = ["term", "stata_coef", "stata_std_err", "stata_t", "stata_p_value"]

    merged = n[keep_n].merge(s[keep_s], on="term", how="outer", indicator=True)
    merged["model"] = label
    merged["abs_coef_diff"] = (merged["native_coef"] - merged["stata_coef"]).abs()
    merged["abs_se_diff"] = (merged["native_std_err"] - merged["stata_std_err"]).abs()
    return merged[
        [
            "model",
            "term",
            "native_coef",
            "stata_coef",
            "abs_coef_diff",
            "native_std_err",
            "stata_std_err",
            "abs_se_diff",
            "native_t",
            "stata_t",
            "native_p_value",
            "stata_p_value",
            "_merge",
        ]
    ]


cmp_ols = compare(native_ols, stata_ols, "ols_robust")
cmp_pooled = compare(native_pooled, stata_pooled, "pooled_cluster_unit")

cmp_all = pd.concat([cmp_ols, cmp_pooled], ignore_index=True)
cmp_path = OUT / "native_vs_stata_ols_comparison.csv"
cmp_all.to_csv(cmp_path, index=False)

print("\nComparison:")
print(cmp_all)

print("\nMax coefficient diff:", cmp_all["abs_coef_diff"].max())
print("Max SE diff:", cmp_all["abs_se_diff"].max())
print("Wrote comparison:", cmp_path)

# Lincom and Wald comparison files are also produced.
print("\nStata lincom output:", stata_lincom_path)
print("Native lincom output:", OUT / "native_lincom_degradation_plus_sensor.csv")
print("Stata Wald output:", stata_wald_path)
print("Native Wald output:", OUT / "native_wald_all_slopes.csv")

print("\nOK: real FD001 native-vs-Stata OLS comparison completed.")
