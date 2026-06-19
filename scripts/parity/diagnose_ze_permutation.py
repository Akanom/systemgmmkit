from __future__ import annotations

import itertools
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
ART = ROOT / "artifacts" / "parity" / "xtabond2"

NATIVE_FILE = ART / "native_Ze_at_stata_b_vs_stata_Ze.csv"
NATIVE_INST = ART / "native_instrument_names.csv"
STATA_NAMES = ART / "stata_Ze_names.csv"


def main() -> None:
    df = pd.read_csv(NATIVE_FILE)

    native = df["native_Ze_at_stata_b"].to_numpy(float)
    stata = df["stata_Ze"].to_numpy(float)

    native_names = pd.read_csv(NATIVE_INST)["instrument_name"].tolist()

    if STATA_NAMES.exists():
        names_raw = pd.read_csv(STATA_NAMES)
        stata_names = names_raw[names_raw["type"] == "row"]["name"].tolist()
    else:
        stata_names = [f"stata_row_{i}" for i in range(1, len(stata) + 1)]

    if len(native) != len(stata):
        raise ValueError("Native and Stata Ze vectors have different lengths.")

    rows = []

    for i, nv in enumerate(native):
        diffs = np.abs(stata - nv)
        best_j = int(np.argmin(diffs))

        rows.append(
            {
                "native_index": i + 1,
                "native_instrument": native_names[i] if i < len(native_names) else "",
                "native_value": nv,
                "closest_stata_index": best_j + 1,
                "closest_stata_name": stata_names[best_j] if best_j < len(stata_names) else "",
                "closest_stata_value": stata[best_j],
                "abs_diff": float(diffs[best_j]),
            }
        )

    greedy = pd.DataFrame(rows)
    greedy_path = ART / "ze_greedy_nearest_matches.csv"
    greedy.to_csv(greedy_path, index=False)

    # Exact small-n assignment search: find permutation minimizing total absolute difference.
    best_perm = None
    best_score = float("inf")

    for perm in itertools.permutations(range(len(stata))):
        score = float(np.sum(np.abs(native - stata[list(perm)])))
        if score < best_score:
            best_score = score
            best_perm = perm

    assignment_rows = []
    assert best_perm is not None

    for i, j in enumerate(best_perm):
        assignment_rows.append(
            {
                "native_index": i + 1,
                "native_instrument": native_names[i] if i < len(native_names) else "",
                "native_value": native[i],
                "assigned_stata_index": j + 1,
                "assigned_stata_name": stata_names[j] if j < len(stata_names) else "",
                "assigned_stata_value": stata[j],
                "diff_native_minus_stata": native[i] - stata[j],
                "abs_diff": abs(native[i] - stata[j]),
            }
        )

    assignment = pd.DataFrame(assignment_rows)
    assignment_path = ART / "ze_best_permutation_assignment.csv"
    assignment.to_csv(assignment_path, index=False)

    summary = pd.DataFrame(
        [
            {
                "n": len(native),
                "best_total_abs_diff": best_score,
                "best_mean_abs_diff": best_score / len(native),
                "best_max_abs_diff": float(assignment["abs_diff"].max()),
            }
        ]
    )

    summary_path = ART / "ze_best_permutation_summary.csv"
    summary.to_csv(summary_path, index=False)

    print("=" * 100)
    print("GREEDY NEAREST MATCHES")
    print("=" * 100)
    print(greedy.to_string(index=False))
    print()

    print("=" * 100)
    print("BEST GLOBAL PERMUTATION ASSIGNMENT")
    print("=" * 100)
    print(summary.to_string(index=False))
    print()
    print(assignment.to_string(index=False))
    print()

    print(f"Wrote: {greedy_path}")
    print(f"Wrote: {assignment_path}")
    print(f"Wrote: {summary_path}")


if __name__ == "__main__":
    main()
