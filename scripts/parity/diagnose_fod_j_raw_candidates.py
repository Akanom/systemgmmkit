import math
from pathlib import Path

import pandas as pd

OUT = Path("artifacts/parity/xtdpdgmm/fod_diff")

oracle = pd.read_csv(OUT / "fod_diff_xtdpdgmm_diagnostics_oracle.csv")

rows = []

for _, s in oracle.iterrows():
    spec = s["spec"]
    native_path = OUT / f"native_{spec}_diagnostics.csv"

    if not native_path.exists():
        continue

    ndf = pd.read_csv(native_path)
    if ndf.empty:
        continue

    n = ndf.iloc[0]

    native_j = pd.to_numeric(n.get("native_j_stat"), errors="coerce")
    native_groups = pd.to_numeric(n.get("native_n_groups"), errors="coerce")
    native_rank = pd.to_numeric(n.get("native_rank"), errors="coerce")
    native_zrank = pd.to_numeric(n.get("native_zrank"), errors="coerce")
    native_df = pd.to_numeric(n.get("native_df_J"), errors="coerce")

    if pd.isna(native_j):
        native_raw_est = math.nan
        small_scale = math.nan
    else:
        small_scale = (native_groups - native_rank) / native_groups
        native_raw_est = native_j / small_scale if small_scale > 0 else math.nan

    candidates = {
        "native_j_stored": native_j,
        "native_j_unscaled_est": native_raw_est,
        "native_j_stored_times_6": native_j * 6 if not pd.isna(native_j) else math.nan,
        "native_j_unscaled_times_6": native_raw_est * 6
        if not pd.isna(native_raw_est)
        else math.nan,
        "native_j_unscaled_times_zrank": native_raw_est * native_zrank
        if not pd.isna(native_raw_est)
        else math.nan,
        "native_j_unscaled_times_rank_plus_zrank_minus_df": (
            native_raw_est * (native_rank + native_zrank - native_df)
            if not pd.isna(native_raw_est) and not pd.isna(native_df)
            else math.nan
        ),
    }

    for name, val in candidates.items():
        rows.append(
            {
                "spec": spec,
                "candidate": name,
                "native_candidate": val,
                "stata_chi2_J": s["stata_chi2_J"],
                "abs_diff_chi2_J": abs(val - s["stata_chi2_J"]) if not pd.isna(val) else math.nan,
                "stata_chi2_J_u": s["stata_chi2_J_u"],
                "abs_diff_chi2_J_u": abs(val - s["stata_chi2_J_u"])
                if not pd.isna(val)
                else math.nan,
                "small_scale": small_scale,
                "native_j_stored": native_j,
                "native_j_unscaled_est": native_raw_est,
            }
        )

out = pd.DataFrame(rows)
out = out.sort_values(["spec", "abs_diff_chi2_J", "abs_diff_chi2_J_u"])

out_csv = OUT / "fod_diff_j_raw_candidate_diagnostic.csv"
out_md = OUT / "fod_diff_j_raw_candidate_diagnostic.md"

out.to_csv(out_csv, index=False)
out_md.write_text(out.to_markdown(index=False), encoding="utf-8")

print(out.to_string(index=False))
print(f"Wrote {out_csv}")
print(f"Wrote {out_md}")
