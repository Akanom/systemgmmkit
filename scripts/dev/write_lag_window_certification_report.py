from pathlib import Path
import pandas as pd

OUT = Path("artifacts/parity/gmm_lag_windows_realdata_notime")
REPORT = Path("artifacts/parity/gmm_lag_windows_realdata_notime/lag_window_certification_report.md")

coef_path = OUT / "native_vs_stata_coef_comparison.csv"
diag_path = OUT / "native_vs_stata_diagnostics_comparison.csv"

coef = pd.read_csv(coef_path) if coef_path.exists() else pd.DataFrame()
diag = pd.read_csv(diag_path) if diag_path.exists() else pd.DataFrame()

lines = []

lines.append("# GMM Lag-Window Certification Report")
lines.append("")
lines.append("## Scope")
lines.append("")
lines.append("This report validates the role-specific and variable-specific GMM lag-window API.")
lines.append("")
lines.append("The validation covers:")
lines.append("")
lines.append("- global GMM lag windows via `gmm_lags`")
lines.append("- role-specific lag windows via `gmm_lags_by_role`")
lines.append("- variable-specific lag windows via `gmm_lags_by_variable`")
lines.append("- backward-compatible default lag behavior")
lines.append("- manual xtabond2 execution on existing benchmark data")
lines.append("- overidentification degrees-of-freedom recovery blocker")
lines.append("")
lines.append("## Certification Status")
lines.append("")
lines.append("| Layer | Status | Interpretation |")
lines.append("|---|---|---|")
lines.append("| Public API | PASS | New arguments are accepted and translated into internal GMM lag windows. |")
lines.append("| Backward compatibility | PASS | Baseline dependent lag default remains `(2, 3)` while other GMM variables retain `(2, 2)`. |")
lines.append("| Stata command generation | PASS | Generated `xtabond2` commands contain the expected `gmmstyle(... lag(a b) collapse)` blocks. |")
lines.append("| Manual Stata real-data execution | PASS | The generated commands run on the existing benchmark data. |")
lines.append("| Overidentification df blocker | PASS | Execution blocks if Hansen/Sargan df cannot be recovered. Real-data run recovered df successfully. |")
lines.append("| Native-vs-xtabond2 parity for custom lag windows | NOT CERTIFIED | Native System GMM remains experimental for these custom lag-window specifications. |")
lines.append("")
lines.append("## Real-Data Stata Diagnostics")
lines.append("")

diag_sources = []
for name in ["m_base", "m_role", "m_var"]:
    dfile = Path("artifacts/parity/gmm_lag_windows_realdata") / f"{name}_diagnostics.csv"
    if dfile.exists():
        row = pd.read_csv(dfile).iloc[0].to_dict()
        diag_sources.append(row)

if diag_sources:
    d = pd.DataFrame(diag_sources)
    keep = [
        "model",
        "N",
        "N_g",
        "k_instruments",
        "k_params",
        "overid_df",
        "overid_df_source",
        "hansen_p",
        "sargan_p",
        "ar1_p",
        "ar2_p",
    ]
    keep = [c for c in keep if c in d.columns]
    lines.append(d[keep].to_markdown(index=False))
else:
    lines.append("No real-data Stata diagnostics file found.")

lines.append("")
lines.append("## Native-vs-Stata No-Time-Dummy Comparison")
lines.append("")
lines.append("The no-time-dummy comparison was run to remove structural time-dummy contamination. Material coefficient gaps remain; therefore native-vs-xtabond2 parity is not certified for these new custom lag-window specifications.")
lines.append("")

if not coef.empty:
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
    lines.append(summary.to_markdown(index=False))
else:
    lines.append("No native-vs-Stata coefficient comparison file found.")

lines.append("")
lines.append("## Decision")
lines.append("")
lines.append("This feature is accepted as an API/specification and Stata command-generation enhancement.")
lines.append("")
lines.append("It must not be described as native System GMM parity for custom lag-window specifications until the native backend is separately certified against xtabond2 for these exact specifications.")
lines.append("")
lines.append("## Follow-up Backlog")
lines.append("")
lines.append("1. Align native instrument counting with xtabond2 for custom lag-window specifications.")
lines.append("2. Confirm whether the native backend applies `spec.gmm` lag windows identically across difference and level equations.")
lines.append("3. Extract Hansen/Sargan diagnostics from native results consistently.")
lines.append("4. Re-run native-vs-xtabond2 parity after backend alignment.")
lines.append("")

REPORT.write_text("\n".join(lines), encoding="utf-8")
print(f"Wrote {REPORT}")
