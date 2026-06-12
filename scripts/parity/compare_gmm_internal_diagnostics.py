from __future__ import annotations

from pathlib import Path

import pandas as pd

OUT = Path("artifacts/parity/xtabond2")


def main() -> None:
    native_path = OUT / "native_gmm_internal_diagnostics.csv"
    stata_path = OUT / "xtabond2_internal_diagnostics.csv"

    native = pd.read_csv(native_path)

    if stata_path.exists():
        stata = pd.read_csv(stata_path)
        comparison = pd.concat([native, stata], axis=1)
    else:
        comparison = native.copy()
        comparison["stata_status"] = "PENDING_RUN_EXPORT_XTABOND2_INTERNALS_DO"

    comparison.to_csv(OUT / "gmm_internal_diagnostics_comparison.csv", index=False)

    md = ["# GMM Internal Diagnostics Comparison", ""]
    md.append("## Native")
    md.append("")
    md.append(native.to_markdown(index=False))
    md.append("")

    if stata_path.exists():
        md.append("## xtabond2")
        md.append("")
        md.append(stata.to_markdown(index=False))
    else:
        md.append("## xtabond2")
        md.append("")
        md.append("Pending. Run `artifacts/parity/xtabond2/export_xtabond2_internals.do` in Stata.")

    (OUT / "gmm_internal_diagnostics_comparison.md").write_text("\n".join(md), encoding="utf-8")

    print(f"Wrote {OUT / 'gmm_internal_diagnostics_comparison.csv'}")
    print(f"Wrote {OUT / 'gmm_internal_diagnostics_comparison.md'}")


if __name__ == "__main__":
    main()
