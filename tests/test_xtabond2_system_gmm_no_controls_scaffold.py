from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "parity" / "xtabond2" / "specs" / "system_gmm_no_controls"


@pytest.mark.parity
def test_system_gmm_no_controls_scaffold_generates_native_artifacts() -> None:
    subprocess.run(
        [sys.executable, "scripts/parity/build_xtabond2_system_gmm_no_controls_do.py"],
        cwd=ROOT,
        check=True,
    )

    subprocess.run(
        [sys.executable, "scripts/parity/run_native_system_gmm_no_controls.py"],
        cwd=ROOT,
        check=True,
    )

    params_path = OUT / "native_params.csv"
    diagnostics_path = OUT / "native_diagnostics.csv"
    dofile_path = OUT / "system_gmm_no_controls.do"

    assert params_path.exists()
    assert diagnostics_path.exists()
    assert dofile_path.exists()

    params = pd.read_csv(params_path)
    diagnostics = pd.read_csv(diagnostics_path)

    assert diagnostics.loc[0, "spec"] == "system_gmm_no_controls"
    assert set(["L1.y", "x"]).issubset(set(params["param"]))
    assert "w" not in set(params["param"])
    assert int(diagnostics.loc[0, "native_n_instruments"]) > 0
    assert int(diagnostics.loc[0, "native_nobs"]) > 0
