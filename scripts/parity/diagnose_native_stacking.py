from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
ART = ROOT / "artifacts" / "parity" / "xtabond2"

Z_FILE = ART / "native_Z.csv"
U_FILE = ART / "native_u_stack.csv"
META_FILE = ART / "native_row_meta.csv"
INST_FILE = ART / "native_instrument_names.csv"
STATA_ZE_FILE = ART / "stata_Ze.csv"


def read_matrix(path: Path) -> np.ndarray:
    df = pd.read_csv(path)
    return df.to_numpy(dtype=float)


def read_vector(path: Path) -> np.ndarray:
    df = pd.read_csv(path)
    return df.to_numpy(dtype=float).reshape(-1, 1)


def main() -> None:
    Z = read_matrix(Z_FILE)
    u = read_vector(U_FILE)
    meta = pd.read_csv(META_FILE)

    if Z.shape[0] != u.shape[0]:
        raise ValueError(f"Z/u row mismatch: Z={Z.shape}, u={u.shape}")

    if Z.shape[0] != len(meta):
        raise ValueError(f"Z/meta row mismatch: Z rows={Z.shape[0]}, meta rows={len(meta)}")

    print("=" * 100)
    print("NATIVE STACKING SHAPE CHECK")
    print("=" * 100)
    print(f"Z shape:    {Z.shape}")
    print(f"u shape:    {u.shape}")
    print(f"meta shape: {meta.shape}")
    print()
    print("row_meta columns:")
    print(list(meta.columns))
    print()

    # Native total Ze
    native_ze = Z.T @ u

    stata_ze = None
    if STATA_ZE_FILE.exists():
        stata_ze = read_vector(STATA_ZE_FILE)

    if INST_FILE.exists():
        inst = pd.read_csv(INST_FILE)
        print("=" * 100)
        print("NATIVE INSTRUMENT NAMES")
        print("=" * 100)
        print(inst.to_string(index=False))
        print()

    print("=" * 100)
    print("TOTAL NATIVE Ze")
    print("=" * 100)
    print(pd.DataFrame(native_ze, columns=["native_Ze"]).to_string(index=False))
    print()

    if stata_ze is not None and stata_ze.shape == native_ze.shape:
        cmp = pd.DataFrame(
            {
                "row": np.arange(1, native_ze.shape[0] + 1),
                "native_Ze": native_ze.reshape(-1),
                "stata_Ze": stata_ze.reshape(-1),
                "diff": native_ze.reshape(-1) - stata_ze.reshape(-1),
                "abs_diff": np.abs(native_ze.reshape(-1) - stata_ze.reshape(-1)),
            }
        )
        cmp.to_csv(ART / "native_vs_stata_Ze_direct.csv", index=False)

        print("=" * 100)
        print("NATIVE VS STATA Ze DIRECT")
        print("=" * 100)
        print(cmp.to_string(index=False))
        print()

    # Detect useful grouping columns
    candidate_cols = [
        "equation",
        "eq",
        "equation_type",
        "row_type",
        "transform",
        "entity",
        "id",
        "time",
        "t",
        "period",
        "pos",
    ]

    available = [c for c in candidate_cols if c in meta.columns]

    print("=" * 100)
    print("AVAILABLE GROUPING COLUMNS")
    print("=" * 100)
    print(available)
    print()

    # Row counts by useful columns
    summaries = []

    for col in available:
        counts = (
            meta.groupby(col, dropna=False)
            .size()
            .reset_index(name="n_rows")
            .sort_values("n_rows", ascending=False)
        )
        out_path = ART / f"native_row_counts_by_{col}.csv"
        counts.to_csv(out_path, index=False)

        print("=" * 100)
        print(f"ROW COUNTS BY {col}")
        print("=" * 100)
        print(counts.head(30).to_string(index=False))
        print(f"Wrote: {out_path}")
        print()

        summaries.append((col, counts))

    # Ze contribution by equation-like columns
    equation_like = [
        c for c in ["equation", "eq", "equation_type", "row_type", "transform"] if c in meta.columns
    ]

    for col in equation_like:
        rows = []

        for value, idx in meta.groupby(col, dropna=False).groups.items():
            mask = np.zeros(len(meta), dtype=bool)
            mask[list(idx)] = True

            z_g = Z[mask, :]
            u_g = u[mask, :]
            ze_g = z_g.T @ u_g

            for j, val in enumerate(ze_g.reshape(-1), start=1):
                rows.append(
                    {
                        col: value,
                        "instrument_index": j,
                        "Ze_contribution": float(val),
                        "n_rows": int(mask.sum()),
                    }
                )

        out = pd.DataFrame(rows)
        out_path = ART / f"native_Ze_by_{col}.csv"
        out.to_csv(out_path, index=False)

        print("=" * 100)
        print(f"Ze CONTRIBUTION BY {col}")
        print("=" * 100)
        print(out.to_string(index=False))
        print(f"Wrote: {out_path}")
        print()

    # Export first rows for manual inspection
    preview = meta.head(50).copy()
    preview.to_csv(ART / "native_row_meta_preview.csv", index=False)

    print("=" * 100)
    print("DONE")
    print("=" * 100)
    print(f"Wrote: {ART / 'native_row_meta_preview.csv'}")


if __name__ == "__main__":
    main()
