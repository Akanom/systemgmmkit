from __future__ import annotations

from pathlib import Path

import pandas as pd

OUT = Path("artifacts/parity/xtabond2")

native = pd.read_csv(OUT / "native_stata_matrix_comparison.csv")
stata_diag = pd.read_csv(OUT / "xtabond2_internal_diagnostics.csv")

row = native[native["object"] == "native_result"].iloc[0]
target_j = float(stata_diag.iloc[0]["stata_hansen"])

native_j = float(row["native_j_stat"])
native_w_norm = float(row["native_w_norm"])
stata_a2_norm = float(native[native["object"] == "stata_A2"].iloc[0]["frobenius_norm"])

scales = {
    "none": 1.0,
    "divide_by_nobs_1248": 1.0 / 1248.0,
    "divide_by_groups_96": 1.0 / 96.0,
    "divide_by_stacked_rows_2400": 1.0 / 2400.0,
    "match_A2_norm": stata_a2_norm / native_w_norm,
    "match_target_J": target_j / native_j,
}

rows = []

for name, scale in scales.items():
    j_scaled = native_j * scale
    rows.append(
        {
            "scale_name": name,
            "scale": scale,
            "scaled_j": j_scaled,
            "target_xtabond2_hansen": target_j,
            "abs_diff": abs(j_scaled - target_j),
        }
    )

out = pd.DataFrame(rows).sort_values("abs_diff")
out.to_csv(OUT / "gmm_weight_scaling_candidates.csv", index=False)

md = []
md.append("# GMM Weight Scaling Candidate Test")
md.append("")
md.append(f"Native J-stat: `{native_j}`")
md.append(f"xtabond2 Hansen statistic: `{target_j}`")
md.append(f"Native W norm: `{native_w_norm}`")
md.append(f"xtabond2 A2 norm: `{stata_a2_norm}`")
md.append("")
md.append(out.to_markdown(index=False))
md.append("")
md.append("## Interpretation")
md.append("")
md.append("- This tests scalar normalization only.")
md.append(
    "- If `match_A2_norm` is close to `match_target_J`, the problem is mostly scalar normalization."
)
md.append(
    "- If not, the problem is matrix construction, residual moment aggregation, or equation stacking."
)

(OUT / "gmm_weight_scaling_candidates.md").write_text("\n".join(md), encoding="utf-8")

print(out.to_string(index=False))
print(f"Wrote {OUT / 'gmm_weight_scaling_candidates.csv'}")
print(f"Wrote {OUT / 'gmm_weight_scaling_candidates.md'}")
