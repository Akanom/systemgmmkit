from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
ART = ROOT / "artifacts" / "parity" / "xtabond2"

DATA_FILE = ART / "system_gmm_benchmark.csv"
META_FILE = ART / "native_row_meta.csv"
U_FILE = ART / "native_u_at_stata_b.csv"
STATA_ZE_FILE = ART / "stata_Ze.csv"
NATIVE_Z_FILE = ART / "native_Z.csv"
INST_FILE = ART / "native_instrument_names.csv"


def lookup(mapping: dict[tuple[int, int], float], entity: int, time: int) -> float | None:
    val = mapping.get((int(entity), int(time)))
    if val is None or not np.isfinite(val):
        return None
    return float(val)


def main() -> None:
    data = pd.read_csv(DATA_FILE)
    meta = pd.read_csv(META_FILE)
    u = pd.read_csv(U_FILE).to_numpy(float).reshape(-1)
    stata_ze = pd.read_csv(STATA_ZE_FILE).to_numpy(float).reshape(-1)

    Z = pd.read_csv(NATIVE_Z_FILE).to_numpy(float)
    inst = pd.read_csv(INST_FILE)["instrument_name"].tolist()

    target_index = 7
    target = float(stata_ze[target_index - 1])

    y_map = {
        (int(r.id), int(r.t)): float(r.y)
        for r in data.itertuples(index=False)
    }

    entity_arr = meta["entity"].astype(int).to_numpy()
    time_arr = meta["time"].astype(int).to_numpy()
    equation_arr = meta["equation"].astype(str).str.lower().to_numpy()

    level_mask = equation_arr == "level"

    rows = []

    # Native current column for reference.
    if "L:diff:y:L1" in inst:
        native_idx = inst.index("L:diff:y:L1")
        native_col = Z[:, native_idx]
        native_ze = float(native_col @ u)

        rows.append({
            "candidate": "CURRENT_NATIVE_L:diff:y:L1",
            "left_offset": None,
            "right_offset": None,
            "time_min": None,
            "time_max": None,
            "missing_policy": "native",
            "candidate_Ze": native_ze,
            "target_stata_r7": target,
            "abs_diff_to_r7": abs(native_ze - target),
            "nonzero_rows": int(np.count_nonzero(native_col)),
        })

    # Offset convention:
    # offset = 0  -> y[t]
    # offset = 1  -> y[t-1]
    # offset = -1 -> y[t+1]
    #
    # Candidate instrument:
    # y[t-left_offset] - y[t-right_offset]
    offsets = range(-3, 8)

    level_times = sorted(set(time_arr[level_mask]))
    min_time = min(level_times)
    max_time = max(level_times)

    time_min_options = [min_time, min_time + 1, min_time + 2, min_time + 3, min_time + 4]
    time_max_options = [max_time, max_time - 1, max_time - 2, max_time - 3, max_time - 4]

    missing_policies = ["zero_missing", "skip_missing"]

    for left_offset in offsets:
        for right_offset in offsets:
            if left_offset == right_offset:
                continue

            for time_min in time_min_options:
                for time_max in time_max_options:
                    if time_min > time_max:
                        continue

                    for policy in missing_policies:
                        z = np.zeros(len(meta), dtype=float)

                        for i, (entity, time) in enumerate(zip(entity_arr, time_arr)):
                            if not level_mask[i]:
                                continue

                            if time < time_min or time > time_max:
                                continue

                            left = lookup(y_map, entity, time - left_offset)
                            right = lookup(y_map, entity, time - right_offset)

                            if left is None or right is None:
                                if policy == "zero_missing":
                                    z[i] = 0.0
                                elif policy == "skip_missing":
                                    z[i] = 0.0
                                continue

                            z[i] = left - right

                        ze = float(z @ u)

                        rows.append({
                            "candidate": f"y[t-{left_offset}] - y[t-{right_offset}]",
                            "left_offset": left_offset,
                            "right_offset": right_offset,
                            "time_min": time_min,
                            "time_max": time_max,
                            "missing_policy": policy,
                            "candidate_Ze": ze,
                            "target_stata_r7": target,
                            "abs_diff_to_r7": abs(ze - target),
                            "nonzero_rows": int(np.count_nonzero(z)),
                        })

    out = pd.DataFrame(rows).sort_values("abs_diff_to_r7").reset_index(drop=True)

    out_path = ART / "level_y_candidates_exhaustive_for_stata_r7.csv"
    out.to_csv(out_path, index=False)

    print("=" * 100)
    print(f"BEST LEVEL-y CANDIDATES FOR STATA r7 = {target}")
    print("=" * 100)
    print(out.head(40).to_string(index=False))
    print()
    print(f"Wrote: {out_path}")


if __name__ == "__main__":
    main()