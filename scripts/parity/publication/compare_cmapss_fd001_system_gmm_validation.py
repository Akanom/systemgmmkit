from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(r"C:\Users\omoko\OneDrive\Desktop - Copy\Publication_papers")
BASE = ROOT / "artifacts" / "parity" / "publication" / "cmapss_fd001"
MODELS = ["risk", "degradation"]


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_csv(path)


def value(row: pd.Series, candidates: list[str]) -> float:
    for name in candidates:
        if name in row.index:
            val = row[name]
            if pd.notna(val):
                return float(val)
    return np.nan


def normalize_param_name(s: str) -> str:
    s = str(s)
    s = s.replace("L.", "L1.")
    if s == "_cons":
        return "_con"
    return s


def compare_model(model: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    model_dir = BASE / model

    native_params = read_csv(model_dir / "native_params.csv")
    stata_params = read_csv(model_dir / "stata_params.csv")
    native_diag = read_csv(model_dir / "native_diagnostics.csv").iloc[0]
    stata_diag = read_csv(model_dir / "stata_diagnostics.csv").iloc[0]

    native_params["param"] = native_params["param"].map(normalize_param_name)
    stata_params["param"] = stata_params["param"].map(normalize_param_name)

    coef = native_params.merge(
        stata_params,
        on="param",
        how="outer",
        indicator=True,
    )

    for col in ["native_coef", "native_std_err", "stata_coef", "stata_std_err"]:
        coef[col] = pd.to_numeric(coef[col], errors="coerce")

    coef["coef_abs_diff"] = (coef["native_coef"] - coef["stata_coef"]).abs()
    coef["se_abs_diff"] = (coef["native_std_err"] - coef["stata_std_err"]).abs()

    coef["coef_tolerance"] = 1e-4
    coef["se_tolerance"] = 1e-3

    coef["coef_status"] = np.where(
        (coef["_merge"] == "both") & (coef["coef_abs_diff"] <= coef["coef_tolerance"]),
        "PASS",
        "CHECK",
    )
    coef["se_status"] = np.where(
        (coef["_merge"] == "both") & (coef["se_abs_diff"] <= coef["se_tolerance"]),
        "PASS",
        "CHECK",
    )

    diag_rows = [
        {
            "metric": "nobs",
            "native": value(native_diag, ["native_nobs"]),
            "stata": value(stata_diag, ["stata_nobs"]),
            "tolerance": 0.0,
        },
        {
            "metric": "n_instruments",
            "native": value(native_diag, ["native_n_instruments"]),
            "stata": value(stata_diag, ["stata_n_instruments"]),
            "tolerance": 0.0,
        },
        {
            "metric": "sargan_j_stat",
            "native": value(native_diag, ["native_sargan_j_stat"]),
            "stata": value(stata_diag, ["stata_sargan"]),
            "tolerance": 1e-3,
        },
        {
            "metric": "sargan_p",
            "native": value(native_diag, ["native_sargan_p"]),
            "stata": value(stata_diag, ["stata_sargan_p"]),
            "tolerance": 1e-3,
        },
        {
            "metric": "hansen_j_stat",
            "native": value(native_diag, ["native_hansen_j_stat"]),
            "stata": value(stata_diag, ["stata_hansen"]),
            "tolerance": 1e-3,
        },
        {
            "metric": "hansen_p",
            "native": value(native_diag, ["native_hansen_p"]),
            "stata": value(stata_diag, ["stata_hansen_p"]),
            "tolerance": 1e-3,
        },
        {
            "metric": "ar1_z",
            "native": value(native_diag, ["native_ar1_z"]),
            "stata": value(stata_diag, ["stata_ar1"]),
            "tolerance": 1e-1,
        },
        {
            "metric": "ar1_p",
            "native": value(native_diag, ["native_ar1_p"]),
            "stata": value(stata_diag, ["stata_ar1_p"]),
            "tolerance": 1e-2,
        },
        {
            "metric": "ar2_z",
            "native": value(native_diag, ["native_ar2_z"]),
            "stata": value(stata_diag, ["stata_ar2"]),
            "tolerance": 1e-1,
        },
        {
            "metric": "ar2_p",
            "native": value(native_diag, ["native_ar2_p"]),
            "stata": value(stata_diag, ["stata_ar2_p"]),
            "tolerance": 1e-2,
        },
    ]

    diag = pd.DataFrame(diag_rows)
    diag["abs_diff"] = (diag["native"] - diag["stata"]).abs()
    diag["status"] = np.where(diag["abs_diff"] <= diag["tolerance"], "PASS", "CHECK")

    coef.insert(0, "model", model)
    diag.insert(0, "model", model)

    return coef, diag


def main() -> None:
    coef_frames = []
    diag_frames = []

    for model in MODELS:
        coef, diag = compare_model(model)
        coef_frames.append(coef)
        diag_frames.append(diag)

        print()
        print("=" * 100)
        print(f"CMAPSS FD001 validation: {model}")
        print("=" * 100)

        print()
        print("COEFFICIENTS")
        print(coef.to_string(index=False))

        print()
        print("DIAGNOSTICS")
        print(diag.to_string(index=False))

    coef_all = pd.concat(coef_frames, ignore_index=True)
    diag_all = pd.concat(diag_frames, ignore_index=True)

    coef_out = BASE / "cmapss_fd001_system_gmm_coef_comparison.csv"
    diag_out = BASE / "cmapss_fd001_system_gmm_diagnostics_comparison.csv"
    report_out = BASE / "cmapss_fd001_system_gmm_publication_validation_report.md"

    coef_all.to_csv(coef_out, index=False)
    diag_all.to_csv(diag_out, index=False)

    report = []
    report.append("# CMAPSS FD001 System GMM publication validation")
    report.append("")
    report.append("## Coefficient comparison")
    report.append("")
    report.append(coef_all.to_markdown(index=False))
    report.append("")
    report.append("## Diagnostic comparison")
    report.append("")
    report.append(diag_all.to_markdown(index=False))
    report.append("")

    report_out.write_text("\n".join(report), encoding="utf-8")

    print()
    print("WROTE:")
    print(coef_out)
    print(diag_out)
    print(report_out)

    hard_fail = diag_all[
        (diag_all["metric"].isin(["nobs", "n_instruments"]))
        & (diag_all["status"] != "PASS")
    ]

    if not hard_fail.empty:
        raise SystemExit(
            "Hard diagnostic mismatch on N/instruments:\n"
            + hard_fail.to_string(index=False)
        )


if __name__ == "__main__":
    main()
