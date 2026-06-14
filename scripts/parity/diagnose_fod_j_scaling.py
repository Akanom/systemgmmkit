from pathlib import Path
import pandas as pd
import math

OUT = Path("artifacts/parity/xtdpdgmm/fod_diff")
comp = pd.read_csv(OUT / "fod_diff_xtdpdgmm_native_diagnostics_comparison.csv")

j = comp[(comp["metric"] == "chi2_J") & comp["native"].notna()].copy()
j["stata_div_native"] = j["stata"] / j["native"]
j["native_times_groups_96"] = j["native"] * 96
j["native_times_effective_rows_1152"] = j["native"] * 1152
j["native_times_marked_sample_1248"] = j["native"] * 1248
j["native_times_df_2"] = j["native"] * 2
j["native_times_zrank_5"] = j["native"] * 5
j["native_times_rank_3"] = j["native"] * 3
j["native_times_6"] = j["native"] * 6
j["abs_diff_times_6"] = (j["native_times_6"] - j["stata"]).abs()

out_csv = OUT / "fod_diff_j_scaling_diagnostic.csv"
out_md = OUT / "fod_diff_j_scaling_diagnostic.md"

j.to_csv(out_csv, index=False)
out_md.write_text(j.to_markdown(index=False), encoding="utf-8")

print(j.to_string(index=False))
print(f"Wrote {out_csv}")
print(f"Wrote {out_md}")
