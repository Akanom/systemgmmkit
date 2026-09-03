"""Compare the JSS ML/search workflow with external Python predictive baselines.

This is predictive benchmark evidence, not estimator or causal parity. Stata
``xtabond2`` remains the comparator for the Dynamic GMM estimators themselves.
"""

from __future__ import annotations

import importlib.metadata
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

ROOT = Path(__file__).resolve().parents[3]
DATA_PATH = ROOT / "data" / "synthetic" / "22_dynamic_gmm_controlled_panel.csv"
SEARCH_PATH = ROOT / "results" / "comparisons" / "auto_gmm_search_results.csv"
SEARCH_STATUS_PATH = ROOT / "results" / "comparisons" / "auto_gmm_search_status.json"
RESULTS_DIR = ROOT / "results" / "comparisons"
ARTIFACT_DIR = ROOT / "artifacts" / "jss" / "tables"
SEED = 20260724


def _metrics(y_true: pd.Series, prediction: np.ndarray) -> dict[str, float]:
    return {
        "rmse": float(np.sqrt(mean_squared_error(y_true, prediction))),
        "mae": float(mean_absolute_error(y_true, prediction)),
        "r2": float(r2_score(y_true, prediction)),
    }


def main() -> int:
    if not DATA_PATH.exists() or not SEARCH_PATH.exists() or not SEARCH_STATUS_PATH.exists():
        raise FileNotFoundError("Run 10_controlled_dynamic_gmm.py and 11_auto_gmm_search.py first.")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    data = pd.read_csv(DATA_PATH).dropna(subset=["y", "L1_y", "x_pred", "x_exog"])
    final_periods = sorted(data["time"].unique())[-2:]
    train = data.loc[~data["time"].isin(final_periods)].copy()
    test = data.loc[data["time"].isin(final_periods)].copy()
    features = ["L1_y", "x_pred", "x_exog"]

    rows: list[dict[str, object]] = []

    started = time.perf_counter()
    ols = sm.OLS(train["y"], sm.add_constant(train[features], has_constant="add")).fit()
    ols_prediction = np.asarray(
        ols.predict(sm.add_constant(test[features], has_constant="add")), dtype=float
    )
    rows.append(
        {
            "model": "statsmodels OLS",
            "package": "statsmodels",
            "package_version": importlib.metadata.version("statsmodels"),
            "comparison_role": "predictive_baseline",
            **_metrics(test["y"], ols_prediction),
            "elapsed_seconds": time.perf_counter() - started,
            "diagnostics_applicable": False,
            "claim_boundary": "Predictive baseline; not a Dynamic GMM parity test.",
        }
    )

    started = time.perf_counter()
    forest = RandomForestRegressor(
        n_estimators=300,
        min_samples_leaf=2,
        random_state=SEED,
        n_jobs=1,
    ).fit(train[features], train["y"])
    forest_prediction = forest.predict(test[features])
    rows.append(
        {
            "model": "scikit-learn random forest",
            "package": "scikit-learn",
            "package_version": importlib.metadata.version("scikit-learn"),
            "comparison_role": "predictive_baseline",
            **_metrics(test["y"], forest_prediction),
            "elapsed_seconds": time.perf_counter() - started,
            "diagnostics_applicable": False,
            "claim_boundary": "Predictive baseline; not a Dynamic GMM parity test.",
        }
    )

    search = pd.read_csv(SEARCH_PATH)
    search_status = json.loads(SEARCH_STATUS_PATH.read_text(encoding="utf-8"))
    best_id = int(search_status["best_candidate_id"])
    best = search.loc[search["candidate_id"].astype(int).eq(best_id)]
    if len(best) != 1:
        raise RuntimeError(f"Expected one selected GMM candidate; found {len(best)}.")
    best_row = best.iloc[0]
    rows.append(
        {
            "model": f"systemgmmkit {best_row['estimator']} {best_row['lag_window']}",
            "package": "systemgmmkit",
            "package_version": "1.0.0",
            "comparison_role": "diagnostic_gated_econometric_search",
            "rmse": float(best_row["rmse"]),
            "mae": np.nan,
            "r2": float(best_row["r2"]),
            "elapsed_seconds": float(search_status["elapsed_seconds"]),
            "diagnostics_applicable": True,
            "claim_boundary": (
                "Selected only after GMM diagnostics; predictive metrics do not prove "
                "causal identification."
            ),
        }
    )

    result = pd.DataFrame(rows)
    if not np.isfinite(result[["rmse", "r2"]].to_numpy(dtype=float)).all():
        raise RuntimeError("External Python comparison produced non-finite required metrics.")

    result_path = RESULTS_DIR / "ml_external_python_comparison.csv"
    artifact_path = ARTIFACT_DIR / "24_ml_external_python_comparison.csv"
    result.to_csv(result_path, index=False)
    result.to_csv(artifact_path, index=False)

    status = {
        "status": "PASS",
        "generated_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "seed": SEED,
        "train_periods": sorted(int(value) for value in train["time"].unique()),
        "test_periods": [int(value) for value in final_periods],
        "train_rows": int(len(train)),
        "test_rows": int(len(test)),
        "packages": sorted(result["package"].unique().tolist()),
        "claim_boundary": (
            "The external rows compare prediction on the same temporal split. They are "
            "not substitutes for Stata xtabond2 estimator parity."
        ),
    }
    status_path = RESULTS_DIR / "ml_external_python_comparison_status.json"
    status_path.write_text(json.dumps(status, indent=2), encoding="utf-8")
    (ARTIFACT_DIR / "24_ml_external_python_comparison_status.json").write_text(
        json.dumps(status, indent=2), encoding="utf-8"
    )
    print(json.dumps(status, indent=2))
    print(result.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
