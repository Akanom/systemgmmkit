from __future__ import annotations

from pathlib import Path

import pandas as pd
from scipy import stats

BASE = Path("artifacts/parity/xtabond2")

SPECS = {
    "system_gmm_baseline_controls": {
        "native": [
            BASE
            / "specs"
            / "system_gmm_baseline_controls"
            / "windmeijer"
            / "native_diagnostics.csv",
        ],
        "stata": [
            BASE
            / "specs"
            / "system_gmm_baseline_controls"
            / "windmeijer"
            / "stata_diagnostics.csv",
            BASE / "xtabond2_system_gmm_diagnostics.csv",
            BASE / "xtabond2_internal_diagnostics.csv",
        ],
    },
    "system_gmm_no_controls": {
        "native": [
            BASE / "specs" / "system_gmm_no_controls" / "native_diagnostics.csv",
        ],
        "stata": [
            BASE / "specs" / "system_gmm_no_controls" / "stata_diagnostics.csv",
        ],
    },
    "system_gmm_three_way_controls": {
        "native": [
            BASE / "specs" / "system_gmm_three_way_controls" / "native_diagnostics.csv",
        ],
        "stata": [
            BASE / "specs" / "system_gmm_three_way_controls" / "stata_diagnostics.csv",
        ],
    },
    "system_gmm_decomposition_controls": {
        "native": [
            BASE / "specs" / "system_gmm_decomposition_controls" / "native_diagnostics.csv",
        ],
        "stata": [
            BASE / "specs" / "system_gmm_decomposition_controls" / "stata_diagnostics.csv",
        ],
    },
}


def _first_existing(paths: list[Path]) -> Path | None:
    for path in paths:
        if path.exists():
            return path
    return None


def _z_abs_from_two_sided_p(p: float | None) -> float | None:
    if p is None or pd.isna(p):
        return None
    p = float(p)
    if not (0 < p <= 1):
        return None
    return float(stats.norm.isf(p / 2.0))


def _get_float(row: pd.Series, names: list[str]) -> float:
    for name in names:
        if name in row.index and not pd.isna(row[name]):
            return float(row[name])
    raise KeyError(f"None of these columns were found: {names}")


rows = []

for spec, paths in SPECS.items():
    native_path = _first_existing(paths["native"])
    stata_path = _first_existing(paths["stata"])

    if native_path is None or stata_path is None:
        rows.append(
            {
                "spec": spec,
                "status": "MISSING_ARTIFACTS",
                "native_path": "" if native_path is None else str(native_path),
                "stata_path": "" if stata_path is None else str(stata_path),
            }
        )
        continue

    try:
        native = pd.read_csv(native_path).iloc[0]
        stata = pd.read_csv(stata_path).iloc[0]

        native_ar1_p = _get_float(native, ["native_ar1_p", "ar1_p"])
        native_ar2_p = _get_float(native, ["native_ar2_p", "ar2_p"])
        stata_ar1_p = _get_float(stata, ["stata_ar1_p", "ar1_p", "ar1p"])
        stata_ar2_p = _get_float(stata, ["stata_ar2_p", "ar2_p", "ar2p"])

        native_ar1_abs_z = _z_abs_from_two_sided_p(native_ar1_p)
        stata_ar1_abs_z = _z_abs_from_two_sided_p(stata_ar1_p)
        native_ar2_abs_z = _z_abs_from_two_sided_p(native_ar2_p)
        stata_ar2_abs_z = _z_abs_from_two_sided_p(stata_ar2_p)

        rows.append(
            {
                "spec": spec,
                "status": "COMPARISON_GENERATED",
                "native_path": str(native_path),
                "stata_path": str(stata_path),
                "native_ar1_p": native_ar1_p,
                "stata_ar1_p": stata_ar1_p,
                "ar1_abs_p_diff": abs(native_ar1_p - stata_ar1_p),
                "native_ar1_abs_z": native_ar1_abs_z,
                "stata_ar1_abs_z": stata_ar1_abs_z,
                "ar1_abs_z_diff": abs(native_ar1_abs_z - stata_ar1_abs_z),
                "native_ar2_p": native_ar2_p,
                "stata_ar2_p": stata_ar2_p,
                "ar2_abs_p_diff": abs(native_ar2_p - stata_ar2_p),
                "native_ar2_abs_z": native_ar2_abs_z,
                "stata_ar2_abs_z": stata_ar2_abs_z,
                "ar2_abs_z_diff": abs(native_ar2_abs_z - stata_ar2_abs_z),
            }
        )
    except Exception as exc:
        rows.append(
            {
                "spec": spec,
                "status": "COMPARISON_FAILED",
                "native_path": str(native_path),
                "stata_path": str(stata_path),
                "message": str(exc),
            }
        )

out = BASE / "ar_diagnostics_comparison.csv"
df = pd.DataFrame(rows)
df.to_csv(out, index=False)

print(df.to_string(index=False))
print(f"\nWrote {out}")
