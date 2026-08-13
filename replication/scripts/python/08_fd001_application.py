"""Create FD001 application summary file for manuscript evidence map."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
PROC = ROOT / "data" / "processed" / "fd001_panel.csv"
REPORT = ROOT / "artifacts" / "jss" / "reproducibility" / "fd001_preprocessing_report.json"
RESULTS_COMPARISONS = ROOT / "results" / "comparisons"
RESULTS_COMPARISONS.mkdir(parents=True, exist_ok=True)
RESULTS_NORMALIZED = ROOT / "results" / "normalized"
RESULTS_NORMALIZED.mkdir(parents=True, exist_ok=True)


def main() -> int:
    if PROC.exists():
        frame = pd.read_csv(PROC)
        report = json.loads(REPORT.read_text(encoding="utf-8")) if REPORT.exists() else {}
        row = {
            "dataset": "data/processed/fd001_panel.csv",
            "n_rows": int(len(frame)),
            "n_units": int(frame["entity"].nunique()) if "entity" in frame.columns else 0,
            "n_periods": int(frame["time"].nunique()) if "time" in frame.columns else 0,
            "synthetic": report.get("source") == "synthetic",
            "source": report.get("source", "unknown"),
            "status": "PASS" if not frame.empty else "WARN",
        }
    else:
        row = {
            "dataset": "data/processed/fd001_panel.csv",
            "n_rows": 0,
            "n_units": 0,
            "n_periods": 0,
            "synthetic": True,
            "status": "MISSING",
        }

    pd.DataFrame([row]).to_csv(
        RESULTS_COMPARISONS / "fd001_application_summary.csv",
        index=False,
    )

    row["synthetic"] = bool(row["synthetic"])
    pd.DataFrame([row]).to_csv(RESULTS_NORMALIZED / "fd001_application_summary.csv", index=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
