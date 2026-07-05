from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ART26 = Path("Artifacts/Joss/tables/26_static_postestimation_comparison")
ART27 = Path("Artifacts/Joss/tables/27_static_cross_software_comparison")
ART27.mkdir(parents=True, exist_ok=True)


INPUTS = [
    # Python/systemgmmkit/reference results from Artifact 26
    ("statsmodels", "Python", "OLS", ART26 / "26_static_model_results_long.csv"),
    ("linearmodels", "Python", "Pooled OLS", ART26 / "26_static_model_results_long.csv"),
    ("linearmodels", "Python", "Random Effects", ART26 / "26_static_model_results_long.csv"),
    ("systemgmmkit", "Python", "OLS", ART26 / "26_static_model_results_long.csv"),
    ("systemgmmkit", "Python", "Pooled OLS", ART26 / "26_static_model_results_long.csv"),
    ("systemgmmkit", "Python", "Random Effects", ART26 / "26_static_model_results_long.csv"),

    # Focused FE and 2SLS
    ("linearmodels", "Python", "Fixed Effects", ART26 / "26_fixed_effects_diagnostic_long.csv"),
    ("systemgmmkit", "Python", "Fixed Effects", ART26 / "26_fixed_effects_diagnostic_long.csv"),
    ("linearmodels", "Python", "2SLS", ART26 / "26_2sls_linearmodels_results.csv"),
    ("systemgmmkit", "Python", "2SLS", ART26 / "26_2sls_systemgmmkit_results.csv"),

    # R
    ("R lm", "R", "OLS", ART27 / "27_r_ols_results.csv"),
    ("R plm", "R", "Pooled OLS", ART27 / "27_r_pooled_ols_results.csv"),
    ("R plm", "R", "Fixed Effects", ART27 / "27_r_fe_results.csv"),
    ("R plm", "R", "Random Effects", ART27 / "27_r_re_results.csv"),
    ("R AER::ivreg", "R", "2SLS", ART27 / "27_r_2sls_results.csv"),

    # Stata
    ("Stata", "Stata", "OLS", ART27 / "27_stata_ols_results.csv"),
    ("Stata", "Stata", "Pooled OLS", ART27 / "27_stata_pooled_ols_results.csv"),
    ("Stata", "Stata", "Fixed Effects", ART27 / "27_stata_fe_results.csv"),
    ("Stata", "Stata", "Random Effects", ART27 / "27_stata_re_results.csv"),
    ("Stata", "Stata", "2SLS", ART27 / "27_stata_2sls_results.csv"),
]

TERM_MAP = {
    "_con": "const",
    "_cons": "const",
    "const": "const",
    "(Intercept)": "const",
    "Intercept": "const",
    "L1_y": "L1_y",
    "x_pred": "x_pred",
    "x_exog": "x_exog",
}

MODEL_REFERENCE = {
    "OLS": "systemgmmkit",
    "Pooled OLS": "systemgmmkit",
    "Fixed Effects": "systemgmmkit",
    "Random Effects": "systemgmmkit",
    "2SLS": "systemgmmkit",
}


def norm_term(x):
    s = str(x).strip()
    return TERM_MAP.get(s, s)


def load_input(software, language, model, path):
    if not path.exists():
        return pd.DataFrame([{
            "software": software,
            "language": language,
            "model": model,
            "term": None,
            "term_norm": None,
            "coefficient": np.nan,
            "std_error": np.nan,
            "p_value": np.nan,
            "status": "MISSING_FILE",
            "source_file": str(path),
        }])

    df = pd.read_csv(path)

    # Artifact 26 long contains many models/software rows.
    if "model" in df.columns:
        df = df[df["model"].eq(model)].copy()

    if "software" in df.columns:
        # Keep exact software if possible, but allow focused files with their own software names.
        if path.name == "26_static_model_results_long.csv":
            df = df[df["software"].eq(software)].copy()

    if path.name == "26_fixed_effects_diagnostic_long.csv":
        if software == "linearmodels":
            df = df[
                (df["software"].eq("linearmodels"))
                & (df["variant"].eq("entity_fe_no_explicit_constant"))
            ].copy()
        elif software == "systemgmmkit":
            df = df[
                (df["software"].eq("systemgmmkit"))
                & (df["variant"].eq("entity_fe_linearmodels_backend"))
            ].copy()

    # Normalize result columns
    rename = {
        "coef": "coefficient",
        "std_err": "std_error",
        "Std..Error": "std_error",
        "Estimate": "coefficient",
        "Pr...t..": "p_value",
        "Pr...z..": "p_value",
    }
    df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})

    if "term" not in df.columns:
        raise ValueError(f"{path} has no term column")
    if "coefficient" not in df.columns:
        raise ValueError(f"{path} has no coefficient column")
    if "std_error" not in df.columns:
        df["std_error"] = np.nan
    if "p_value" not in df.columns:
        df["p_value"] = np.nan

    out = pd.DataFrame({
        "software": software,
        "language": language,
        "model": model,
        "term": df["term"],
        "term_norm": df["term"].map(norm_term),
        "coefficient": pd.to_numeric(df["coefficient"], errors="coerce"),
        "std_error": pd.to_numeric(df["std_error"], errors="coerce"),
        "p_value": pd.to_numeric(df["p_value"], errors="coerce"),
        "status": "OK",
        "source_file": str(path),
    })

    # For FE, exclude constants from parity table.
    if model == "Fixed Effects":
        out = out[out["term_norm"].ne("const")].copy()

    return out


def classify(max_coef, max_se):
    if pd.isna(max_coef):
        return "NO_COMPARISON"
    if max_coef <= 1e-8 and (pd.isna(max_se) or max_se <= 1e-8):
        return "PASS_NUMERIC"
    if max_coef <= 1e-6:
        return "PASS_COEFFICIENTS"
    return "REVIEW"


def main():
    frames = [load_input(*item) for item in INPUTS]
    long = pd.concat(frames, ignore_index=True)

    long_path = ART27 / "27_static_cross_software_results_long.csv"
    long.to_csv(long_path, index=False)

    rows = []

    for model, ref_sw in MODEL_REFERENCE.items():
        dfm = long[(long["model"].eq(model)) & (long["status"].eq("OK"))].copy()
        ref = dfm[dfm["software"].eq(ref_sw)].copy()

        for sw in sorted(dfm["software"].unique()):
            if sw == ref_sw:
                continue

            other = dfm[dfm["software"].eq(sw)].copy()

            merged = ref.merge(
                other,
                on=["model", "term_norm"],
                suffixes=("_ref", "_other"),
                how="outer",
                indicator=True,
            )

            both = merged[merged["_merge"].eq("both")].copy()
            both["abs_coef_diff"] = (both["coefficient_ref"] - both["coefficient_other"]).abs()
            both["abs_se_diff"] = (both["std_error_ref"] - both["std_error_other"]).abs()

            max_coef = float(both["abs_coef_diff"].max()) if not both.empty else np.nan
            max_se = float(both["abs_se_diff"].max()) if not both.empty else np.nan

            rows.append({
                "model": model,
                "reference": ref_sw,
                "comparison_software": sw,
                "common_terms": int(merged["_merge"].eq("both").sum()),
                "reference_only_terms": int(merged["_merge"].eq("left_only").sum()),
                "comparison_only_terms": int(merged["_merge"].eq("right_only").sum()),
                "max_abs_coef_diff": max_coef,
                "max_abs_se_diff": max_se,
                "status": classify(max_coef, max_se),
            })

            merged.to_csv(
                ART27 / f"27_{model.lower().replace(' ', '_')}_{sw.lower().replace(' ', '_').replace(':', '').replace('::', '_')}_vs_systemgmmkit.csv",
                index=False,
            )

    summary = pd.DataFrame(rows)
    summary_path = ART27 / "27_static_cross_software_pairwise_summary.csv"
    summary.to_csv(summary_path, index=False)

    coef_wide = long[long["status"].eq("OK")].pivot_table(
        index=["model", "term_norm"],
        columns="software",
        values="coefficient",
        aggfunc="first",
    ).reset_index()

    se_wide = long[long["status"].eq("OK")].pivot_table(
        index=["model", "term_norm"],
        columns="software",
        values="std_error",
        aggfunc="first",
    ).reset_index()

    coef_wide.to_csv(ART27 / "27_static_cross_software_coefficients_wide.csv", index=False)
    se_wide.to_csv(ART27 / "27_static_cross_software_standard_errors_wide.csv", index=False)

    md = "# Artifact 27: Static Cross-Software Comparison\n\n"
    md += "## Pairwise Summary Relative to systemgmmkit\n\n"
    md += summary.to_markdown(index=False)
    md += "\n\n## Coefficients\n\n"
    md += coef_wide.to_markdown(index=False)
    md += "\n\n## Standard Errors\n\n"
    md += se_wide.to_markdown(index=False)
    md += "\n\n## Interpretation\n\n"
    md += (
        "This artifact compares static and quasi-static estimators across Python, R, Stata, and systemgmmkit. "
        "OLS, pooled OLS, fixed effects, random effects, and 2SLS are compared term by term. "
        "Fixed-effects comparisons exclude intercepts because fixed-effect intercept normalization differs across implementations. "
        "Coefficient agreement is the primary comparison target for random effects and 2SLS where covariance scaling conventions may differ.\n"
    )

    md_path = ART27 / "27_static_cross_software_summary.md"
    md_path.write_text(md, encoding="utf-8")

    print(summary.to_string(index=False))
    print()
    print(f"[DONE] Wrote {long_path}")
    print(f"[DONE] Wrote {summary_path}")
    print(f"[DONE] Wrote {md_path}")


if __name__ == "__main__":
    main()
