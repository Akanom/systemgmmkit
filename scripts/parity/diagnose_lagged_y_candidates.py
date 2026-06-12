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


def safe_lookup(values: dict[tuple[int, int], float], entity: int, time: int) -> float:
    val = values.get((int(entity), int(time)))
    if val is None or not np.isfinite(val):
        return 0.0
    return float(val)


def main() -> None:
    data = pd.read_csv(DATA_FILE)
    meta = pd.read_csv(META_FILE)
    u = pd.read_csv(U_FILE).to_numpy(float).reshape(-1)
    stata_ze = pd.read_csv(STATA_ZE_FILE).to_numpy(float).reshape(-1)

    if len(meta) != len(u):
        raise ValueError(f"meta/u length mismatch: meta={len(meta)}, u={len(u)}")

    required = {"id", "t", "y", "x", "w"}
    missing = required - set(data.columns)
    if missing:
        raise ValueError(f"Benchmark data missing columns: {sorted(missing)}")

    y_map = {
        (int(r.id), int(r.t)): float(r.y)
        for r in data.itertuples(index=False)
    }

    x_map = {
        (int(r.id), int(r.t)): float(r.x)
        for r in data.itertuples(index=False)
    }

    diff_mask = meta["equation"].astype(str).str.lower().eq("diff").to_numpy()
    level_mask = meta["equation"].astype(str).str.lower().eq("level").to_numpy()

    candidates: dict[str, np.ndarray] = {}

    entity_arr = meta["entity"].astype(int).to_numpy()
    time_arr = meta["time"].astype(int).to_numpy()

    # Difference-equation raw y-lag candidates.
    # D:y:Lk means use y[t-k] on difference-equation rows.
    for lag in range(1, 7):
        z = np.zeros(len(meta), dtype=float)

        for i, (entity, time) in enumerate(zip(entity_arr, time_arr)):
            if not diff_mask[i]:
                continue
            z[i] = safe_lookup(y_map, entity, time - lag)

        candidates[f"D:y:L{lag}"] = z

    # Difference-equation raw x-lag candidates for cross-checking.
    for lag in range(1, 7):
        z = np.zeros(len(meta), dtype=float)

        for i, (entity, time) in enumerate(zip(entity_arr, time_arr)):
            if not diff_mask[i]:
                continue
            z[i] = safe_lookup(x_map, entity, time - lag)

        candidates[f"D:x:L{lag}"] = z

    # Stata gmm(L.y, lag(2 3)) candidates:
    # L2.(L.y) = y[t-3]
    # L3.(L.y) = y[t-4]
    candidates["D:L.y:L2_equiv_y_L3"] = candidates["D:y:L3"]
    candidates["D:L.y:L3_equiv_y_L4"] = candidates["D:y:L4"]

    # Level-equation y-difference candidates.
    # These test the timing convention for the System-GMM level instrument.
    level_candidates = {
        "L:diff:y:current_y_t_minus_y_tminus1": (0, 1),
        "L:diff:y:lag1_y_tminus1_minus_y_tminus2": (1, 2),
        "L:diff:y:lag2_y_tminus2_minus_y_tminus3": (2, 3),
        "L:diff:y:lag3_y_tminus3_minus_y_tminus4": (3, 4),
        "L:diff:y:reverse_lag1_y_tminus2_minus_y_tminus1": (2, 1),
    }

    for name, (left_lag, right_lag) in level_candidates.items():
        z = np.zeros(len(meta), dtype=float)

        for i, (entity, time) in enumerate(zip(entity_arr, time_arr)):
            if not level_mask[i]:
                continue

            left = safe_lookup(y_map, entity, time - left_lag)
            right = safe_lookup(y_map, entity, time - right_lag)
            z[i] = left - right

        candidates[name] = z

    # Level-equation x-difference candidates for cross-checking.
    level_x_candidates = {
        "L:diff:x:current_x_t_minus_x_tminus1": (0, 1),
        "L:diff:x:lag1_x_tminus1_minus_x_tminus2": (1, 2),
        "L:diff:x:lag2_x_tminus2_minus_x_tminus3": (2, 3),
    }

    for name, (left_lag, right_lag) in level_x_candidates.items():
        z = np.zeros(len(meta), dtype=float)

        for i, (entity, time) in enumerate(zip(entity_arr, time_arr)):
            if not level_mask[i]:
                continue

            left = safe_lookup(x_map, entity, time - left_lag)
            right = safe_lookup(x_map, entity, time - right_lag)
            z[i] = left - right

        candidates[name] = z

    rows = []

    for name, z in candidates.items():
        ze = float(z @ u)

        diffs = np.abs(stata_ze - ze)
        closest_idx = int(np.argmin(diffs))

        rows.append({
            "candidate": name,
            "candidate_Ze": ze,
            "closest_stata_index": closest_idx + 1,
            "closest_stata_Ze": float(stata_ze[closest_idx]),
            "abs_diff": float(diffs[closest_idx]),
        })

    out = pd.DataFrame(rows).sort_values(["abs_diff", "candidate"]).reset_index(drop=True)

    out_path = ART / "lagged_y_candidate_matches.csv"
    out.to_csv(out_path, index=False)

    print("=" * 100)
    print("LAGGED-y / LEVEL-DIFF CANDIDATE MATCHES")
    print("=" * 100)
    print(out.head(30).to_string(index=False))
    print()
    print(f"Wrote: {out_path}")

    # Also print candidates closest to the remaining unmatched Stata rows:
    # r5 and r7 are the main unresolved targets after IV:w was fixed.
    for target_idx in [5, 7]:
        target = stata_ze[target_idx - 1]
        tmp = out.copy()
        tmp["target_stata_index"] = target_idx
        tmp["target_stata_Ze"] = target
        tmp["target_abs_diff"] = np.abs(tmp["candidate_Ze"] - target)
        tmp = tmp.sort_values("target_abs_diff").head(10)

        target_path = ART / f"lagged_y_candidates_for_stata_r{target_idx}.csv"
        tmp.to_csv(target_path, index=False)

        print()
        print("=" * 100)
        print(f"BEST CANDIDATES FOR STATA r{target_idx} = {target}")
        print("=" * 100)
        print(tmp[["candidate", "candidate_Ze", "target_stata_Ze", "target_abs_diff"]].to_string(index=False))
        print(f"Wrote: {target_path}")


if __name__ == "__main__":
    main()