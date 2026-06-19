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

OUT.mkdir(parents=True, exist_ok=True)

offsets = ["-1", "0", "1", "2"]
rows = []

for offset in offsets:
    print("\n" + "=" * 100)
    print(f"RUNNING FOD IV INSTRUMENT OFFSET={offset}")
    print("=" * 100)

    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path.cwd() / "src")
    env["SYSTEMGMMKIT_FORCE_ONESTEP"] = "1"

    # GMM timing fix already identified. Set explicitly.
    env["SYSTEMGMMKIT_FOD_GMM_INSTRUMENT_POS_OFFSET"] = "1"
    env["SYSTEMGMMKIT_FOD_IV_INSTRUMENT_POS_OFFSET"] = offset

    proc = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=str(Path.cwd()),
        env=env,
        text=True,
        capture_output=True,
    )

    run_name = f"fod_iv_offset_{offset.replace('-', 'm')}"
    stdout_path = OUT / f"{run_name}_stdout.txt"
    stderr_path = OUT / f"{run_name}_stderr.txt"
    stdout_path.write_text(proc.stdout, encoding="utf-8")
    stderr_path.write_text(proc.stderr, encoding="utf-8")

    if proc.returncode != 0:
        rows.append(
            {
                "fod_iv_instrument_pos_offset": offset,
                "status": "ERROR",
                "returncode": proc.returncode,
                "max_abs_coef_diff": None,
                "mean_abs_coef_diff": None,
                "m_base_w_abs_coef_diff": None,
                "max_abs_se_diff": None,
                "mean_abs_se_diff": None,
                "stdout": str(stdout_path),
                "stderr": str(stderr_path),
            }
        )
        print("ERROR")
        print(proc.stderr[-2000:])
        continue

    comp_path = OUT / "native_vs_stata_onestep_coef_comparison.csv"

    if not comp_path.exists():
        rows.append(
            {
                "fod_iv_instrument_pos_offset": offset,
                "status": "MISSING_COMPARISON_OUTPUT",
                "returncode": proc.returncode,
                "max_abs_coef_diff": None,
                "mean_abs_coef_diff": None,
                "m_base_w_abs_coef_diff": None,
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

    m_base_w = valid[valid["model"].astype(str).eq("m_base") & valid["param"].astype(str).eq("w")]

    row = {
        "fod_iv_instrument_pos_offset": offset,
        "status": "OK",
        "returncode": proc.returncode,
        "max_abs_coef_diff": valid["abs_coef_diff"].max(),
        "mean_abs_coef_diff": valid["abs_coef_diff"].mean(),
        "m_base_w_abs_coef_diff": (
            m_base_w["abs_coef_diff"].iloc[0] if not m_base_w.empty else None
        ),
        "max_abs_se_diff": valid["abs_se_diff"].max(),
        "mean_abs_se_diff": valid["abs_se_diff"].mean(),
        "coef_file": str(copy_path),
        "stdout": str(stdout_path),
        "stderr": str(stderr_path),
    }

    rows.append(row)

    print(
        f"OK: max_coef={row['max_abs_coef_diff']:.6g} | "
        f"mean_coef={row['mean_abs_coef_diff']:.6g} | "
        f"m_base_w={row['m_base_w_abs_coef_diff']:.6g}"
    )

grid = pd.DataFrame(rows)
out_path = OUT / "fod_iv_instrument_offset_grid_summary.csv"
grid.to_csv(out_path, index=False)

print("\nGRID SUMMARY")
print(grid.sort_values("max_abs_coef_diff", na_position="last").to_string(index=False))

print(f"\nWrote: {out_path}")
