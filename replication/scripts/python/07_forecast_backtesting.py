"""Create forecast/benchmark summary used by manuscript backtesting row."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
ART_TABLES = ROOT / "artifacts" / "joss" / "tables" / "28_performance_benchmarks"
RESULTS_COMPARISONS = ROOT / "results" / "comparisons"
RESULTS_COMPARISONS.mkdir(parents=True, exist_ok=True)


def main() -> int:
    source = ART_TABLES / "28_dynamic_gmm_performance_summary.csv"
    if source.exists():
        perf = pd.read_csv(source)
        rows = []
        for _, row in perf.iterrows():
            rows.append(
                {
                    "section": str(row.get("benchmark", "dynamic_gmm")),
                    "dataset": str(row.get("size_label", "all")),
                    "backend": str(row.get("backend", "native")),
                    "status": "PASS"
                    if row.get("status", "OK") == "OK"
                    else row.get("status", "WARN"),
                    "mean_seconds": row.get("mean_seconds", 0.0),
                    "n_rows": row.get("n_rows", 0),
                }
            )
    else:
        rows = [
            {
                "section": "dynamic_gmm",
                "dataset": "fallback",
                "backend": "native",
                "status": "MISSING",
                "mean_seconds": 0.0,
                "n_rows": 0,
            }
        ]

    pd.DataFrame(rows).to_csv(
        RESULTS_COMPARISONS / "forecast_backtesting_summary.csv",
        index=False,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
