"""Normalize and summarise Difference GMM artifacts."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
ART_TABLES = ROOT / "artifacts" / "joss" / "tables"
RESULTS_NORMALIZED = ROOT / "results" / "normalized"
RESULTS_COMPARISONS = ROOT / "results" / "comparisons"
RESULTS_NORMALIZED.mkdir(parents=True, exist_ok=True)
RESULTS_COMPARISONS.mkdir(parents=True, exist_ok=True)


def _safe_read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def main() -> int:
    diff = _safe_read_csv(ART_TABLES / "22_difference_gmm_results.csv")
    if not diff.empty:
        diff.to_csv(RESULTS_NORMALIZED / "difference_gmm_results.csv", index=False)

    summary_rows = []
    if diff.empty:
        summary_rows.append({"model": "Difference GMM", "status": "MISSING"})
    else:
        for model in sorted(diff["model"].dropna().unique()):
            subset = diff[diff["model"] == model]
            status = "PASS" if subset["coefficient"].notna().all() else "WARN"
            summary_rows.append({"model": str(model), "status": status})

    pd.DataFrame(summary_rows).to_csv(
        RESULTS_COMPARISONS / "difference_gmm_validation_summary.csv",
        index=False,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
