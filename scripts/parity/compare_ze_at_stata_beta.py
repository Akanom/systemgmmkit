from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
ART = ROOT / "artifacts" / "parity" / "xtabond2"

NATIVE_Z = ART / "native_Z.csv"
NATIVE_X = ART / "native_X.csv"
NATIVE_Y = ART / "native_y_stack.csv"

STATA_B = ART / "stata_b.csv"
STATA_ZE = ART / "stata_Ze.csv"

NATIVE_PARAMS = ART / "native_system_gmm_params.csv"
NATIVE_REGRESSORS = ART / "native_regressor_names.csv"


def read_numeric_matrix(path: Path) -> np.ndarray:
    if not path.exists():
        raise FileNotFoundError(path)

    df = pd.read_csv(path)

    # Drop obvious non-numeric/index columns if present
    for col in list(df.columns):
        if col.lower() in {"index", "row", "row_id"}:
            df = df.drop(columns=[col])

    return df.to_numpy(dtype=float)


def read_vector(path: Path) -> np.ndarray:
    arr = read_numeric_matrix(path)

    if arr.shape[0] == 1 and arr.shape[1] > 1:
        return arr.reshape(-1, 1)

    if arr.shape[1] == 1:
        return arr.reshape(-1, 1)

    raise ValueError(f"Expected vector-like matrix from {path}, got shape {arr.shape}")


def main() -> None:
    Z = read_numeric_matrix(NATIVE_Z)
    X = read_numeric_matrix(NATIVE_X)
    y = read_vector(NATIVE_Y)

    b_stata = read_vector(STATA_B)
    ze_stata = read_vector(STATA_ZE)

    print("=" * 100)
    print("SHAPE CHECK")
    print("=" * 100)
    print(f"Z native:       {Z.shape}")
    print(f"X native:       {X.shape}")
    print(f"y native:       {y.shape}")
    print(f"b Stata:        {b_stata.shape}")
    print(f"Ze Stata:       {ze_stata.shape}")
    print()

    if X.shape[1] != b_stata.shape[0]:
        raise SystemExit(
            f"FAILED: X columns {X.shape[1]} != Stata b rows {b_stata.shape[0]}. "
            "Coefficient order or export shape must be fixed first."
        )

    if Z.shape[0] != X.shape[0] or X.shape[0] != y.shape[0]:
        raise SystemExit(
            f"FAILED: stacked rows differ. Z={Z.shape}, X={X.shape}, y={y.shape}"
        )

    u_at_stata_b = y - X @ b_stata
    ze_at_stata_b = Z.T @ u_at_stata_b

    if ze_at_stata_b.shape != ze_stata.shape:
        raise SystemExit(
            f"FAILED: Ze shapes differ. Native-at-Stata-b={ze_at_stata_b.shape}, "
            f"Stata={ze_stata.shape}"
        )

    diff = ze_at_stata_b.reshape(-1) - ze_stata.reshape(-1)

    denom = float(np.dot(ze_at_stata_b.reshape(-1), ze_at_stata_b.reshape(-1)))
    alpha = (
        float(np.dot(ze_stata.reshape(-1), ze_at_stata_b.reshape(-1)) / denom)
        if denom != 0
        else np.nan
    )

    scaled = alpha * ze_at_stata_b.reshape(-1)
    scaled_diff = scaled - ze_stata.reshape(-1)

    out = pd.DataFrame({
        "row_id": np.arange(1, ze_stata.shape[0] + 1),
        "native_Ze_at_stata_b": ze_at_stata_b.reshape(-1),
        "stata_Ze": ze_stata.reshape(-1),
        "diff": diff,
        "abs_diff": np.abs(diff),
        "native_scaled_to_stata": scaled,
        "scaled_diff": scaled_diff,
        "abs_scaled_diff": np.abs(scaled_diff),
    })

    summary = pd.DataFrame([{
        "n_rows": int(ze_stata.shape[0]),
        "max_abs_diff": float(np.max(np.abs(diff))),
        "mean_abs_diff": float(np.mean(np.abs(diff))),
        "rmse": float(np.sqrt(np.mean(diff ** 2))),
        "corr": float(np.corrcoef(ze_at_stata_b.reshape(-1), ze_stata.reshape(-1))[0, 1]),
        "best_scalar_alpha_stata_over_native": alpha,
        "max_abs_diff_after_best_scalar": float(np.max(np.abs(scaled_diff))),
        "mean_abs_diff_after_best_scalar": float(np.mean(np.abs(scaled_diff))),
        "u_at_stata_b_norm": float(np.linalg.norm(u_at_stata_b)),
        "ze_at_stata_b_norm": float(np.linalg.norm(ze_at_stata_b)),
        "stata_ze_norm": float(np.linalg.norm(ze_stata)),
    }])

    out_path = ART / "native_Ze_at_stata_b_vs_stata_Ze.csv"
    summary_path = ART / "native_Ze_at_stata_b_summary.csv"
    u_path = ART / "native_u_at_stata_b.csv"

    out.to_csv(out_path, index=False)
    summary.to_csv(summary_path, index=False)
    pd.DataFrame(u_at_stata_b, columns=["native_u_at_stata_b"]).to_csv(u_path, index=False)

    print("=" * 100)
    print("NATIVE Ze AT STATA b VS STATA e(Ze)")
    print("=" * 100)
    print(summary.to_string(index=False))
    print()
    print(out.to_string(index=False))
    print()
    print(f"Wrote: {out_path}")
    print(f"Wrote: {summary_path}")
    print(f"Wrote: {u_path}")

    if NATIVE_REGRESSORS.exists():
        print()
        print("=" * 100)
        print("NATIVE REGRESSOR ORDER")
        print("=" * 100)
        print(pd.read_csv(NATIVE_REGRESSORS).to_string(index=False))

    if NATIVE_PARAMS.exists():
        print()
        print("=" * 100)
        print("NATIVE PARAMS FILE")
        print("=" * 100)
        print(pd.read_csv(NATIVE_PARAMS).to_string(index=False))


if __name__ == "__main__":
    main()