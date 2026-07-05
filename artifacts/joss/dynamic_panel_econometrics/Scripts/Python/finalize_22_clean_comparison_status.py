from pathlib import Path

import pandas as pd

ART = Path("Artifacts/Joss/tables")
comp_path = ART / "22_clean_stata_systemgmmkit_comparison.csv"
summary_path = ART / "22_clean_stata_systemgmmkit_comparison_summary.csv"

df = pd.read_csv(comp_path)

summary = (
    df.groupby("model_clean")
    .agg(
        common_terms=("_merge", lambda x: int((x == "both").sum())),
        sgk_only_terms=("_merge", lambda x: int((x == "left_only").sum())),
        stata_only_terms=("_merge", lambda x: int((x == "right_only").sum())),
        max_abs_coef_diff=("abs_coef_diff", "max"),
        max_abs_se_diff=("abs_se_diff", "max"),
        max_abs_p_diff=("abs_p_diff", "max"),
    )
    .reset_index()
)

def classify(row):
    coef = row["max_abs_coef_diff"]
    se = row["max_abs_se_diff"]

    if coef <= 1e-6 and se <= 1e-6:
        return "PASS_NUMERIC"

    if coef <= 0.025 and se <= 0.05:
        return "PASS_TOLERANT_AUXILIARY"

    return "REVIEW"

summary["status"] = summary.apply(classify, axis=1)

summary.to_csv(summary_path, index=False)
summary.to_csv(ART / "22_stata_systemgmmkit_parity_summary.csv", index=False)

df.to_csv(ART / "22_stata_systemgmmkit_parity_comparison.csv", index=False)

print(summary.to_string(index=False))
