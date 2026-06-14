from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_fod_diff_parity_runner_rejects_windmeijer() -> None:
    script = Path("scripts/parity/run_native_fod_diff_parity.py")
    data = Path("artifacts/parity/xtabond2/system_gmm_benchmark.csv")
    out = Path("artifacts/parity/xtdpdgmm/fod_diff")

    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--data-csv",
            str(data),
            "--out-dir",
            str(out),
            "--entity",
            "id",
            "--time",
            "t",
            "--y",
            "y",
            "--x",
            "x",
            "--w",
            "w",
            "--windmeijer",
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    combined = result.stdout + result.stderr
    assert "Windmeijer" in combined
    assert "not certified for FOD Difference GMM" in combined
