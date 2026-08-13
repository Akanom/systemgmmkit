"""Run the manuscript's diagnostic-first automatic Dynamic GMM search."""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

import systemgmmkit as sgk
from systemgmmkit.ml import auto_dynamic_gmm

ROOT = Path(__file__).resolve().parents[3]
DATA_PATH = ROOT / "data" / "synthetic" / "22_dynamic_gmm_controlled_panel.csv"
RESULTS_DIR = ROOT / "results" / "comparisons"
ARTIFACT_DIR = ROOT / "artifacts" / "jss" / "tables"
VERSION = "1.0.0"
SEED = 20260724


def _optional_column(frame: pd.DataFrame, name: str) -> pd.Series:
    if name in frame:
        return frame[name]
    return pd.Series([pd.NA] * len(frame), index=frame.index)


def main() -> int:
    if getattr(sgk, "__version__", "unknown") != VERSION:
        raise RuntimeError(f"Automatic search requires systemgmmkit {VERSION}.")
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            "Controlled panel is missing. Run 10_controlled_dynamic_gmm.py first."
        )

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    data = pd.read_csv(DATA_PATH)

    started = time.perf_counter()
    search = auto_dynamic_gmm(
        data,
        y="y",
        entity="id",
        time="time",
        regressors=["x_pred", "x_exog"],
        predetermined=["x_pred"],
        exogenous=["x_exog"],
        test_size=2,
        models=("system", "difference"),
        steps=("twostep",),
        lag_windows=((2, 2), (2, 3)),
        transformations=("fd",),
        collapse_options=(True,),
        windmeijer_options=(True,),
        time_effects_options=(False,),
        backend_options=("native",),
        predict_kwargs={"strict": False},
    )
    elapsed = time.perf_counter() - started

    raw = search.results.copy()
    if len(raw) != 4:
        raise RuntimeError(f"Expected four automatic-search candidates; found {len(raw)}.")

    normalized = pd.DataFrame(
        {
            "candidate_id": raw["spec_id"].astype(int),
            "estimator": raw["model"].str.title() + " GMM",
            "lag_window": raw["gmm_lags"].map(lambda value: f"{int(value[0])}:{int(value[1])}"),
            "valid": raw["passes_diagnostics"].astype(bool),
            "rmse": pd.to_numeric(raw["rmse"], errors="coerce"),
            "r2": pd.to_numeric(raw["r2"], errors="coerce"),
            "hansen_p": pd.to_numeric(_optional_column(raw, "diag_hansen_p"), errors="coerce"),
            "ar2_p": pd.to_numeric(_optional_column(raw, "diag_ar2_p"), errors="coerce"),
            "n_instruments": pd.to_numeric(
                _optional_column(raw, "diag_n_instruments"), errors="coerce"
            ).astype("Int64"),
            "rank_score": pd.to_numeric(raw["rank_score"], errors="coerce"),
            "rejection_reason": raw["rejection_reason"].fillna(""),
        }
    )
    if normalized["rmse"].isna().any() or normalized["r2"].isna().any():
        raise RuntimeError("Automatic search returned missing holdout metrics.")
    if not normalized["valid"].any() or search.best_spec is None:
        raise RuntimeError("Automatic search found no diagnostically admissible candidate.")

    csv_path = RESULTS_DIR / "auto_gmm_search_results.csv"
    normalized.to_csv(csv_path, index=False)
    normalized.to_csv(ARTIFACT_DIR / "23_auto_gmm_search_results.csv", index=False)

    status = {
        "status": "PASS",
        "generated_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "seed": SEED,
        "systemgmmkit_version": VERSION,
        "dataset": str(DATA_PATH.relative_to(ROOT)).replace("\\", "/"),
        "candidate_count": int(len(normalized)),
        "valid_candidate_count": int(normalized["valid"].sum()),
        "elapsed_seconds": elapsed,
        "best_spec": search.best_spec,
        "best_candidate_id": int(search.best_row["spec_id"]),
        "selection_metric": search.selection_metric,
        "claim_boundary": (
            "Diagnostics filter candidates before predictive ranking; selection "
            "does not establish causal identification or instrument validity."
        ),
    }
    (RESULTS_DIR / "auto_gmm_search_status.json").write_text(
        json.dumps(status, indent=2), encoding="utf-8"
    )
    (ARTIFACT_DIR / "23_auto_gmm_search_status.json").write_text(
        json.dumps(status, indent=2), encoding="utf-8"
    )
    print(json.dumps(status, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
