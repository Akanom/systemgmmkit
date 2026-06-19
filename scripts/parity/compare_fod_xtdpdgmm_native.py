from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

SPECS = [
    "fod_diff_endog_x_onestep",
    "fod_diff_endog_x_twostep",
    "fod_diff_predet_x_onestep",
    "fod_diff_predet_x_twostep",
]


def norm_term(x: object) -> str:
    s = str(x).strip()

    if ":" in s:
        s = s.split(":")[-1]

    replacements = {
        "L.y": "L1.y",
        "L1.y": "L1.y",
        "l1.y": "L1.y",
        "_cons": "_con",
    }

    return replacements.get(s, s)


def compare_spec(out_dir: Path, spec: str) -> pd.DataFrame:
    stata_path = out_dir / f"stata_{spec}.csv"
    native_path = out_dir / f"native_{spec}.csv"

    if not stata_path.exists():
        return pd.DataFrame(
            [
                {
                    "spec": spec,
                    "status": "MISSING_STATA",
                    "message": str(stata_path),
                }
            ]
        )

    if not native_path.exists():
        return pd.DataFrame(
            [
                {
                    "spec": spec,
                    "status": "MISSING_NATIVE",
                    "message": str(native_path),
                }
            ]
        )

    stata = pd.read_csv(stata_path)
    native = pd.read_csv(native_path)

    stata["term_norm"] = stata["term"].map(norm_term)
    native["term_norm"] = native["term"].map(norm_term)

    merged = stata.merge(
        native,
        on="term_norm",
        how="inner",
        suffixes=("_stata", "_native"),
    )

    if merged.empty:
        return pd.DataFrame(
            [
                {
                    "spec": spec,
                    "status": "NO_MATCHED_TERMS",
                    "message": "No common coefficient names between Stata and native outputs.",
                }
            ]
        )

    merged["coef_abs_diff"] = (
        pd.to_numeric(merged["stata_coef"], errors="coerce")
        - pd.to_numeric(merged["native_coef"], errors="coerce")
    ).abs()

    if "stata_std_err" in merged.columns and "native_std_err" in merged.columns:
        merged["se_abs_diff"] = (
            pd.to_numeric(merged["stata_std_err"], errors="coerce")
            - pd.to_numeric(merged["native_std_err"], errors="coerce")
        ).abs()
    else:
        merged["se_abs_diff"] = pd.NA

    merged["spec"] = spec
    merged["status"] = "COMPARED"

    keep = [
        "spec",
        "status",
        "term_norm",
        "term_stata",
        "term_native",
        "stata_coef",
        "native_coef",
        "coef_abs_diff",
        "stata_std_err",
        "native_std_err",
        "se_abs_diff",
    ]

    for col in keep:
        if col not in merged.columns:
            merged[col] = pd.NA

    detail_path = out_dir / f"comparison_{spec}.csv"
    merged[keep].to_csv(detail_path, index=False)

    return merged[keep]


def summarize(result: pd.DataFrame) -> pd.DataFrame:
    rows = []

    for spec, g in result.groupby("spec", dropna=False):
        status_values = set(g["status"].dropna().astype(str))

        if "COMPARED" not in status_values:
            rows.append(
                {
                    "spec": spec,
                    "status": next(iter(status_values), "FAILED"),
                    "matched_terms": 0,
                    "max_abs_coef_diff": pd.NA,
                    "mean_abs_coef_diff": pd.NA,
                    "max_abs_se_diff": pd.NA,
                    "mean_abs_se_diff": pd.NA,
                    "message": g.get("message", pd.Series([""])).iloc[0],
                }
            )
            continue

        coef = pd.to_numeric(g["coef_abs_diff"], errors="coerce")
        se = pd.to_numeric(g["se_abs_diff"], errors="coerce")

        rows.append(
            {
                "spec": spec,
                "status": "COMPARED",
                "matched_terms": int(g["term_norm"].nunique()),
                "max_abs_coef_diff": coef.max(),
                "mean_abs_coef_diff": coef.mean(),
                "max_abs_se_diff": se.max(),
                "mean_abs_se_diff": se.mean(),
                "message": "",
            }
        )

    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()

    out_dir = Path(args.out_dir)

    frames = [compare_spec(out_dir, spec) for spec in SPECS]
    result = pd.concat(frames, ignore_index=True)

    detail_path = out_dir / "fod_diff_xtdpdgmm_native_comparison.csv"
    result.to_csv(detail_path, index=False)

    summary = summarize(result)
    summary_path = out_dir / "fod_diff_xtdpdgmm_native_summary.csv"
    summary_md_path = out_dir / "fod_diff_xtdpdgmm_native_summary.md"

    summary.to_csv(summary_path, index=False)
    summary_md_path.write_text(summary.to_markdown(index=False), encoding="utf-8")

    print(f"Wrote {detail_path}")
    print(f"Wrote {summary_path}")
    print(f"Wrote {summary_md_path}")
    print()
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
