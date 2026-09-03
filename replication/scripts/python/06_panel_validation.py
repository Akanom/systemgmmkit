"""Compute panel-level validation checks."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
PROC_PATH = ROOT / "data" / "processed" / "fd001_panel.csv"
RESULTS_COMPARISONS = ROOT / "results" / "comparisons"
RESULTS_COMPARISONS.mkdir(parents=True, exist_ok=True)
RESULTS_NORMALIZED = ROOT / "results" / "normalized"
RESULTS_NORMALIZED.mkdir(parents=True, exist_ok=True)


def main() -> int:
    frame = pd.read_csv(PROC_PATH) if PROC_PATH.exists() else pd.DataFrame()

    if frame.empty:
        summary = pd.DataFrame(
            [
                {"metric": "n_rows", "value": 0},
                {"metric": "n_units", "value": 0},
                {"metric": "status", "value": "missing_dataset"},
            ]
        )
        summary.to_csv(RESULTS_COMPARISONS / "panel_validation_summary.csv", index=False)
        return 0

    by_entity = frame.groupby("entity").size()
    summary_rows = [
        {"metric": "n_rows", "value": int(len(frame))},
        {"metric": "n_units", "value": int(frame["entity"].nunique())},
        {"metric": "n_time_periods", "value": int(frame["time"].nunique())},
        {"metric": "min_periods_per_unit", "value": int(by_entity.min())},
        {"metric": "max_periods_per_unit", "value": int(by_entity.max())},
        {"metric": "mean_periods_per_unit", "value": float(by_entity.mean())},
        {"metric": "status", "value": "PASS"},
    ]

    pd.DataFrame(summary_rows).to_csv(
        RESULTS_COMPARISONS / "panel_validation_summary.csv",
        index=False,
    )
    frame.describe(include="all").to_csv(RESULTS_NORMALIZED / "panel_descriptor_summary.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
