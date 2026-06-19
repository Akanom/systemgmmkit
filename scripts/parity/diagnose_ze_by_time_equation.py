from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
ART = ROOT / "artifacts" / "parity" / "xtabond2"

Z_FILE = ART / "native_Z.csv"
U_FILE = ART / "native_u_at_stata_b.csv"
META_FILE = ART / "native_row_meta.csv"
INST_FILE = ART / "native_instrument_names.csv"


def main() -> None:
    Z = pd.read_csv(Z_FILE).to_numpy(float)
    u = pd.read_csv(U_FILE).to_numpy(float).reshape(-1, 1)
    meta = pd.read_csv(META_FILE)
    inst = pd.read_csv(INST_FILE)["instrument_name"].tolist()

    if Z.shape[0] != u.shape[0] or Z.shape[0] != len(meta):
        raise ValueError(f"Shape mismatch: Z={Z.shape}, u={u.shape}, meta={meta.shape}")

    rows = []

    for (equation, time), idx in meta.groupby(["equation", "time"], dropna=False).groups.items():
        mask = np.zeros(len(meta), dtype=bool)
        mask[list(idx)] = True

        ze = Z[mask, :].T @ u[mask, :]

        for j, value in enumerate(ze.reshape(-1), start=1):
            rows.append(
                {
                    "equation": equation,
                    "time": time,
                    "instrument_index": j,
                    "instrument_name": inst[j - 1] if j - 1 < len(inst) else "",
                    "Ze_contribution": float(value),
                    "n_rows": int(mask.sum()),
                }
            )

    out = pd.DataFrame(rows)
    out_path = ART / "native_Ze_at_stata_b_by_equation_time.csv"
    out.to_csv(out_path, index=False)

    pivot = out.pivot_table(
        index=["equation", "time"],
        columns="instrument_name",
        values="Ze_contribution",
        aggfunc="sum",
        fill_value=0.0,
    ).reset_index()

    pivot_path = ART / "native_Ze_at_stata_b_by_equation_time_pivot.csv"
    pivot.to_csv(pivot_path, index=False)

    print("=" * 100)
    print("Ze AT STATA b BY EQUATION/TIME")
    print("=" * 100)
    print(pivot.to_string(index=False))
    print()
    print(f"Wrote: {out_path}")
    print(f"Wrote: {pivot_path}")


if __name__ == "__main__":
    main()
