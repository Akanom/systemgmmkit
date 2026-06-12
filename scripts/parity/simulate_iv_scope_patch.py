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
STATA_ZE_FILE = ART / "stata_Ze.csv"


def main() -> None:
    Z = pd.read_csv(Z_FILE).to_numpy(float)
    u = pd.read_csv(U_FILE).to_numpy(float).reshape(-1, 1)
    meta = pd.read_csv(META_FILE)
    inst = pd.read_csv(INST_FILE)

    names = inst["instrument_name"].tolist()

    if "IV:w" not in names:
        raise SystemExit(f"IV:w not found. Instrument names: {names}")

    iv_idx = names.index("IV:w")

    Z_original = Z.copy()
    Z_patched = Z.copy()

    # Simulate correct iv(w, eq(level)) behavior:
    # zero IV:w on difference-equation rows.
    diff_mask = meta["equation"].astype(str).str.lower().eq("diff").to_numpy()
    Z_patched[diff_mask, iv_idx] = 0.0

    ze_original = Z_original.T @ u
    ze_patched = Z_patched.T @ u
    stata_ze = pd.read_csv(STATA_ZE_FILE).to_numpy(float).reshape(-1, 1)

    out = pd.DataFrame({
        "instrument_index": np.arange(1, len(names) + 1),
        "instrument_name": names,
        "native_original_Ze_at_stata_b": ze_original.reshape(-1),
        "native_after_iv_scope_patch_Ze_at_stata_b": ze_patched.reshape(-1),
    })

    out_path = ART / "simulate_iv_scope_patch_Ze.csv"
    out.to_csv(out_path, index=False)

    print("=" * 100)
    print("SIMULATED IV-SCOPE PATCH")
    print("=" * 100)
    print(out.to_string(index=False))
    print()

    print("=" * 100)
    print("STATA Ze")
    print("=" * 100)
    print(pd.DataFrame(stata_ze, columns=["stata_Ze"]).to_string(index=True))
    print()

    print(f"Wrote: {out_path}")

    print()
    print("Expected key check:")
    print("After patch, IV:w should be close to Stata r1 = -10.48920769645072")


if __name__ == "__main__":
    main()