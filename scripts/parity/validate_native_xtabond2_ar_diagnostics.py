from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path("artifacts/parity/xtabond2")

SPECS = {
    "system_gmm_baseline_controls": {
        "native_root": BASE / "specs" / "system_gmm_baseline_controls",
        "stata": BASE / "xtabond2_system_gmm_diagnostics.csv",
    },
    "system_gmm_no_controls": {
        "native_root": BASE / "specs" / "system_gmm_no_controls",
        "stata": BASE / "specs" / "system_gmm_no_controls" / "stata_diagnostics.csv",
    },
    "system_gmm_three_way_controls": {
        "native_root": BASE / "specs" / "system_gmm_three_way_controls",
        "stata": BASE / "specs" / "system_gmm_three_way_controls" / "stata_diagnostics.csv",
    },
    "system_gmm_decomposition_controls": {
        "native_root": BASE / "specs" / "system_gmm_decomposition_controls",
        "stata": BASE / "specs" / "system_gmm_decomposition_controls" / "stata_diagnostics.csv",
    },
}


def _find_native_diagnostics(root: Path) -> Path:
    preferred = root / "windmeijer" / "native_diagnostics.csv"
    if preferred.exists():
        return preferred

    direct = root / "native_diagnostics.csv"
    if direct.exists():
        return direct

    matches = sorted(root.rglob("native_diagnostics.csv"))
    if not matches:
        raise FileNotFoundError(f"No native_diagnostics.csv found under {root}")

    return matches[0]


def _read_one(path: Path) -> pd.Series:
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_csv(path).iloc[0]


def _as_float(row: pd.Series, name: str) -> float:
    if name not in row:
        return np.nan
    return float(row[name])


def main() -> None:
    rows: list[dict[str, object]] = []

    for spec, paths in SPECS.items():
        native_path = _find_native_diagnostics(paths["native_root"])
        stata_path = paths["stata"]

        native = _read_one(native_path)
        stata = _read_one(stata_path)

        row = {
            "spec": spec,
            "native_path": str(native_path),
            "stata_path": str(stata_path),
            "native_nobs": _as_float(native, "native_nobs"),
            "stata_nobs": _as_float(stata, "stata_nobs"),
            "native_n_instruments": _as_float(native, "native_n_instruments"),
            "stata_n_instruments": _as_float(stata, "stata_n_instruments"),
            "native_hansen_p": _as_float(native, "native_hansen_p"),
            "stata_hansen_p": _as_float(stata, "stata_hansen_p"),
            "native_ar1": _as_float(native, "native_ar1"),
            "stata_ar1": _as_float(stata, "stata_ar1"),
            "native_ar1_p": _as_float(native, "native_ar1_p"),
            "stata_ar1_p": _as_float(stata, "stata_ar1_p"),
            "native_ar2": _as_float(native, "native_ar2"),
            "stata_ar2": _as_float(stata, "stata_ar2"),
            "native_ar2_p": _as_float(native, "native_ar2_p"),
            "stata_ar2_p": _as_float(stata, "stata_ar2_p"),
        }

        row["same_nobs"] = row["native_nobs"] == row["stata_nobs"]
        row["same_instrument_count"] = (
            row["native_n_instruments"] == row["stata_n_instruments"]
        )

        row["abs_hansen_p_diff"] = abs(row["native_hansen_p"] - row["stata_hansen_p"])
        row["abs_ar1_diff"] = abs(row["native_ar1"] - row["stata_ar1"])
        row["abs_ar1_p_diff"] = abs(row["native_ar1_p"] - row["stata_ar1_p"])
        row["abs_ar2_diff"] = abs(row["native_ar2"] - row["stata_ar2"])
        row["abs_ar2_p_diff"] = abs(row["native_ar2_p"] - row["stata_ar2_p"])

        row["ar_status"] = (
            "PASS_AR_PARITY"
            if (
                row["abs_ar1_diff"] <= 0.10
                and row["abs_ar1_p_diff"] <= 0.03
                and row["abs_ar2_diff"] <= 0.10
                and row["abs_ar2_p_diff"] <= 0.03
            )
            else "REVIEW_AR_PARITY"
        )

        rows.append(row)

    out = pd.DataFrame(rows)

    out_path = BASE / "native_xtabond2_ar_diagnostics_validation.csv"
    out.to_csv(out_path, index=False)

    cols = [
        "spec",
        "same_nobs",
        "same_instrument_count",
        "native_ar1",
        "stata_ar1",
        "abs_ar1_diff",
        "native_ar1_p",
        "stata_ar1_p",
        "abs_ar1_p_diff",
        "native_ar2",
        "stata_ar2",
        "abs_ar2_diff",
        "native_ar2_p",
        "stata_ar2_p",
        "abs_ar2_p_diff",
        "ar_status",
    ]

    print(out[cols].to_string(index=False))
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()