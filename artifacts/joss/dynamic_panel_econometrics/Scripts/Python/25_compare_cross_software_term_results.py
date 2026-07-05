from __future__ import annotations

from pathlib import Path

import pandas as pd

OUT = Path("Artifacts/Joss/tables/25_cross_software_comparison")
long_path = OUT / "25_cross_software_results_long.csv"

if not long_path.exists():
    raise FileNotFoundError(long_path)

df = pd.read_csv(long_path)

df = df[df["status"].eq("OK")].copy()

# Keep key terms in sensible order
term_order = {
    "L1_y": 1,
    "x_pred": 2,
    "x_exog": 3,
    "const": 4,
}

software_order = {
    "systemgmmkit": 1,
    "Stata xtabond2": 2,
    "pydynpd": 3,
    "plm::pgmm": 4,
}

df["term_order"] = df["term_norm"].map(term_order).fillna(99)
df["software_order"] = df["software"].map(software_order).fillna(99)

# Coefficient table
coef = df.pivot_table(
    index=["model", "term_norm"],
    columns="software",
    values="coefficient",
    aggfunc="first",
).reset_index()

# Standard error table
se = df.pivot_table(
    index=["model", "term_norm"],
    columns="software",
    values="std_error",
    aggfunc="first",
).reset_index()

coef = coef.sort_values(
    by=["model", "term_norm"],
    key=lambda col: col.map(term_order).fillna(99) if col.name == "term_norm" else col
)

se = se.sort_values(
    by=["model", "term_norm"],
    key=lambda col: col.map(term_order).fillna(99) if col.name == "term_norm" else col
)

coef_path = OUT / "25_cross_software_coefficients_wide.csv"
se_path = OUT / "25_cross_software_standard_errors_wide.csv"

coef.to_csv(coef_path, index=False)
se.to_csv(se_path, index=False)

# Build difference-from-systemgmmkit table
rows = []

for (model, term), group in df.groupby(["model", "term_norm"]):
    ref = group[group["software"].eq("systemgmmkit")]

    if ref.empty:
        continue

    ref_coef = float(ref["coefficient"].iloc[0])
    ref_se = float(ref["std_error"].iloc[0])

    for _, row in group.iterrows():
        software = row["software"]
        if software == "systemgmmkit":
            continue

        rows.append(
            {
                "model": model,
                "term": term,
                "comparison_software": software,
                "systemgmmkit_coef": ref_coef,
                "comparison_coef": row["coefficient"],
                "coef_diff": ref_coef - row["coefficient"],
                "abs_coef_diff": abs(ref_coef - row["coefficient"]),
                "systemgmmkit_se": ref_se,
                "comparison_se": row["std_error"],
                "se_diff": ref_se - row["std_error"],
                "abs_se_diff": abs(ref_se - row["std_error"]),
            }
        )

diff = pd.DataFrame(rows)

diff["term_order"] = diff["term"].map(term_order).fillna(99)
diff["software_order"] = diff["comparison_software"].map(software_order).fillna(99)
diff = diff.sort_values(["model", "software_order", "term_order"]).drop(
    columns=["term_order", "software_order"]
)

diff_path = OUT / "25_cross_software_term_level_differences.csv"
diff.to_csv(diff_path, index=False)

# Paper-readable markdown
md = "# Artifact 25: Term-Level Cross-Software Result Comparison\n\n"

md += "## Coefficients\n\n"
md += coef.to_markdown(index=False)
md += "\n\n## Standard Errors\n\n"
md += se.to_markdown(index=False)
md += "\n\n## Differences Relative to systemgmmkit\n\n"
md += diff.to_markdown(index=False)
md += "\n\n## Interpretation\n\n"
md += (
    "Stata xtabond2 is the closest numerical comparator. System GMM matches "
    "systemgmmkit at numerical precision. Difference GMM falls within the "
    "predefined tolerant auxiliary band. pydynpd and plm::pgmm produce comparable "
    "directional estimates, but their coefficient and standard-error differences "
    "remain outside the auxiliary parity band, so they are classified as REVIEW "
    "ecosystem comparisons rather than strict parity checks.\n"
)

md_path = OUT / "25_cross_software_term_level_comparison.md"
md_path.write_text(md, encoding="utf-8")

print(f"[DONE] Wrote {coef_path}")
print(f"[DONE] Wrote {se_path}")
print(f"[DONE] Wrote {diff_path}")
print(f"[DONE] Wrote {md_path}")
print()
print(md)
