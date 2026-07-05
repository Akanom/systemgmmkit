from __future__ import annotations

from pathlib import Path

import pandas as pd
import statsmodels.api as sm
from linearmodels.iv import IV2SLS

from systemgmmkit import PanelIVSpec, run_panel_2sls

ROOT = Path(".")
DATA = ROOT / "Data/Processed/22_dynamic_gmm_controlled_panel.csv"
OUT = ROOT / "Artifacts/Joss/tables/26_static_postestimation_comparison"
OUT.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(DATA).sort_values(["id", "time"]).copy()

if "L1_y" not in df.columns:
    df["L1_y"] = df.groupby("id")["y"].shift(1)

df["L2_x_pred"] = df.groupby("id")["x_pred"].shift(2)

iv_df = df.dropna(subset=["y", "L1_y", "x_exog", "x_pred", "L2_x_pred"]).copy()

# Reference: linearmodels IV2SLS
ref = IV2SLS(
    dependent=iv_df["y"],
    exog=sm.add_constant(iv_df[["L1_y", "x_exog"]], has_constant="add"),
    endog=iv_df[["x_pred"]],
    instruments=iv_df[["L2_x_pred"]],
).fit(cov_type="unadjusted")

# systemgmmkit 0.5.11 API: parameter name is exog, not exogenous.
spec = PanelIVSpec(
    dependent="y",
    exog=["L1_y", "x_exog"],
    endogenous=["x_pred"],
    instruments=["L2_x_pred"],
    covariance="unadjusted",
    add_constant=True,
)

sgk = run_panel_2sls(
    spec,
    iv_df,
    entity="id",
    time="time",
)

def to_frame(result, software):
    params = pd.Series(result.params)

    se = None
    for attr in ["std_errors", "bse", "std_error", "standard_errors"]:
        if hasattr(result, attr):
            se = pd.Series(getattr(result, attr))
            break
    if se is None:
        se = pd.Series([float("nan")] * len(params), index=params.index)

    pvals = None
    for attr in ["pvalues", "p_values"]:
        if hasattr(result, attr):
            pvals = pd.Series(getattr(result, attr))
            break
    if pvals is None:
        pvals = pd.Series([float("nan")] * len(params), index=params.index)

    out = pd.DataFrame({
        "software": software,
        "term": params.index.astype(str),
        "coefficient": params.values,
        "std_error": se.reindex(params.index).values,
        "p_value": pvals.reindex(params.index).values,
    })

    out["term_norm"] = out["term"].replace({
        "_con": "const",
        "_cons": "const",
        "Intercept": "const",
        "const": "const",
    })

    return out

ref_df = to_frame(ref, "linearmodels")
sgk_df = to_frame(sgk, "systemgmmkit")

ref_df.to_csv(OUT / "26_2sls_linearmodels_results.csv", index=False)
sgk_df.to_csv(OUT / "26_2sls_systemgmmkit_results.csv", index=False)

merged = ref_df.merge(
    sgk_df,
    on="term_norm",
    suffixes=("_ref", "_sgk"),
    how="outer",
    indicator=True,
)

merged["abs_coef_diff"] = (merged["coefficient_ref"] - merged["coefficient_sgk"]).abs()
merged["abs_se_diff"] = (merged["std_error_ref"] - merged["std_error_sgk"]).abs()

merged.to_csv(OUT / "26_2sls_linearmodels_systemgmmkit_comparison.csv", index=False)

max_coef = merged["abs_coef_diff"].max()
max_se = merged["abs_se_diff"].max()

status = "PASS_NUMERIC" if max_coef <= 1e-8 and max_se <= 1e-8 else (
    "PASS_COEFFICIENTS" if max_coef <= 1e-6 else "REVIEW"
)

summary = pd.DataFrame([{
    "model": "2SLS",
    "reference": "linearmodels",
    "comparison_software": "systemgmmkit",
    "common_terms": int(merged["_merge"].eq("both").sum()),
    "reference_only_terms": int(merged["_merge"].eq("left_only").sum()),
    "comparison_only_terms": int(merged["_merge"].eq("right_only").sum()),
    "max_abs_coef_diff": max_coef,
    "max_abs_se_diff": max_se,
    "status": status,
}])

summary.to_csv(OUT / "26_2sls_focused_summary.csv", index=False)

print(merged.to_string(index=False))
print()
print(summary.to_string(index=False))
