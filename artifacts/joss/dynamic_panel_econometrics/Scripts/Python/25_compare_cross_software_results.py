from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(".")
ART = ROOT / "Artifacts/Joss/tables"
OUT = ART / "25_cross_software_comparison"
OUT.mkdir(parents=True, exist_ok=True)


INPUTS = [
    {
        "software": "systemgmmkit",
        "language": "Python",
        "model": "Difference GMM",
        "path": ART / "22_difference_gmm_results.csv",
    },
    {
        "software": "systemgmmkit",
        "language": "Python",
        "model": "System GMM",
        "path": ART / "22_system_gmm_results.csv",
    },
    {
        "software": "Stata xtabond2",
        "language": "Stata",
        "model": "Difference GMM",
        "path": ART / "22_stata_difference_gmm_coefficients.csv",
    },
    {
        "software": "Stata xtabond2",
        "language": "Stata",
        "model": "System GMM",
        "path": ART / "22_stata_system_gmm_coefficients.csv",
    },
    {
        "software": "plm::pgmm",
        "language": "R",
        "model": "Difference GMM",
        "path": OUT / "25_r_plm_difference_gmm_results.csv",
    },
    {
        "software": "plm::pgmm",
        "language": "R",
        "model": "System GMM",
        "path": OUT / "25_r_plm_system_gmm_results.csv",
    },
    {
        "software": "pydynpd",
        "language": "Python",
        "model": "Difference GMM",
        "path": OUT / "25_python_pydynpd_difference_gmm_results.csv",
    },
    {
        "software": "pydynpd",
        "language": "Python",
        "model": "System GMM",
        "path": OUT / "25_python_pydynpd_system_gmm_results.csv",
    },
]


TERM_MAP = {
    "L.y": "L1_y",
    "l.y": "L1_y",
    "L1.y": "L1_y",
    "L1_y": "L1_y",
    "l1_y": "L1_y",
    "lag(y, 1)": "L1_y",
    "lag(y, 1:1)": "L1_y",
    "_cons": "const",
    "_con": "const",
    "(Intercept)": "const",
    "Intercept": "const",
    "const": "const",
    "x_pred": "x_pred",
    "x_exog": "x_exog",
}


REFERENCE = {
    "Difference GMM": "systemgmmkit",
    "System GMM": "systemgmmkit",
}


NUMERIC_COEF_TOL = 1e-6
NUMERIC_SE_TOL = 1e-6
TOLERANT_COEF_TOL = 0.025
TOLERANT_SE_TOL = 0.05


def norm_term(x: object) -> str:
    s = str(x).strip()
    return TERM_MAP.get(s, s)


def classify(coef_gap: float, se_gap: float) -> str:
    if pd.isna(coef_gap) or pd.isna(se_gap):
        return "NO_COMPARISON"
    if coef_gap <= NUMERIC_COEF_TOL and se_gap <= NUMERIC_SE_TOL:
        return "PASS_NUMERIC"
    if coef_gap <= TOLERANT_COEF_TOL and se_gap <= TOLERANT_SE_TOL:
        return "PASS_TOLERANT_AUXILIARY"
    return "REVIEW"


def standardize_result(item: dict) -> pd.DataFrame:
    path = item["path"]

    if not path.exists():
        return pd.DataFrame([{
            "software": item["software"],
            "language": item["language"],
            "model": item["model"],
            "term": None,
            "term_norm": None,
            "coefficient": None,
            "std_error": None,
            "p_value": None,
            "status": "MISSING_FILE",
            "source_file": str(path),
        }])

    df = pd.read_csv(path)

    # Normalize columns from different result formats.
    rename = {}
    if "coef" in df.columns and "coefficient" not in df.columns:
        rename["coef"] = "coefficient"
    if "std_err" in df.columns and "std_error" not in df.columns:
        rename["std_err"] = "std_error"
    if "Std..Error" in df.columns and "std_error" not in df.columns:
        rename["Std..Error"] = "std_error"
    if "Estimate" in df.columns and "coefficient" not in df.columns:
        rename["Estimate"] = "coefficient"
    if "Pr...z.." in df.columns and "p_value" not in df.columns:
        rename["Pr...z.."] = "p_value"

    df = df.rename(columns=rename)

    if "term" not in df.columns:
        raise ValueError(f"{path} has no term column.")

    if "coefficient" not in df.columns:
        raise ValueError(f"{path} has no coefficient column.")

    if "std_error" not in df.columns:
        df["std_error"] = pd.NA

    if "p_value" not in df.columns:
        df["p_value"] = pd.NA

    out = pd.DataFrame({
        "software": item["software"],
        "language": item["language"],
        "model": item["model"],
        "term": df["term"],
        "term_norm": df["term"].map(norm_term),
        "coefficient": pd.to_numeric(df["coefficient"], errors="coerce"),
        "std_error": pd.to_numeric(df["std_error"], errors="coerce"),
        "p_value": pd.to_numeric(df["p_value"], errors="coerce"),
        "status": "OK",
        "source_file": str(path),
    })

    return out


def main() -> None:
    frames = [standardize_result(item) for item in INPUTS]
    long = pd.concat(frames, ignore_index=True)

    long_path = OUT / "25_cross_software_results_long.csv"
    long.to_csv(long_path, index=False)

    summary_rows = []

    for model, ref_software in REFERENCE.items():
        model_df = long[
            long["model"].eq(model)
            & long["status"].eq("OK")
            & long["term_norm"].notna()
        ].copy()

        ref = model_df[model_df["software"].eq(ref_software)].copy()

        for software in sorted(model_df["software"].unique()):
            if software == ref_software:
                continue

            other = model_df[model_df["software"].eq(software)].copy()

            merged = ref.merge(
                other,
                on=["model", "term_norm"],
                how="outer",
                suffixes=("_ref", "_other"),
                indicator=True,
            )

            both = merged[merged["_merge"].eq("both")].copy()

            both["abs_coef_diff"] = (
                both["coefficient_ref"] - both["coefficient_other"]
            ).abs()

            both["abs_se_diff"] = (
                both["std_error_ref"] - both["std_error_other"]
            ).abs()

            max_coef = float(both["abs_coef_diff"].max()) if not both.empty else float("nan")
            max_se = float(both["abs_se_diff"].max()) if not both.empty else float("nan")

            summary_rows.append({
                "model": model,
                "reference": ref_software,
                "comparison_software": software,
                "common_terms": int(merged["_merge"].eq("both").sum()),
                "reference_only_terms": int(merged["_merge"].eq("left_only").sum()),
                "comparison_only_terms": int(merged["_merge"].eq("right_only").sum()),
                "max_abs_coef_diff": max_coef,
                "max_abs_se_diff": max_se,
                "status": classify(max_coef, max_se),
            })

            detail_path = OUT / (
                "25_pairwise_"
                + model.lower().replace(" ", "_")
                + "_"
                + software.lower().replace(" ", "_").replace("::", "_")
                + "_vs_"
                + ref_software.lower().replace(" ", "_")
                + ".csv"
            )

            merged.to_csv(detail_path, index=False)

    summary = pd.DataFrame(summary_rows)
    summary_path = OUT / "25_cross_software_pairwise_summary.csv"
    summary.to_csv(summary_path, index=False)

    metadata = {
        "artifact": "25",
        "purpose": "Cross-software result comparison for Python/R/Stata dynamic-panel workflows.",
        "reference": REFERENCE,
        "numeric_tolerance": {
            "coef": NUMERIC_COEF_TOL,
            "se": NUMERIC_SE_TOL,
        },
        "tolerant_auxiliary_tolerance": {
            "coef": TOLERANT_COEF_TOL,
            "se": TOLERANT_SE_TOL,
        },
        "important_boundary": (
            "Cross-software equality is not expected unless sample construction, "
            "instrument matrix, equation scope, finite-sample correction, and covariance "
            "scaling are explicitly aligned."
        ),
    }

    metadata_path = OUT / "25_cross_software_comparison_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    md = "# Artifact 25: Cross-Software Result Comparison\n\n"
    md += "## Pairwise Summary\n\n"
    md += summary.to_markdown(index=False)
    md += "\n\n## Interpretation\n\n"
    md += (
        "The comparison uses systemgmmkit as the reference within this artifact. "
        "Stata xtabond2 is expected to match closely where the effective sample and "
        "instrument conventions are aligned. R package results are reported as "
        "ecosystem comparison outputs; strict parity is not assumed unless the "
        "underlying model specification and instrument construction are fully aligned.\n"
    )

    md_path = OUT / "25_cross_software_pairwise_summary.md"
    md_path.write_text(md, encoding="utf-8")

    print(summary.to_string(index=False))
    print()
    print(f"[DONE] Wrote {long_path}")
    print(f"[DONE] Wrote {summary_path}")
    print(f"[DONE] Wrote {metadata_path}")
    print(f"[DONE] Wrote {md_path}")


if __name__ == "__main__":
    main()
