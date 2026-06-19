from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd

OUT = Path("artifacts/parity/gmm_lag_windows_realdata_notime")
SCRIPT = Path("scripts/dev/compare_realdata_notime_onestep_native_vs_stata.py")

start_positions = ["0", "1", "2", "3", "4"]
offsets = ["-3", "-2", "-1", "0", "1", "2", "3"]

rows = []

for start_pos in start_positions:
    for offset in offsets:
        print("\n" + "=" * 100)
        print(f"RUNNING FOD START POS={start_pos} | GMM INSTRUMENT OFFSET={offset}")
        print("=" * 100)

        env = os.environ.copy()
        env["PYTHONPATH"] = str(Path.cwd() / "src")
        env["SYSTEMGMMKIT_FORCE_ONESTEP"] = "1"
        env["SYSTEMGMMKIT_FOD_START_POS"] = start_pos
        env["SYSTEMGMMKIT_FOD_GMM_INSTRUMENT_POS_OFFSET"] = offset

        proc = subprocess.run(
            [sys.executable, str(SCRIPT)],
            cwd=str(Path.cwd()),
            env=env,
            text=True,
            capture_output=True,
        )

        run_name = f"fod_start_{start_pos}__gmm_offset_{offset.replace('-', 'm')}"
        stdout_path = OUT / f"{run_name}_stdout.txt"
        stderr_path = OUT / f"{run_name}_stderr.txt"
        stdout_path.write_text(proc.stdout, encoding="utf-8")
        stderr_path.write_text(proc.stderr, encoding="utf-8")

        if proc.returncode != 0:
            rows.append(
                {
                    "fod_start_pos": start_pos,
                    "gmm_instrument_pos_offset": offset,
                    "status": "ERROR",
                    "returncode": proc.returncode,
                    "max_abs_coef_diff": None,
                    "mean_abs_coef_diff": None,
                    "max_abs_x_coef_diff": None,
                    "mean_abs_x_coef_diff": None,
                    "max_abs_se_diff": None,
                    "mean_abs_se_diff": None,
                    "stderr": str(stderr_path),
                }
            )
            print(proc.stderr[-1600:])
            continue

        comp_path = OUT / "native_vs_stata_onestep_coef_comparison.csv"
        copy_path = OUT / f"{run_name}_coef_comparison.csv"
        shutil.copyfile(comp_path, copy_path)

        comp = pd.read_csv(comp_path)
        valid = comp.dropna(subset=["abs_coef_diff"]).copy()
        x_valid = valid[valid["param"].astype(str).eq("x")]

        row = {
            "fod_start_pos": start_pos,
            "gmm_instrument_pos_offset": offset,
            "status": "OK",
            "returncode": proc.returncode,
            "max_abs_coef_diff": valid["abs_coef_diff"].max(),
            "mean_abs_coef_diff": valid["abs_coef_diff"].mean(),
            "max_abs_x_coef_diff": x_valid["abs_coef_diff"].max() if not x_valid.empty else None,
            "mean_abs_x_coef_diff": x_valid["abs_coef_diff"].mean() if not x_valid.empty else None,
            "max_abs_se_diff": valid["abs_se_diff"].max(),
            "mean_abs_se_diff": valid["abs_se_diff"].mean(),
            "coef_file": str(copy_path),
        }

        rows.append(row)

        print(
            f"OK: max_coef={row['max_abs_coef_diff']:.6g} | "
            f"mean_coef={row['mean_abs_coef_diff']:.6g} | "
            f"max_x={row['max_abs_x_coef_diff']:.6g}"
        )

grid = pd.DataFrame(rows)
out_path = OUT / "fod_start_pos_gmm_instrument_offset_grid_summary.csv"
grid.to_csv(out_path, index=False)

print("\nGRID SUMMARY")
cols = [
    "fod_start_pos",
    "gmm_instrument_pos_offset",
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
    .head(20)
    .to_string(index=False)
)

print(f"\nWrote: {out_path}")
