from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
ART = ROOT / "artifacts" / "parity"

NATIVE_FILE = ART / "native_ze_system_gmm_baseline_controls.csv"
STATA_FILE = ART / "stata_ze_system_gmm_baseline_controls.csv"


def main() -> None:
    native = pd.read_csv(NATIVE_FILE)
    stata = pd.read_csv(STATA_FILE)

    native_cols = [c for c in native.columns if c.lower() not in {"row_id", "row"}]
    stata_cols = [c for c in stata.columns if c.lower() not in {"row_id", "row"}]

    if not native_cols:
        raise ValueError(f"No native Ze column found in {NATIVE_FILE}")

    if not stata_cols:
        raise ValueError(f"No Stata Ze column found in {STATA_FILE}")

    n = native[native_cols[0]].to_numpy(dtype=float).reshape(-1)
    s = stata[stata_cols[0]].to_numpy(dtype=float).reshape(-1)

    if len(n) != len(s):
        print("VECTOR LENGTH MISMATCH")
        print(f"native length: {len(n)}")
        print(f"stata length:  {len(s)}")
        return

    diff = n - s

    # Best scalar fit: s ≈ alpha * n
    denom = float(np.dot(n, n))
    alpha = float(np.dot(s, n) / denom) if denom != 0 else np.nan
    scaled_diff = alpha * n - s

    corr = np.corrcoef(n, s)[0, 1] if len(n) > 1 else np.nan

    out = pd.DataFrame({
        "row_id": np.arange(1, len(n) + 1),
        "native_Ze": n,
        "stata_Ze": s,
        "diff": diff,
        "abs_diff": np.abs(diff),
        "native_scaled_to_stata": alpha * n,
        "scaled_diff": scaled_diff,
        "abs_scaled_diff": np.abs(scaled_diff),
    })

    out_path = ART / "ze_native_vs_stata_comparison.csv"
    out.to_csv(out_path, index=False)

    summary = pd.DataFrame([{
        "n_rows": len(n),
        "max_abs_diff": float(np.max(np.abs(diff))),
        "mean_abs_diff": float(np.mean(np.abs(diff))),
        "rmse": float(np.sqrt(np.mean(diff ** 2))),
        "corr": float(corr),
        "best_scalar_alpha_stata_over_native": alpha,
        "max_abs_diff_after_best_scalar": float(np.max(np.abs(scaled_diff))),
        "mean_abs_diff_after_best_scalar": float(np.mean(np.abs(scaled_diff))),
    }])

    summary_path = ART / "ze_native_vs_stata_summary.csv"
    summary.to_csv(summary_path, index=False)

    print("=" * 100)
    print("NATIVE Ze VS STATA e(Ze) SUMMARY")
    print("=" * 100)
    print(summary.to_string(index=False))
    print()
    print(f"Wrote: {out_path}")
    print(f"Wrote: {summary_path}")


if __name__ == "__main__":
    main()