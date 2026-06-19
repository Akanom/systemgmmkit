from pathlib import Path

import pandas as pd

OUT = Path("artifacts/parity/gmm_lag_windows_realdata_notime")
coef_path = OUT / "native_vs_stata_coef_comparison.csv"
diag_path = OUT / "native_vs_stata_diagnostics_comparison.csv"

if not coef_path.exists():
    raise SystemExit(f"Missing {coef_path}")

coef = pd.read_csv(coef_path)

summary = (
    coef.dropna(subset=["abs_coef_diff"])
    .groupby("model", as_index=False)
    .agg(
        max_abs_coef_diff=("abs_coef_diff", "max"),
        mean_abs_coef_diff=("abs_coef_diff", "mean"),
        max_abs_se_diff=("abs_se_diff", "max"),
        mean_abs_se_diff=("abs_se_diff", "mean"),
    )
)

print(summary.to_string(index=False))

status = (
    "PASS"
    if (summary["max_abs_coef_diff"].max() <= 1e-5 and summary["max_abs_se_diff"].max() <= 1e-4)
    else "NOT_CERTIFIED"
)

status_file = OUT / "custom_lag_native_parity_status.txt"
status_file.write_text(status + "\n", encoding="utf-8")

print(f"\nCustom lag native parity status: {status}")
print(f"Wrote {status_file}")
