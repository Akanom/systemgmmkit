from __future__ import annotations

from pathlib import Path

import pandas as pd
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
ART = ROOT / "artifacts" / "parity" / "xtabond2"

STATA_B = ART / "stata_b.csv"
NATIVE_PARAMS = ART / "native_system_gmm_params.csv"
NATIVE_REGRESSORS = ART / "native_regressor_names.csv"


def read_stata_b(path: Path) -> np.ndarray:
    df = pd.read_csv(path)
    return df.to_numpy(dtype=float).reshape(-1)


def main() -> None:
    stata_b = read_stata_b(STATA_B)
    native = pd.read_csv(NATIVE_PARAMS)

    print("=" * 100)
    print("RAW NATIVE PARAMS")
    print("=" * 100)
    print(native.to_string(index=False))
    print()

    print("=" * 100)
    print("NATIVE REGRESSOR ORDER")
    print("=" * 100)
    if NATIVE_REGRESSORS.exists():
        print(pd.read_csv(NATIVE_REGRESSORS).to_string(index=False))
    print()

    # Try common layouts
    numeric_cols = native.select_dtypes(include="number").columns.tolist()

    if "coef" in native.columns:
        native_b = native["coef"].to_numpy(dtype=float)
    elif "estimate" in native.columns:
        native_b = native["estimate"].to_numpy(dtype=float)
    elif len(numeric_cols) == 1:
        native_b = native[numeric_cols[0]].to_numpy(dtype=float)
    else:
        raise SystemExit(
            f"Could not infer native coefficient column. Columns={list(native.columns)}"
        )

    if len(native_b) != len(stata_b):
        raise SystemExit(
            f"Coefficient length mismatch: native={len(native_b)}, stata={len(stata_b)}"
        )

    names = ["L1.y", "x", "w", "_cons"]

    cmp = pd.DataFrame({
        "param": names[:len(stata_b)],
        "native_b": native_b,
        "stata_b": stata_b,
        "diff_native_minus_stata": native_b - stata_b,
        "abs_diff": np.abs(native_b - stata_b),
    })

    summary = pd.DataFrame([{
        "n_params": len(stata_b),
        "max_abs_coef_diff": float(cmp["abs_diff"].max()),
        "mean_abs_coef_diff": float(cmp["abs_diff"].mean()),
        "rmse": float(np.sqrt(np.mean((native_b - stata_b) ** 2))),
    }])

    cmp_path = ART / "native_vs_stata_coefficients.csv"
    summary_path = ART / "native_vs_stata_coefficients_summary.csv"

    cmp.to_csv(cmp_path, index=False)
    summary.to_csv(summary_path, index=False)

    print("=" * 100)
    print("NATIVE VS STATA COEFFICIENTS")
    print("=" * 100)
    print(summary.to_string(index=False))
    print()
    print(cmp.to_string(index=False))
    print()
    print(f"Wrote: {cmp_path}")
    print(f"Wrote: {summary_path}")


if __name__ == "__main__":
    main()