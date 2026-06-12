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

XTABOND2_HANSEN = 6.577371156435732

ORDER_NATIVE_TO_STATA = [4, 7, 0, 2, 1, 3, 5, 6]


def _read_matrix(path: Path) -> np.ndarray:
    df = pd.read_csv(path)

    drop_cols = [
        c for c in df.columns
        if c.lower() in {"index", "row", "row_id"}
    ]

    if drop_cols:
        df = df.drop(columns=drop_cols)

    return df.to_numpy(dtype=float)


def _read_vector(path: Path) -> np.ndarray:
    arr = _read_matrix(path)

    if arr.shape[1] == 1:
        return arr.reshape(-1, 1)

    if arr.shape[0] == 1:
        return arr.reshape(-1, 1)

    raise ValueError(f"Expected vector-like matrix at {path}, got {arr.shape}")


@pytest.mark.parity
def test_native_system_gmm_matches_xtabond2_moments_a2_and_hansen() -> None:
    required = [
        ART / "system_gmm_benchmark.csv",
        ART / "stata_Ze.csv",
        ART / "stata_A2.csv",
        ROOT / "scripts" / "parity" / "run_native_system_gmm_benchmark.py",
    ]

    missing = [p for p in required if not p.exists()]
    if missing:
        pytest.skip(
            "xtabond2 parity artifacts are unavailable: "
            + ", ".join(str(p) for p in missing)
        )

    env = os.environ.copy()

    # No parity behavior env flags should be required anymore.
    env.pop("SYSTEMGMMKIT_SYSTEM_IV_Z_MODE", None)
    env.pop("SYSTEMGMMKIT_DIFF_GMM_LAGGED_DEP_OFFSET", None)
    env.pop("SYSTEMGMMKIT_LEVEL_GMM_LAGGED_DEP_OFFSET", None)
    env.pop("SYSTEMGMMKIT_HANSEN_GROUP_SCALE", None)

    # Only debug export is enabled so the test can inspect internals.
    env["SYSTEMGMMKIT_EXPORT_GMM_DEBUG"] = "1"
    env["SYSTEMGMMKIT_GMM_DEBUG_DIR"] = "artifacts/parity/xtabond2"

    subprocess.run(
        [sys.executable, "scripts/parity/run_native_system_gmm_benchmark.py"],
        cwd=ROOT,
        env=env,
        check=True,
    )

    debug = pd.read_csv(ART / "native_debug_shapes.csv").iloc[0]

    assert int(debug["Z_rows"]) == 2400
    assert int(debug["Z_cols"]) == 8
    assert int(debug["X_cols"]) == 4
    assert int(debug["Ze_rows"]) == 8
    assert int(debug["W_rows"]) == 8
    assert int(debug["W_cols"]) == 8

    native_j = float(debug["native_j_stat"])
    assert abs(native_j - XTABOND2_HANSEN) < 1e-5

    native_ze = _read_vector(ART / "native_Ze.csv")
    stata_ze = _read_vector(ART / "stata_Ze.csv")

    native_ze_reordered = native_ze[ORDER_NATIVE_TO_STATA, :]
    ze_abs_diff = np.abs(native_ze_reordered - stata_ze)

    assert float(np.max(ze_abs_diff)) < 1e-4
    assert float(np.mean(ze_abs_diff)) < 1e-5

    native_a2 = _read_matrix(ART / "native_A2.csv")
    stata_a2 = _read_matrix(ART / "stata_A2.csv")

    native_a2_reordered = native_a2[np.ix_(ORDER_NATIVE_TO_STATA, ORDER_NATIVE_TO_STATA)]

    n_groups = 96
    native_a2_scaled = native_a2_reordered / n_groups

    a2_abs_diff = np.abs(native_a2_scaled - stata_a2)

    assert float(np.max(a2_abs_diff)) < 1e-8
    assert float(np.mean(a2_abs_diff)) < 1e-9

    j_from_native_scaled_a2 = float(
        (stata_ze.T @ native_a2_scaled @ stata_ze).squeeze()
    )

    assert abs(j_from_native_scaled_a2 - XTABOND2_HANSEN) < 1e-5