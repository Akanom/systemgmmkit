import json
import subprocess
import sys
from pathlib import Path


def test_ml_workflow_smoke_script_runs(tmp_path):
    outdir = tmp_path / "ml_workflow"

    completed = subprocess.run(
        [
            sys.executable,
            "scripts/ml/run_ml_workflow_smoke.py",
            "--outdir",
            str(outdir),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "PASS" in completed.stdout

    expected = [
        "static_panel.csv",
        "dynamic_panel.csv",
        "ols_predictions_residuals.csv",
        "panel_cv_scores.csv",
        "model_comparison.csv",
        "gmm_grid_search.csv",
        "forecast.csv",
        "forecast_backtest.csv",
        "summary.json",
        "README.md",
    ]

    for name in expected:
        assert (outdir / name).exists(), name

    summary = json.loads((outdir / "summary.json").read_text(encoding="utf-8"))
    assert summary["status"] == "PASS"
    assert summary["row_counts"]["model_comparison"] == 2
    assert summary["row_counts"]["gmm_grid_search"] == 3
