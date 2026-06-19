import sys
from pathlib import Path

import pandas as pd

ROOT = Path("artifacts/parity/xtabond2")

coef_candidates = [
    ROOT / "xtabond2_native_system_gmm_coef_comparison.csv",
    ROOT / "system_gmm_fd_twostep_native_vs_xtabond2_coef_comparison.csv",
]

diag_candidates = [
    ROOT / "xtabond2_native_system_gmm_diagnostics_comparison.csv",
    ROOT / "system_gmm_fd_twostep_native_vs_xtabond2_diagnostics_comparison.csv",
]


def fail(msg: str) -> None:
    print(f"BLOCKED: {msg}")
    sys.exit(1)


def read_first_existing(paths):
    for p in paths:
        if p.exists():
            print(f"Using {p}")
            return p, pd.read_csv(p)
    fail("No certified parity comparison CSV found.")


coef_path, coef = read_first_existing(coef_candidates)
diag_path, diag = read_first_existing(diag_candidates)

print("\n=== Certified coefficient comparison columns ===")
print(list(coef.columns))

print("\n=== Certified diagnostics comparison columns ===")
print(list(diag.columns))

# Flexible threshold checks because historical comparison files have evolved.
coef_diff_cols = [c for c in coef.columns if "coef" in c.lower() and "diff" in c.lower()]

se_diff_cols = [
    c for c in coef.columns if ("se" in c.lower() or "std" in c.lower()) and "diff" in c.lower()
]

if not coef_diff_cols:
    fail(f"No coefficient-difference column found in {coef_path}")

for col in coef_diff_cols:
    max_diff = pd.to_numeric(coef[col], errors="coerce").abs().max()
    print(f"{col}: max={max_diff}")
    if pd.notna(max_diff) and max_diff > 1e-5:
        fail(f"certified coefficient parity exceeded tolerance in {col}: {max_diff}")

# SE tolerance may differ by file/history, but for Windmeijer-certified files this should be tight.
for col in se_diff_cols:
    max_diff = pd.to_numeric(coef[col], errors="coerce").abs().max()
    print(f"{col}: max={max_diff}")
    if pd.notna(max_diff) and max_diff > 1e-4:
        fail(f"certified SE parity exceeded tolerance in {col}: {max_diff}")

print("\nCERTIFIED PARITY GUARD: PASS")
