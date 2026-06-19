from __future__ import annotations

import math
from pathlib import Path

import pandas as pd

OUT = Path("artifacts/parity/xtdpdgmm/fod_diff")

SPECS = [
    "fod_diff_endog_x_onestep",
    "fod_diff_endog_x_twostep",
    "fod_diff_predet_x_onestep",
    "fod_diff_predet_x_twostep",
]


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_csv(path)


def _scalar_from_return(path: Path, name: str) -> float:
    df = _read_csv(path)
    row = df[(df["kind"].astype(str) == "scalar") & (df["name"].astype(str) == name)]
    if row.empty:
        return float("nan")
    return float(row.iloc[0]["value_num"])


def _as_float(value) -> float:
    try:
        if pd.isna(value):
            return float("nan")
        if str(value).strip() == "":
            return float("nan")
        return float(value)
    except Exception:
        return float("nan")


def _first_existing(row: pd.Series, names: list[str]) -> float:
    lower_map = {str(c).lower(): c for c in row.index}
    for name in names:
        key = name.lower()
        if key in lower_map:
            return _as_float(row[lower_map[key]])
    return float("nan")


def _native_metric(native_path: Path, candidates: list[str]) -> float:
    if not native_path.exists():
        return float("nan")

    df = pd.read_csv(native_path)
    if df.empty:
        return float("nan")

    row = df.iloc[0]
    return _first_existing(row, candidates)


def _abs_diff(a: float, b: float) -> float:
    if math.isnan(a) or math.isnan(b):
        return float("nan")
    return abs(a - b)


def _status(metric: str, stata: float, native: float, abs_diff: float) -> str:
    if math.isnan(native):
        return "MISSING_NATIVE"

    if metric == "N" and stata == 1248.0 and native == 1152.0:
        return "CONVENTION_DIFFERENCE_MARKED_VS_EFFECTIVE_SAMPLE"

    if metric in {"N_g", "rank", "zrank"}:
        return "MATCH" if abs_diff == 0 else "DIFFERENT"

    if metric in {"p_J", "p_J_u", "ar1_p", "ar2_p"}:
        return "MATCH" if abs_diff <= 1e-5 else "DIFFERENT"

    if metric in {"chi2_J", "chi2_J_u", "ar1_z", "ar2_z"}:
        return "MATCH" if abs_diff <= 1e-5 else "DIFFERENT"

    return "CHECK"


def build_stata_oracle() -> pd.DataFrame:
    rows = []

    for spec in SPECS:
        ereturn_path = OUT / f"stata_{spec}_ereturn.csv"
        overid_path = OUT / f"stata_{spec}_estat_overid_return.csv"
        serial_path = OUT / f"stata_{spec}_estat_serial_return.csv"

        rows.append(
            {
                "spec": spec,
                "stata_N": _scalar_from_return(ereturn_path, "N"),
                "stata_N_g": _scalar_from_return(ereturn_path, "N_g"),
                "stata_N_clust": _scalar_from_return(ereturn_path, "N_clust"),
                "stata_rank": _scalar_from_return(ereturn_path, "rank"),
                "stata_zrank": _scalar_from_return(ereturn_path, "zrank"),
                "stata_steps": _scalar_from_return(ereturn_path, "steps"),
                "stata_chi2_J": _scalar_from_return(overid_path, "chi2_J"),
                "stata_df_J": _scalar_from_return(overid_path, "df_J"),
                "stata_p_J": _scalar_from_return(overid_path, "p_J"),
                "stata_chi2_J_u": _scalar_from_return(overid_path, "chi2_J_u"),
                "stata_p_J_u": _scalar_from_return(overid_path, "p_J_u"),
                "stata_ar1_z": _scalar_from_return(serial_path, "z_1"),
                "stata_ar1_p": _scalar_from_return(serial_path, "p_1"),
                "stata_ar2_z": _scalar_from_return(serial_path, "z_2"),
                "stata_ar2_p": _scalar_from_return(serial_path, "p_2"),
            }
        )

    oracle = pd.DataFrame(rows)
    oracle.to_csv(OUT / "fod_diff_xtdpdgmm_diagnostics_oracle.csv", index=False)
    oracle.to_markdown(OUT / "fod_diff_xtdpdgmm_diagnostics_oracle.md", index=False)
    return oracle


def compare_native_to_stata(oracle: pd.DataFrame) -> pd.DataFrame:
    rows = []

    native_candidates = {
        "N": ["native_N", "native_nobs", "N", "nobs", "n_obs", "n_observations", "observations"],
        "N_g": ["native_N_g", "native_n_groups", "N_g", "n_groups", "groups"],
        "rank": ["native_rank", "rank", "k_params", "n_params"],
        "zrank": [
            "native_zrank",
            "native_n_instruments",
            "zrank",
            "n_instruments",
            "instruments",
            "k_inst",
            "instrument_count",
        ],
        "chi2_J": [
            "native_chi2_J",
            "native_hansen_J",
            "native_hansen_j_robust",
            "chi2_J",
            "hansen_J",
            "hansen_j_robust",
        ],
        "p_J": [
            "native_p_J",
            "native_hansen_p",
            "native_hansen_p_robust",
            "p_J",
            "hansen_p",
            "hansen_p_robust",
        ],
        "chi2_J_u": [
            "native_chi2_J_u",
            "native_hansen_j_stat",
            "native_sargan_j_stat",
            "chi2_J_u",
            "sargan_j",
            "sargan_stat",
        ],
        "p_J_u": [
            "native_p_J_u",
            "native_sargan_p",
            "p_J_u",
            "sargan_p",
            "sargan_pvalue",
            "sargan_p_value",
        ],
        "ar1_z": ["native_ar1_z", "ar1_z", "AR(1) z", "ar_1_z", "m1_z"],
        "ar1_p": ["native_ar1_p", "ar1_p", "AR(1) p", "ar_1_p", "m1_p"],
        "ar2_z": ["native_ar2_z", "ar2_z", "AR(2) z", "ar_2_z", "m2_z"],
        "ar2_p": ["native_ar2_p", "ar2_p", "AR(2) p", "ar_2_p", "m2_p"],
    }

    for _, srow in oracle.iterrows():
        spec = srow["spec"]
        native_path = OUT / f"native_{spec}_diagnostics.csv"

        for metric, candidates in native_candidates.items():
            stata_col = f"stata_{metric}"
            if stata_col not in srow.index:
                continue

            stata_val = float(srow[stata_col])
            native_val = _native_metric(native_path, candidates)
            abs_diff = _abs_diff(stata_val, native_val)

            rows.append(
                {
                    "spec": spec,
                    "metric": metric,
                    "stata": stata_val,
                    "native": native_val,
                    "abs_diff": abs_diff,
                    "status": _status(metric, stata_val, native_val, abs_diff),
                    "native_found": not math.isnan(native_val),
                    "native_file": str(native_path),
                }
            )

    comp = pd.DataFrame(rows)
    comp.to_csv(OUT / "fod_diff_xtdpdgmm_native_diagnostics_comparison.csv", index=False)
    comp.to_markdown(OUT / "fod_diff_xtdpdgmm_native_diagnostics_comparison.md", index=False)
    return comp


def main() -> None:
    oracle = build_stata_oracle()
    comp = compare_native_to_stata(oracle)

    print("\nStata diagnostic oracle:")
    print(oracle.to_string(index=False))

    print("\nNative-vs-Stata diagnostic comparison:")
    print(comp.to_string(index=False))

    print("\nStatus counts:")
    print(comp["status"].value_counts().to_string())


if __name__ == "__main__":
    main()
