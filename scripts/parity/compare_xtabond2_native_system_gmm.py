from __future__ import annotations

from pathlib import Path

import pandas as pd


OUT = Path("artifacts/parity/xtabond2")


def main() -> None:
    native_params_path = OUT / "native_system_gmm_params.csv"
    stata_params_path = OUT / "xtabond2_system_gmm_params.csv"
    native_diag_path = OUT / "native_system_gmm_diagnostics.csv"
    stata_diag_path = OUT / "xtabond2_system_gmm_diagnostics.csv"

    native_params = pd.read_csv(native_params_path)

    if stata_params_path.exists():
        stata_params = pd.read_csv(stata_params_path)
    else:
        stata_params = pd.DataFrame(columns=["parm", "estimate"])

    if not stata_params.empty:
        compare = native_params.merge(
            stata_params,
            left_on="param",
            right_on="parm",
            how="outer",
        )
        if "estimate" in compare.columns:
            compare["abs_coef_diff"] = (compare["native_coef"] - compare["estimate"]).abs()
    else:
        compare = native_params.copy()
        compare["stata_coef"] = None
        compare["abs_coef_diff"] = None

    compare.to_csv(OUT / "xtabond2_native_system_gmm_coef_comparison.csv", index=False)

    native_diag = pd.read_csv(native_diag_path)

    if stata_diag_path.exists():
        stata_diag = pd.read_csv(stata_diag_path)
        diag = pd.concat([native_diag, stata_diag], axis=1)
    else:
        diag = native_diag.copy()
        diag["stata_status"] = "PENDING_RUN_STATA_DOFILE"

    diag.to_csv(OUT / "xtabond2_native_system_gmm_diagnostics_comparison.csv", index=False)

    md = []
    md.append("# xtabond2 vs Native System GMM Parity")
    md.append("")
    md.append("## Status")
    md.append("")
    if stata_diag_path.exists() and stata_params_path.exists():
        md.append("Stata xtabond2 outputs detected. Comparison generated.")
    else:
        md.append("Native outputs generated. Stata xtabond2 outputs pending. Run the generated `.do` file in Stata.")
    md.append("")
    md.append("## Files")
    md.append("")
    md.append("- `system_gmm_benchmark.csv`")
    md.append("- `system_gmm_xtabond2_parity.do`")
    md.append("- `native_system_gmm_params.csv`")
    md.append("- `native_system_gmm_diagnostics.csv`")
    md.append("- `xtabond2_native_system_gmm_coef_comparison.csv`")
    md.append("- `xtabond2_native_system_gmm_diagnostics_comparison.csv`")
    md.append("")

    (OUT / "xtabond2_native_system_gmm_parity.md").write_text("\n".join(md), encoding="utf-8")

    print(f"Wrote comparison outputs to {OUT}")


if __name__ == "__main__":
    main()
