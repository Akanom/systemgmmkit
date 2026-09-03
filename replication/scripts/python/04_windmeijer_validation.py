"""Build Windmeijer / diagnostic summary from dynamic GMM health metrics."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
ART_TABLES = ROOT / "artifacts" / "joss" / "tables"
RESULTS_COMPARISONS = ROOT / "results" / "comparisons"
RESULTS_NORMALIZED = ROOT / "results" / "normalized"
RESULTS_NORMALIZED.mkdir(parents=True, exist_ok=True)
RESULTS_COMPARISONS.mkdir(parents=True, exist_ok=True)


def main() -> int:
    health_path = ART_TABLES / "22_dynamic_gmm_health_metrics.csv"
    if health_path.exists():
        health = pd.read_csv(health_path)
    else:
        health = pd.DataFrame(
            [
                {
                    "estimator": "system",
                    "covariance_type": "unknown",
                    "hansen_p": None,
                    "sargan_p": None,
                    "ar1_p": None,
                    "ar2_p": None,
                }
            ]
        )

    rows = []
    for _, row in health.iterrows():
        cov = row.get("covariance_type", "unknown")
        status = "PASS"
        if str(cov).lower() in {"unknown", "", "none", "nan"}:
            status = "WARN"
        rows.append(
            {
                "model": str(row.get("estimator", "model")),
                "covariance_type": str(cov),
                "hansen_p": row.get("hansen_p"),
                "sargan_p": row.get("sargan_p"),
                "ar1_p": row.get("ar1_p"),
                "ar2_p": row.get("ar2_p"),
                "status": status,
            }
        )

    pd.DataFrame(rows).to_csv(
        RESULTS_COMPARISONS / "windmeijer_validation.csv",
        index=False,
    )

    health.to_csv(RESULTS_NORMALIZED / "dynamic_gmm_health_metrics.csv", index=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
