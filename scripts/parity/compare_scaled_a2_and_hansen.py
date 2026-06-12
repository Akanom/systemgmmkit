from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
ART = ROOT / "artifacts" / "parity" / "xtabond2"

NATIVE_A2 = ART / "native_A2.csv"
STATA_A2 = ART / "stata_A2.csv"
STATA_ZE = ART / "stata_Ze.csv"
NATIVE_ZE_REORDERED = ART / "native_Ze_reordered_to_stata_order.csv"

ORDER_NATIVE_TO_STATA = [4, 7, 0, 2, 1, 3, 5, 6]
N_GROUPS = 96
XTABOND2_HANSEN = 6.577371156435732


def read_matrix(path: Path) -> np.ndarray:
    if not path.exists():
        raise FileNotFoundError(path)

    df = pd.read_csv(path)

    drop_cols = [c for c in df.columns if c.lower() in {"index", "row", "row_id"}]
    if drop_cols:
        df = df.drop(columns=drop_cols)

    return df.to_numpy(dtype=float)


def read_vector(path: Path) -> np.ndarray:
    arr = read_matrix(path)

    if arr.shape[0] == 1 and arr.shape[1] > 1:
        return arr.reshape(-1, 1)

    if arr.shape[1] == 1:
        return arr.reshape(-1, 1)

    raise ValueError(f"Expected vector-like matrix from {path}, got {arr.shape}")


def main() -> None:
    native_a2 = read_matrix(NATIVE_A2)
    stata_a2 = read_matrix(STATA_A2)
    stata_ze = read_vector(STATA_ZE)

    native_a2_reordered = native_a2[np.ix_(ORDER_NATIVE_TO_STATA, ORDER_NATIVE_TO_STATA)]
    native_a2_reordered_scaled = native_a2_reordered / N_GROUPS

    a2_diff = native_a2_reordered_scaled - stata_a2

    j_from_stata_a2 = float((stata_ze.T @ stata_a2 @ stata_ze).squeeze())
    j_from_native_scaled_a2 = float(
        (stata_ze.T @ native_a2_reordered_scaled @ stata_ze).squeeze()
    )
    j_from_native_unscaled_a2 = float(
        (stata_ze.T @ native_a2_reordered @ stata_ze).squeeze()
    )

    summary = pd.DataFrame([{
        "n_groups": N_GROUPS,
        "native_a2_norm_reordered": float(np.linalg.norm(native_a2_reordered)),
        "native_a2_norm_reordered_div_groups": float(np.linalg.norm(native_a2_reordered_scaled)),
        "stata_a2_norm": float(np.linalg.norm(stata_a2)),
        "a2_scaled_max_abs_diff": float(np.max(np.abs(a2_diff))),
        "a2_scaled_mean_abs_diff": float(np.mean(np.abs(a2_diff))),
        "a2_scaled_rmse": float(np.sqrt(np.mean(a2_diff ** 2))),
        "j_from_stata_a2": j_from_stata_a2,
        "j_from_native_scaled_a2": j_from_native_scaled_a2,
        "j_from_native_unscaled_a2": j_from_native_unscaled_a2,
        "xtabond2_hansen": XTABOND2_HANSEN,
        "abs_diff_j_stata_a2_vs_xtabond2": abs(j_from_stata_a2 - XTABOND2_HANSEN),
        "abs_diff_j_native_scaled_a2_vs_xtabond2": abs(j_from_native_scaled_a2 - XTABOND2_HANSEN),
    }])

    diff_path = ART / "native_A2_reordered_div_groups_minus_stata_A2.csv"
    scaled_path = ART / "native_A2_reordered_div_groups.csv"
    summary_path = ART / "native_A2_group_scaled_summary.csv"

    pd.DataFrame(native_a2_reordered_scaled).to_csv(scaled_path, index=False)
    pd.DataFrame(a2_diff).to_csv(diff_path, index=False)
    summary.to_csv(summary_path, index=False)

    print("=" * 100)
    print("GROUP-SCALED A2 VS STATA A2")
    print("=" * 100)
    print(summary.to_string(index=False))
    print()
    print(f"Wrote: {scaled_path}")
    print(f"Wrote: {diff_path}")
    print(f"Wrote: {summary_path}")


if __name__ == "__main__":
    main()