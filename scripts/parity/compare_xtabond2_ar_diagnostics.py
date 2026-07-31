from __future__ import annotations

import hashlib
from pathlib import Path
from typing import TypedDict

import numpy as np
import pandas as pd

BASE = Path("artifacts/parity/xtabond2")
COEF_TOL = 1e-6
AR_Z_TOL = 0.10
AR_P_TOL = 0.03
OVERID_STAT_TOL = 1e-6
OVERID_P_TOL = 1e-6


class SpecConfig(TypedDict):
    native_params: Path
    native_diagnostics: Path
    stata_params: Path
    stata_diagnostics: Path
    data: Path
    do_file: Path
    expected_params: frozenset[str]
    expected_nobs: int
    expected_n_groups: int
    expected_n_instruments: int
    expected_overid_df: int
    max_rel_se_diff: float


SPECS: dict[str, SpecConfig] = {
    "system_gmm_baseline_controls": {
        "native_params": BASE
        / "specs"
        / "system_gmm_baseline_controls"
        / "windmeijer"
        / "native_params.csv",
        "native_diagnostics": BASE
        / "specs"
        / "system_gmm_baseline_controls"
        / "windmeijer"
        / "native_diagnostics.csv",
        "stata_params": BASE / "xtabond2_system_gmm_params.csv",
        "stata_diagnostics": BASE / "xtabond2_system_gmm_diagnostics.csv",
        "data": BASE / "system_gmm_benchmark.csv",
        "do_file": BASE / "system_gmm_xtabond2_parity.do",
        "expected_params": frozenset({"L1.y", "x", "w", "_con"}),
        "expected_nobs": 1248,
        "expected_n_groups": 96,
        "expected_n_instruments": 8,
        "expected_overid_df": 4,
        "max_rel_se_diff": 1e-6,
    },
    "system_gmm_no_controls": {
        "native_params": BASE / "specs" / "system_gmm_no_controls" / "native_params.csv",
        "native_diagnostics": BASE / "specs" / "system_gmm_no_controls" / "native_diagnostics.csv",
        "stata_params": BASE / "specs" / "system_gmm_no_controls" / "stata_params.csv",
        "stata_diagnostics": BASE / "specs" / "system_gmm_no_controls" / "stata_diagnostics.csv",
        "data": BASE / "specs" / "system_gmm_no_controls" / "system_gmm_no_controls_benchmark.csv",
        "do_file": BASE / "specs" / "system_gmm_no_controls" / "system_gmm_no_controls.do",
        "expected_params": frozenset({"L1.y", "x", "_con"}),
        "expected_nobs": 1248,
        "expected_n_groups": 96,
        "expected_n_instruments": 7,
        "expected_overid_df": 4,
        "max_rel_se_diff": 1e-3,
    },
    "system_gmm_three_way_controls": {
        "native_params": BASE / "specs" / "system_gmm_three_way_controls" / "native_params.csv",
        "native_diagnostics": BASE
        / "specs"
        / "system_gmm_three_way_controls"
        / "native_diagnostics.csv",
        "stata_params": BASE / "specs" / "system_gmm_three_way_controls" / "stata_params.csv",
        "stata_diagnostics": BASE
        / "specs"
        / "system_gmm_three_way_controls"
        / "stata_diagnostics.csv",
        "data": BASE
        / "specs"
        / "system_gmm_three_way_controls"
        / "system_gmm_three_way_controls_benchmark.csv",
        "do_file": BASE
        / "specs"
        / "system_gmm_three_way_controls"
        / "system_gmm_three_way_controls.do",
        "expected_params": frozenset(
            {
                "L1.y",
                "x",
                "frag",
                "polity",
                "x_frag",
                "x_polity",
                "frag_polity",
                "x_frag_polity",
                "w",
                "_con",
            }
        ),
        "expected_nobs": 1248,
        "expected_n_groups": 96,
        "expected_n_instruments": 16,
        "expected_overid_df": 6,
        "max_rel_se_diff": 1e-5,
    },
    "system_gmm_decomposition_controls": {
        "native_params": BASE / "specs" / "system_gmm_decomposition_controls" / "native_params.csv",
        "native_diagnostics": BASE
        / "specs"
        / "system_gmm_decomposition_controls"
        / "native_diagnostics.csv",
        "stata_params": BASE / "specs" / "system_gmm_decomposition_controls" / "stata_params.csv",
        "stata_diagnostics": BASE
        / "specs"
        / "system_gmm_decomposition_controls"
        / "stata_diagnostics.csv",
        "data": BASE
        / "specs"
        / "system_gmm_decomposition_controls"
        / "system_gmm_decomposition_controls_benchmark.csv",
        "do_file": BASE
        / "specs"
        / "system_gmm_decomposition_controls"
        / "system_gmm_decomposition_controls.do",
        "expected_params": frozenset({"L1.y", "x_long", "x_short", "w", "c1", "_con"}),
        "expected_nobs": 1248,
        "expected_n_groups": 96,
        "expected_n_instruments": 12,
        "expected_overid_df": 6,
        "max_rel_se_diff": 1e-6,
    },
}


def _read_one(path: Path) -> pd.Series:
    if not path.exists():
        raise FileNotFoundError(path)
    frame = pd.read_csv(path)
    if len(frame) != 1:
        raise ValueError(f"Expected exactly one diagnostic row in {path}, found {len(frame)}")
    return frame.iloc[0]


def _read_params(path: Path, *, stata: bool) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    frame = pd.read_csv(path)
    if stata:
        frame = frame.rename(columns={"parm": "param", "estimate": "coef", "stderr": "std_err"})
        frame["param"] = frame["param"].replace({"L.y": "L1.y", "_cons": "_con"})
    else:
        frame = frame.rename(columns={"native_coef": "coef", "native_std_err": "std_err"})

    required = {"param", "coef", "std_err"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"Missing required parameter columns in {path}: {sorted(missing)}")

    result = frame[["param", "coef", "std_err"]].copy()
    result["param"] = result["param"].astype(str).str.strip()
    result["coef"] = pd.to_numeric(result["coef"], errors="coerce")
    result["std_err"] = pd.to_numeric(result["std_err"], errors="coerce")
    return result


def _number(row: pd.Series, name: str) -> float:
    if name not in row.index or pd.isna(row[name]):
        raise ValueError(f"Missing required diagnostic {name!r}")
    value = float(row[name])
    if not np.isfinite(value):
        raise ValueError(f"Non-finite required diagnostic {name!r}: {value}")
    return value


def _integer(row: pd.Series, name: str) -> int:
    value = _number(row, name)
    if not value.is_integer():
        raise ValueError(f"Required count {name!r} is not an integer: {value}")
    return int(value)


def _probability(row: pd.Series, name: str) -> float:
    value = _number(row, name)
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"Required p-value {name!r} is outside [0, 1]: {value}")
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _parameter_result(paths: SpecConfig) -> dict[str, object]:
    native = _read_params(paths["native_params"], stata=False)
    stata = _read_params(paths["stata_params"], stata=True)
    expected_terms = set(paths["expected_params"])
    native_terms = set(native["param"])
    stata_terms = set(stata["param"])

    parameter_set_complete = (
        native["param"].is_unique
        and stata["param"].is_unique
        and len(native) == len(stata) == len(expected_terms)
        and native_terms == stata_terms == expected_terms
    )
    parameters_finite = bool(
        np.isfinite(native[["coef", "std_err"]].to_numpy(dtype=float)).all()
        and np.isfinite(stata[["coef", "std_err"]].to_numpy(dtype=float)).all()
    )
    standard_errors_positive = bool(native["std_err"].gt(0).all() and stata["std_err"].gt(0).all())

    merged = native.merge(stata, on="param", how="outer", suffixes=("_native", "_stata"))
    coef_diff = (merged["coef_native"] - merged["coef_stata"]).abs()
    relative_se_diff = (merged["std_err_native"] - merged["std_err_stata"]).abs() / merged[
        "std_err_stata"
    ].abs()
    max_abs_coef_diff = float(coef_diff.max(skipna=False))
    max_rel_se_diff = float(relative_se_diff.max(skipna=False))
    parameter_pass = (
        parameter_set_complete
        and parameters_finite
        and standard_errors_positive
        and np.isfinite(max_abs_coef_diff)
        and np.isfinite(max_rel_se_diff)
        and max_abs_coef_diff <= COEF_TOL
        and max_rel_se_diff <= paths["max_rel_se_diff"]
    )

    return {
        "expected_parameter_count": len(expected_terms),
        "native_parameter_count": len(native),
        "stata_parameter_count": len(stata),
        "expected_parameters": ";".join(sorted(expected_terms)),
        "native_parameters": ";".join(sorted(native_terms)),
        "stata_parameters": ";".join(sorted(stata_terms)),
        "parameter_set_complete": parameter_set_complete,
        "parameters_finite": parameters_finite,
        "standard_errors_positive": standard_errors_positive,
        "max_abs_coef_diff": max_abs_coef_diff,
        "coef_tol": COEF_TOL,
        "max_rel_se_diff": max_rel_se_diff,
        "se_rel_tol": paths["max_rel_se_diff"],
        "parameter_status": "PASS_PARAMETER_PARITY" if parameter_pass else "FAIL_PARAMETER_PARITY",
    }


def _compare_spec(spec: str, paths: SpecConfig) -> dict[str, object]:
    native = _read_one(paths["native_diagnostics"])
    stata = _read_one(paths["stata_diagnostics"])

    row: dict[str, object] = {
        "spec": spec,
        "native_params_path": paths["native_params"].as_posix(),
        "stata_params_path": paths["stata_params"].as_posix(),
        "native_diagnostics_path": paths["native_diagnostics"].as_posix(),
        "stata_diagnostics_path": paths["stata_diagnostics"].as_posix(),
        "data_sha256": _sha256(paths["data"]),
        "do_file_sha256": _sha256(paths["do_file"]),
        "native_params_sha256": _sha256(paths["native_params"]),
        "stata_params_sha256": _sha256(paths["stata_params"]),
        "native_diagnostics_sha256": _sha256(paths["native_diagnostics"]),
        "stata_diagnostics_sha256": _sha256(paths["stata_diagnostics"]),
        "stata_version": _number(stata, "stata_version"),
        "stata_reported_date": stata.get("stata_reported_date", stata.get("stata_run_date", "")),
        "stata_reported_time": stata.get("stata_reported_time", stata.get("stata_run_time", "")),
        "native_nobs": _integer(native, "native_nobs"),
        "stata_nobs": _integer(stata, "stata_nobs"),
        "native_n_groups": _integer(native, "native_n_groups"),
        "stata_n_groups": _integer(stata, "stata_n_groups"),
        "native_n_instruments": _integer(native, "native_n_instruments"),
        "stata_n_instruments": _integer(stata, "stata_n_instruments"),
        "native_overid_df": _integer(native, "native_overid_df"),
        "stata_hansen_df": _integer(stata, "stata_hansen_df"),
        "stata_sargan_df": _integer(stata, "stata_sargan_df"),
        "native_hansen": _number(native, "native_hansen_j_stat"),
        "stata_hansen": _number(stata, "stata_hansen"),
        "native_hansen_p": _probability(native, "native_hansen_p"),
        "stata_hansen_p": _probability(stata, "stata_hansen_p"),
        "native_sargan": _number(native, "native_sargan_j_stat"),
        "stata_sargan": _number(stata, "stata_sargan"),
        "native_sargan_p": _probability(native, "native_sargan_p"),
        "stata_sargan_p": _probability(stata, "stata_sargan_p"),
        "native_ar1_z": _number(native, "native_ar1_z"),
        "stata_ar1_z": _number(stata, "stata_ar1_z"),
        "native_ar1_p": _probability(native, "native_ar1_p"),
        "stata_ar1_p": _probability(stata, "stata_ar1_p"),
        "native_ar2_z": _number(native, "native_ar2_z"),
        "stata_ar2_z": _number(stata, "stata_ar2_z"),
        "native_ar2_p": _probability(native, "native_ar2_p"),
        "stata_ar2_p": _probability(stata, "stata_ar2_p"),
        **_parameter_result(paths),
    }

    row["same_nobs"] = row["native_nobs"] == row["stata_nobs"] == paths["expected_nobs"]
    row["same_n_groups"] = (
        row["native_n_groups"] == row["stata_n_groups"] == paths["expected_n_groups"]
    )
    row["same_instrument_count"] = (
        row["native_n_instruments"] == row["stata_n_instruments"] == paths["expected_n_instruments"]
    )
    row["same_overid_df"] = (
        row["native_overid_df"]
        == row["stata_hansen_df"]
        == row["stata_sargan_df"]
        == paths["expected_overid_df"]
    )
    for diagnostic in (
        "hansen",
        "hansen_p",
        "sargan",
        "sargan_p",
        "ar1_z",
        "ar1_p",
        "ar2_z",
        "ar2_p",
    ):
        row[f"abs_{diagnostic}_diff"] = abs(
            float(row[f"native_{diagnostic}"]) - float(row[f"stata_{diagnostic}"])
        )

    count_pass = all(
        bool(row[name])
        for name in (
            "same_nobs",
            "same_n_groups",
            "same_instrument_count",
            "same_overid_df",
        )
    )
    overid_pass = (
        float(row["abs_hansen_diff"]) <= OVERID_STAT_TOL
        and float(row["abs_hansen_p_diff"]) <= OVERID_P_TOL
        and float(row["abs_sargan_diff"]) <= OVERID_STAT_TOL
        and float(row["abs_sargan_p_diff"]) <= OVERID_P_TOL
    )
    ar_pass = (
        float(row["abs_ar1_z_diff"]) <= AR_Z_TOL
        and float(row["abs_ar1_p_diff"]) <= AR_P_TOL
        and float(row["abs_ar2_z_diff"]) <= AR_Z_TOL
        and float(row["abs_ar2_p_diff"]) <= AR_P_TOL
    )
    diagnostic_pass = count_pass and overid_pass and ar_pass
    parameter_pass = row["parameter_status"] == "PASS_PARAMETER_PARITY"
    row["count_status"] = "PASS" if count_pass else "FAIL"
    row["overid_status"] = "PASS" if overid_pass else "FAIL"
    row["ar_status"] = "PASS" if ar_pass else "FAIL"
    row["diagnostic_status"] = (
        "PASS_DIAGNOSTIC_PARITY" if diagnostic_pass else "FAIL_DIAGNOSTIC_PARITY"
    )
    row["status"] = (
        "PASS_XTABOND2_PARITY" if parameter_pass and diagnostic_pass else "FAIL_XTABOND2_PARITY"
    )
    return row


def main() -> None:
    rows = [_compare_spec(spec, paths) for spec, paths in SPECS.items()]
    frame = pd.DataFrame(rows)

    out_csv = BASE / "diagnostic_parity_certificate.csv"
    out_md = BASE / "diagnostic_parity_certificate.md"
    legacy_csv = BASE / "ar_diagnostics_comparison.csv"
    frame.to_csv(out_csv, index=False)
    frame.to_csv(legacy_csv, index=False)

    display_columns = [
        "spec",
        "parameter_set_complete",
        "parameters_finite",
        "standard_errors_positive",
        "max_abs_coef_diff",
        "max_rel_se_diff",
        "parameter_status",
        "same_nobs",
        "same_n_groups",
        "same_instrument_count",
        "same_overid_df",
        "abs_hansen_diff",
        "abs_hansen_p_diff",
        "abs_sargan_diff",
        "abs_sargan_p_diff",
        "abs_ar1_z_diff",
        "abs_ar1_p_diff",
        "abs_ar2_z_diff",
        "abs_ar2_p_diff",
        "diagnostic_status",
        "status",
    ]
    report = [
        "# xtabond2 System GMM Unified Parity Certificate",
        "",
        "This certificate compares native SystemGMMKit with Stata `xtabond2` on four",
        "maintained, specification-aligned fixtures. Claims are benchmark-specific.",
        "",
        frame[display_columns].to_markdown(index=False),
        "",
        "## Gates",
        "",
        "- expected parameter sets: exact and unique; coefficients and standard errors: finite",
        "- standard errors: strictly positive",
        f"- coefficient absolute differences: `<= {COEF_TOL:g}`",
        "- Windmeijer standard-error relative differences: specification-specific",
        "  tolerances recorded in `se_rel_tol`",
        "- observations, groups, instruments, and overidentification degrees of freedom: exact",
        f"- Hansen/Sargan statistic and p-value absolute differences: `<= {OVERID_STAT_TOL:g}`",
        f"- signed AR(1)/AR(2) z-statistic absolute differences: `<= {AR_Z_TOL:g}`",
        f"- AR(1)/AR(2) p-value absolute differences: `<= {AR_P_TOL:g}`",
        "",
        "Overall status passes only when both parameter and diagnostic gates pass.",
        "SHA-256 hashes bind the certificate to the fixture, do-file, and exact native",
        "and Stata parameter and diagnostic exports. The Stata-reported date and time",
        "are retained as informational metadata only and are not conformity gates.",
        "",
    ]
    out_md.write_text("\n".join(report), encoding="utf-8")

    print(frame[display_columns].to_string(index=False))
    print(f"\nWrote {out_csv}")
    print(f"Wrote {out_md}")
    if not frame["status"].eq("PASS_XTABOND2_PARITY").all():
        raise SystemExit("One or more System GMM parameter or diagnostic parity gates failed.")


if __name__ == "__main__":
    main()
