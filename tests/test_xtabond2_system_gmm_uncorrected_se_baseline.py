from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts" / "parity" / "xtabond2"

EXPECTED_PARAMS = ["L1.y", "x", "w", "_con"]


def _read_matrix(path: Path) -> np.ndarray:
    df = pd.read_csv(path)
    drop_cols = [c for c in df.columns if c.lower() in {"index", "row", "row_id"}]
    if drop_cols:
        df = df.drop(columns=drop_cols)
    return df.to_numpy(dtype=float)


@pytest.mark.parity
def test_native_system_gmm_uncorrected_clustered_se_baseline_vs_xtabond2() -> None:
    required = [
        ART / "system_gmm_benchmark.csv",
        ART / "stata_V.csv",
        ROOT / "scripts" / "parity" / "run_native_system_gmm_benchmark.py",
    ]

    missing = [p for p in required if not p.exists()]
    if missing:
        pytest.skip(
            "xtabond2 SE parity artifacts are unavailable: "
            + ", ".join(str(p) for p in missing)
        )

    env = os.environ.copy()
    env["SYSTEMGMMKIT_EXPORT_GMM_DEBUG"] = "1"
    env["SYSTEMGMMKIT_GMM_DEBUG_DIR"] = "artifacts/parity/xtabond2"
    env["SYSTEMGMMKIT_NATIVE_WINDMEIJER"] = "0"

    subprocess.run(
        [sys.executable, "scripts/parity/run_native_system_gmm_benchmark.py"],
        cwd=ROOT,
        env=env,
        check=True,
    )

    params_path = ART / "native_system_gmm_params.csv"
    diagnostics_path = ART / "native_system_gmm_diagnostics.csv"

    params = pd.read_csv(params_path)
    diagnostics = pd.read_csv(diagnostics_path)

    assert "native_std_err" in params.columns
    assert "native_covariance_type" in diagnostics.columns

    cov_type = str(diagnostics.loc[0, "native_covariance_type"])
    assert cov_type == "robust-clustered-two-step-uncorrected"

    stata_v = _read_matrix(ART / "stata_V.csv")
    stata_se = np.sqrt(np.maximum(np.diag(stata_v), 0.0))

    rows = []

    for i, param in enumerate(EXPECTED_PARAMS):
        match = params[params["param"].eq(param)]

        assert not match.empty, f"Missing native parameter: {param}"

        native_se = float(match.iloc[0]["native_std_err"])
        stata = float(stata_se[i])

        abs_diff = abs(native_se - stata)
        rel_diff = abs_diff / max(abs(stata), 1e-15)

        rows.append(
            {
                "param": param,
                "native_se": native_se,
                "stata_se": stata,
                "abs_diff": abs_diff,
                "rel_diff": rel_diff,
            }
        )

    out = pd.DataFrame(rows)

    max_rel = float(out["rel_diff"].max())
    mean_rel = float(out["rel_diff"].mean())

    # This is deliberately NOT a Windmeijer parity test.
    # It guards the corrected entity-level robust covariance baseline.
    # Current verified benchmark is approximately:
    #   max_rel_diff  ≈ 0.154
    #   mean_rel_diff ≈ 0.075
    assert max_rel < 0.20
    assert mean_rel < 0.10
