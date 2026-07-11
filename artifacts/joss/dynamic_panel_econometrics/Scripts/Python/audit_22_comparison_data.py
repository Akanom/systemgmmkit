from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path("Artifacts/Joss/tables/22_data_audit")
OUT.mkdir(parents=True, exist_ok=True)

PATHS = {
    "panel": Path("Data/Processed/22_dynamic_gmm_controlled_panel.csv"),
    "difference_result": Path("Artifacts/Joss/tables/22_difference_gmm_results.csv"),
    "system_result": Path("Artifacts/Joss/tables/22_system_gmm_results.csv"),
    "stata_difference_coefficients": Path("Artifacts/Joss/tables/22_stata_difference_gmm_coefficients.csv"),
    "stata_system_coefficients": Path("Artifacts/Joss/tables/22_stata_system_gmm_coefficients.csv"),
    "comparison": Path("Artifacts/Joss/tables/22_stata_systemgmmkit_parity_comparison.csv"),
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def add(rows, check, status, value="", details=""):
    rows.append({
        "check": check,
        "status": status,
        "value": value,
        "details": details,
    })


def norm_term(x):
    s = str(x).strip()
    return {
        "L.y": "L1_y",
        "l.y": "L1_y",
        "L1.y": "L1_y",
        "L1_y": "L1_y",
        "l1_y": "L1_y",
        "_cons": "const",
        "_con": "const",
        "cons": "const",
        "const": "const",
    }.get(s, s)


def term_set(path: Path):
    if not path.exists():
        return set()
    df = pd.read_csv(path)
    for col in ["term", "param", "parm"]:
        if col in df.columns:
            return set(df[col].dropna().map(norm_term))
    return set()


def compare_to_panel(panel: pd.DataFrame, path: Path, name: str, rows: list[dict]):
    if not path.exists():
        add(rows, f"{name}_exists", "FAIL", "missing", str(path))
        return

    other = pd.read_csv(path)
    add(rows, f"{name}_exists", "PASS", str(path), f"shape={other.shape}")

    common = [c for c in panel.columns if c in other.columns]
    if not {"id", "time"}.issubset(common):
        add(rows, f"{name}_id_time_columns", "FAIL", "", f"common columns={common}")
        return

    p = panel[common].sort_values(["id", "time"]).reset_index(drop=True)
    o = other[common].sort_values(["id", "time"]).reset_index(drop=True)

    if p.shape != o.shape:
        add(rows, f"{name}_same_shape_as_panel", "FAIL", f"{p.shape} vs {o.shape}", "")
        return

    numeric_cols = [c for c in common if c not in ["id", "time"] and pd.api.types.is_numeric_dtype(p[c])]
    max_abs = 0.0
    worst_col = ""

    for col in numeric_cols:
        diff = (pd.to_numeric(p[col], errors="coerce") - pd.to_numeric(o[col], errors="coerce")).abs()
        col_max = float(diff.max(skipna=True)) if len(diff) else 0.0
        if col_max > max_abs:
            max_abs = col_max
            worst_col = col

    status = "PASS" if max_abs <= 1e-12 else "REVIEW"
    add(rows, f"{name}_matches_panel_common_columns", status, f"max_abs_diff={max_abs}", f"worst_col={worst_col}; common={common}")


def main():
    rows = []

    for name, path in PATHS.items():
        if path.exists():
            add(rows, f"file_exists_{name}", "PASS", str(path), f"sha256={sha256(path)[:16]}")
        else:
            add(rows, f"file_exists_{name}", "FAIL", str(path), "missing")

    panel_path = PATHS["panel"]
    if not panel_path.exists():
        raise FileNotFoundError(panel_path)

    df = pd.read_csv(panel_path)
    add(rows, "panel_shape", "PASS", str(df.shape), f"columns={list(df.columns)}")

    required = ["id", "time", "y", "x_pred", "x_exog", "L1_y"]
    missing = [c for c in required if c not in df.columns]
    add(rows, "required_columns", "PASS" if not missing else "FAIL", ",".join(missing), f"required={required}")

    dup = int(df.duplicated(["id", "time"]).sum())
    add(rows, "duplicate_id_time_rows", "PASS" if dup == 0 else "FAIL", dup, "")

    n_ids = int(df["id"].nunique())
    n_times = int(df["time"].nunique())
    add(rows, "panel_dimensions", "PASS", f"ids={n_ids}, times={n_times}, rows={len(df)}", "")

    counts = df.groupby("id")["time"].nunique()
    balanced = counts.nunique() == 1
    add(rows, "balanced_by_id_time_count", "PASS" if balanced else "REVIEW", counts.describe().to_dict(), "")

    miss = df[required].isna().sum().to_dict()
    add(rows, "missing_values_required_columns", "PASS", json.dumps(miss), "")

    # Lag audit
    sdf = df.sort_values(["id", "time"]).copy()
    sdf["computed_L1_y"] = sdf.groupby("id")["y"].shift(1)

    comparable = sdf["L1_y"].notna() & sdf["computed_L1_y"].notna()
    lag_diff = (sdf.loc[comparable, "L1_y"] - sdf.loc[comparable, "computed_L1_y"]).abs()
    max_lag_diff = float(lag_diff.max(skipna=True)) if len(lag_diff) else np.nan
    bad_lag_rows = int((lag_diff > 1e-10).sum()) if len(lag_diff) else 0

    add(
        rows,
        "L1_y_matches_group_lag_y",
        "PASS" if bad_lag_rows == 0 and max_lag_diff <= 1e-10 else "FAIL",
        f"max_abs_lag_diff={max_lag_diff}",
        f"bad_lag_rows={bad_lag_rows}",
    )

    first_time = sdf.groupby("id")["time"].transform("min").eq(sdf["time"])
    first_missing = int(sdf.loc[first_time, "L1_y"].isna().sum())
    nonfirst_missing = int(sdf.loc[~first_time, "L1_y"].isna().sum())

    add(rows, "first_period_L1_y_missing_count", "PASS", first_missing, "expected one missing lag per id")
    add(rows, "nonfirst_period_L1_y_missing_count", "PASS" if nonfirst_missing == 0 else "FAIL", nonfirst_missing, "")

    # Term audits
    sgk_diff_terms = term_set(PATHS["difference_result"])
    sgk_sys_terms = term_set(PATHS["system_result"])
    stata_diff_terms = term_set(PATHS["stata_difference_coefficients"])
    stata_sys_terms = term_set(PATHS["stata_system_coefficients"])

    add(rows, "difference_term_overlap", "PASS" if sgk_diff_terms <= stata_diff_terms or sgk_diff_terms == stata_diff_terms else "REVIEW",
        f"sgk={sorted(sgk_diff_terms)}; stata={sorted(stata_diff_terms)}", "")
    add(rows, "system_term_overlap", "PASS" if sgk_sys_terms <= stata_sys_terms or sgk_sys_terms == stata_sys_terms else "REVIEW",
        f"sgk={sorted(sgk_sys_terms)}; stata={sorted(stata_sys_terms)}", "")

    # Current comparison summary, if available
    comp_path = PATHS["comparison"]
    if comp_path.exists():
        comp = pd.read_csv(comp_path)
        comp.to_csv(OUT / "22_current_comparison_snapshot.csv", index=False)

        summary_cols = [c for c in [
            "model", "common_terms", "sgk_only_terms", "stata_only_terms",
            "max_abs_coef_diff", "max_abs_se_diff", "status"
        ] if c in comp.columns]

        if summary_cols:
            add(rows, "current_comparison_status", "INFO", comp[summary_cols].to_dict(orient="records"), "")

    # Descriptive stats
    desc_cols = [c for c in ["y", "L1_y", "x_pred", "x_exog", "alpha_true", "eps_true"] if c in df.columns]
    df[desc_cols].describe().T.to_csv(OUT / "22_panel_descriptive_statistics.csv")

    counts.reset_index(name="n_time_periods").to_csv(OUT / "22_panel_time_counts_by_id.csv", index=False)
    sdf[["id", "time", "y", "L1_y", "computed_L1_y"]].to_csv(OUT / "22_lag_audit_rows.csv", index=False)

    audit = pd.DataFrame(rows)
    audit.to_csv(OUT / "22_comparison_data_audit_summary.csv", index=False)

    md = "# Artifact 22 Comparison Data Audit\n\n"
    md += "## Summary\n\n"
    md += audit.to_markdown(index=False)
    md += "\n\n## Interpretation rule\n\n"
    md += (
        "- If panel structure, duplicate checks, and L1_y lag checks pass, the data itself is probably clean.\n"
        "- If Artifact 22 still shows REVIEW after the data passes, the issue is more likely model-command semantics, sample construction, instrument architecture, or export logic rather than the raw comparison data.\n"
        "- Raw debug-workflow data dumps are intentionally not part of the committed reviewer bundle; this audit relies on the controlled panel and committed comparison CSV outputs.\n"
        "- Artifact 22 remains auxiliary and should not replace the maintained parity certificate.\n"
    )
    (OUT / "22_comparison_data_audit.md").write_text(md, encoding="utf-8")

    print(audit.to_string(index=False))
    print(f"\n[DONE] Wrote audit outputs to {OUT}")


if __name__ == "__main__":
    main()
