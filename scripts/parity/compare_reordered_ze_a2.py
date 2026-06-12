from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
ART = ROOT / "artifacts" / "parity" / "xtabond2"

NATIVE_ZE = ART / "native_Ze_at_stata_b_vs_stata_Ze.csv"
NATIVE_A2 = ART / "native_A2.csv"
STATA_ZE = ART / "stata_Ze.csv"
STATA_A2 = ART / "stata_A2.csv"

# Native order:
# 0 D:y:L2
# 1 D:y:L3
# 2 D:x:L2
# 3 D:x:L3
# 4 IV:w
# 5 L:diff:y:L1
# 6 L:diff:x:L1
# 7 L:constant
#
# Stata order:
# 0 IV:w
# 1 L:constant
# 2 D:y:L2
# 3 D:x:L2
# 4 D:y:L3
# 5 D:x:L3
# 6 L:diff:y:L1
# 7 L:diff:x:L1
ORDER_NATIVE_TO_STATA = [4, 7, 0, 2, 1, 3, 5, 6]


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
    ze_cmp = pd.read_csv(NATIVE_ZE)
    native_ze = ze_cmp["native_Ze_at_stata_b"].to_numpy(float).reshape(-1, 1)
    stata_ze = read_vector(STATA_ZE)

    native_ze_reordered = native_ze[ORDER_NATIVE_TO_STATA, :]

    ze_out = pd.DataFrame({
        "stata_order_index": np.arange(1, len(ORDER_NATIVE_TO_STATA) + 1),
        "native_original_index": np.array(ORDER_NATIVE_TO_STATA) + 1,
        "native_Ze_reordered": native_ze_reordered.reshape(-1),
        "stata_Ze": stata_ze.reshape(-1),
        "diff": native_ze_reordered.reshape(-1) - stata_ze.reshape(-1),
        "abs_diff": np.abs(native_ze_reordered.reshape(-1) - stata_ze.reshape(-1)),
    })

    ze_summary = pd.DataFrame([{
        "n": int(len(stata_ze)),
        "max_abs_diff": float(ze_out["abs_diff"].max()),
        "mean_abs_diff": float(ze_out["abs_diff"].mean()),
        "rmse": float(np.sqrt(np.mean(ze_out["diff"].to_numpy(float) ** 2))),
    }])

    ze_out_path = ART / "native_Ze_reordered_to_stata_order.csv"
    ze_summary_path = ART / "native_Ze_reordered_to_stata_order_summary.csv"

    ze_out.to_csv(ze_out_path, index=False)
    ze_summary.to_csv(ze_summary_path, index=False)

    print("=" * 100)
    print("REORDERED NATIVE Ze VS STATA Ze")
    print("=" * 100)
    print(ze_summary.to_string(index=False))
    print()
    print(ze_out.to_string(index=False))

    if NATIVE_A2.exists() and STATA_A2.exists():
        native_a2 = read_matrix(NATIVE_A2)
        stata_a2 = read_matrix(STATA_A2)

        native_a2_reordered = native_a2[np.ix_(ORDER_NATIVE_TO_STATA, ORDER_NATIVE_TO_STATA)]

        if native_a2_reordered.shape != stata_a2.shape:
            raise SystemExit(
                f"A2 shape mismatch: native_reordered={native_a2_reordered.shape}, "
                f"stata={stata_a2.shape}"
            )

        a2_diff = native_a2_reordered - stata_a2

        a2_out = pd.DataFrame(a2_diff)
        a2_summary = pd.DataFrame([{
            "rows": int(stata_a2.shape[0]),
            "cols": int(stata_a2.shape[1]),
            "native_a2_norm_reordered": float(np.linalg.norm(native_a2_reordered)),
            "stata_a2_norm": float(np.linalg.norm(stata_a2)),
            "max_abs_diff": float(np.max(np.abs(a2_diff))),
            "mean_abs_diff": float(np.mean(np.abs(a2_diff))),
            "rmse": float(np.sqrt(np.mean(a2_diff ** 2))),
        }])

        a2_reordered_path = ART / "native_A2_reordered_to_stata_order.csv"
        a2_diff_path = ART / "native_A2_reordered_minus_stata_A2.csv"
        a2_summary_path = ART / "native_A2_reordered_to_stata_order_summary.csv"

        pd.DataFrame(native_a2_reordered).to_csv(a2_reordered_path, index=False)
        a2_out.to_csv(a2_diff_path, index=False)
        a2_summary.to_csv(a2_summary_path, index=False)

        print()
        print("=" * 100)
        print("REORDERED NATIVE A2 VS STATA A2")
        print("=" * 100)
        print(a2_summary.to_string(index=False))

    print()
    print(f"Wrote: {ze_out_path}")
    print(f"Wrote: {ze_summary_path}")


if __name__ == "__main__":
    main()