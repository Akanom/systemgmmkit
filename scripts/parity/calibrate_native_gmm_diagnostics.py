from __future__ import annotations

from pathlib import Path

import pandas as pd
from scipy import stats

OUT = Path("artifacts/parity/xtabond2")

diag = pd.read_csv(OUT / "xtabond2_native_system_gmm_diagnostics_comparison.csv")

row = diag.iloc[0].to_dict()

native = {
    "hansen_p": row.get("native_hansen_p"),
    "ar1_p": row.get("native_ar1_p"),
    "ar2_p": row.get("native_ar2_p"),
}

stata = {
    "hansen_p": row.get("stata_hansen_p"),
    "sargan_p": row.get("stata_sargan_p"),
    "ar1_p": row.get("stata_ar1_p"),
    "ar2_p": row.get("stata_ar2_p"),
}

records = []

# Hansen/Sargan implied chi-square with df=1 from Stata output
for name in ["hansen_p", "sargan_p"]:
    p = stata.get(name)
    if pd.notna(p):
        records.append(
            {
                "diagnostic": name,
                "source": "xtabond2",
                "p_value": p,
                "implied_stat_df1": stats.chi2.isf(float(p), 1),
            }
        )

# Native Hansen
if pd.notna(native["hansen_p"]):
    records.append(
        {
            "diagnostic": "hansen_p",
            "source": "native",
            "p_value": native["hansen_p"],
            "implied_stat_df1": stats.chi2.isf(float(native["hansen_p"]), 1),
        }
    )

# AR tests implied absolute z-stat
for name in ["ar1_p", "ar2_p"]:
    for source, values in [("native", native), ("xtabond2", stata)]:
        p = values.get(name)
        if pd.notna(p):
            records.append(
                {
                    "diagnostic": name,
                    "source": source,
                    "p_value": p,
                    "implied_abs_z": stats.norm.isf(float(p) / 2.0),
                }
            )

out = pd.DataFrame(records)
out.to_csv(OUT / "native_gmm_diagnostic_calibration.csv", index=False)

md = []
md.append("# Native GMM Diagnostic Calibration")
md.append("")
md.append(
    "This file compares native experimental diagnostic p-values against xtabond2 implied statistics."
)
md.append("")
md.append("## Calibration Table")
md.append("")
md.append(out.to_markdown(index=False))
md.append("")
md.append("## Interpretation")
md.append("")
md.append("- Nobs and instrument-count parity are already achieved.")
md.append("- Native AR(2) is directionally close to xtabond2.")
md.append("- Native AR(1) and Hansen are not parity-calibrated.")
md.append(
    "- Coefficient and diagnostic parity should not be claimed until the weighting matrix and residual moment tests are aligned with xtabond2."
)

(OUT / "native_gmm_diagnostic_calibration.md").write_text("\n".join(md), encoding="utf-8")

print(out)
print(f"Wrote {OUT / 'native_gmm_diagnostic_calibration.csv'}")
print(f"Wrote {OUT / 'native_gmm_diagnostic_calibration.md'}")
