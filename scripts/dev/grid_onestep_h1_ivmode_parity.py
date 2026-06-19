from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd

OUT = Path("artifacts/parity/gmm_lag_windows_realdata_notime")
SCRIPT = Path("scripts/dev/compare_realdata_notime_onestep_native_vs_stata.py")

if not SCRIPT.exists():
    raise SystemExit(f"Missing comparison script: {SCRIPT}")

grid_rows = []

h1_modes = ["blockdiag", "full_error_cov", "identity"]
iv_modes = ["stacked_x", "level_only", "diff_only", "zero"]

for h1 in h1_modes:
    for iv_mode in iv_modes:
        print("\n" + "=" * 100)
        print(f"RUNNING GRID: H1={h1} | IV_Z_MODE={iv_mode}")
        print("=" * 100)

        env = os.environ.copy()
        env["PYTHONPATH"] = str(Path.cwd() / "src")
        env["SYSTEMGMMKIT_FORCE_ONESTEP"] = "1"
        env["SYSTEMGMMKIT_H1_MODE"] = h1
        env["SYSTEMGMMKIT_SYSTEM_IV_Z_MODE"] = iv_mode

        proc = subprocess.run(
            [sys.executable, str(SCRIPT)],
            cwd=str(Path.cwd()),
            env=env,
            text=True,
            capture_output=True,
        )

        run_name = f"h1_{h1}__iv_{iv_mode}"
        stdout_path = OUT / f"{run_name}_stdout.txt"
        stderr_path = OUT / f"{run_name}_stderr.txt"

        stdout_path.write_text(proc.stdout, encoding="utf-8")
        stderr_path.write_text(proc.stderr, encoding="utf-8")

        if proc.returncode != 0:
            grid_rows.append(
                {
                    "h1_mode": h1,
                    "iv_z_mode": iv_mode,
                    "status": "ERROR",
                    "returncode": proc.returncode,
                    "max_abs_coef_diff": None,
                    "mean_abs_coef_diff": None,
                    "max_abs_se_diff": None,
                    "mean_abs_se_diff": None,
                    "stdout": str(stdout_path),
                    "stderr": str(stderr_path),
                }
            )
            print(f"ERROR: returncode={proc.returncode}")
            print(proc.stderr[-2000:])
            continue

        comp_path = OUT / "native_vs_stata_onestep_coef_comparison.csv"
        if not comp_path.exists():
            grid_rows.append(
                {
                    "h1_mode": h1,
                    "iv_z_mode": iv_mode,
                    "status": "MISSING_OUTPUT",
                    "returncode": proc.returncode,
                    "max_abs_coef_diff": None,
                    "mean_abs_coef_diff": None,
                    "max_abs_se_diff": None,
                    "mean_abs_se_diff": None,
                    "stdout": str(stdout_path),
                    "stderr": str(stderr_path),
                }
            )
            continue

        copy_path = OUT / f"{run_name}_coef_comparison.csv"
        shutil.copyfile(comp_path, copy_path)

        comp = pd.read_csv(comp_path)
        valid = comp.dropna(subset=["abs_coef_diff"]).copy()

        summary_all = {
            "h1_mode": h1,
            "iv_z_mode": iv_mode,
            "status": "OK",
            "returncode": proc.returncode,
            "max_abs_coef_diff": valid["abs_coef_diff"].max(),
            "mean_abs_coef_diff": valid["abs_coef_diff"].mean(),
            "max_abs_se_diff": valid["abs_se_diff"].max(),
            "mean_abs_se_diff": valid["abs_se_diff"].mean(),
            "coef_file": str(copy_path),
            "stdout": str(stdout_path),
            "stderr": str(stderr_path),
        }

        # Also track x specifically because x is the biggest offender.
        x_valid = valid[valid["param"].astype(str).eq("x")]
        if not x_valid.empty:
            summary_all["max_abs_x_coef_diff"] = x_valid["abs_coef_diff"].max()
            summary_all["mean_abs_x_coef_diff"] = x_valid["abs_coef_diff"].mean()
        else:
            summary_all["max_abs_x_coef_diff"] = None
            summary_all["mean_abs_x_coef_diff"] = None

        grid_rows.append(summary_all)

        print(
            f"OK: max_coef={summary_all['max_abs_coef_diff']:.6g} | "
            f"mean_coef={summary_all['mean_abs_coef_diff']:.6g} | "
            f"max_x={summary_all['max_abs_x_coef_diff']:.6g}"
        )

grid = pd.DataFrame(grid_rows)
grid_path = OUT / "onestep_h1_ivmode_grid_summary.csv"
grid.to_csv(grid_path, index=False)

print("\n" + "=" * 100)
print("GRID SUMMARY")
print("=" * 100)

cols = [
    "h1_mode",
    "iv_z_mode",
    "status",
    "max_abs_coef_diff",
    "mean_abs_coef_diff",
    "max_abs_x_coef_diff",
    "mean_abs_x_coef_diff",
    "max_abs_se_diff",
    "mean_abs_se_diff",
]

print(
    grid[cols]
    .sort_values(["status", "max_abs_coef_diff"], na_position="last")
    .to_string(index=False)
)

print(f"\nWrote: {grid_path}")
