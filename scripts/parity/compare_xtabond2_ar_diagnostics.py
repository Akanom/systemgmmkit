from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

if __package__:
    from .system_gmm_certification_registry import (
        REGISTRY_PATH,
        REPOSITORY_ROOT,
        SpecConfig,
        canonical_text_sha256,
        certification_registry_sha256,
        comparator_provenance_sha256,
        load_certification_registry,
        load_comparator_provenance,
        repository_path,
    )
else:
    from system_gmm_certification_registry import (
        REGISTRY_PATH,
        REPOSITORY_ROOT,
        SpecConfig,
        canonical_text_sha256,
        certification_registry_sha256,
        comparator_provenance_sha256,
        load_certification_registry,
        load_comparator_provenance,
        repository_path,
    )

BASE = REPOSITORY_ROOT / "artifacts" / "parity" / "xtabond2"
COMPARATOR_PATH = Path("scripts/parity/compare_xtabond2_ar_diagnostics.py")
COMPARATOR_ID = "systemgmmkit.xtabond2-parity-comparator-v3"
REGISTRY = load_certification_registry(REGISTRY_PATH)
REGISTRY_SHA256 = certification_registry_sha256(REGISTRY_PATH)
PROVENANCE = load_comparator_provenance(REGISTRY)
PROVENANCE_SHA256 = comparator_provenance_sha256(REGISTRY)
SPECS = REGISTRY.specifications
COEF_TOL = REGISTRY.tolerances.coefficient_absolute
AR_Z_TOL = REGISTRY.tolerances.ar_z_absolute
AR_P_TOL = REGISTRY.tolerances.ar_p_value_absolute
OVERID_STAT_TOL = REGISTRY.tolerances.overidentification_statistic_absolute
OVERID_P_TOL = REGISTRY.tolerances.overidentification_p_value_absolute


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


def _read_sample(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    frame = pd.read_csv(path)
    required = ["id", "t"]
    missing = set(required) - set(frame.columns)
    if missing:
        raise ValueError(f"Missing required sample columns in {path}: {sorted(missing)}")
    sample = frame[required].copy()
    if sample.isna().any().any():
        raise ValueError(f"Sample keys must not be missing in {path}.")
    if sample.duplicated(required).any():
        raise ValueError(f"Sample keys must be unique in {path}.")
    return sample.sort_values(required).reset_index(drop=True)


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


def _text(row: pd.Series, name: str) -> str:
    if name not in row.index or pd.isna(row[name]):
        raise ValueError(f"Missing required comparator metadata {name!r}")
    value = str(row[name]).strip()
    if not value:
        raise ValueError(f"Empty required comparator metadata {name!r}")
    return value


def _sha256(path: Path) -> str:
    return canonical_text_sha256(path)


def _embedded_comparator_metadata(stata: pd.Series) -> tuple[bool, bool | float]:
    fields = ("xtabond2_e_version", "xtabond2_ado_header")
    present = [field in stata.index and not pd.isna(stata[field]) for field in fields]
    if any(present) and not all(present):
        raise ValueError("Stata export has incomplete embedded xtabond2 provenance metadata.")
    if not all(present):
        return False, float("nan")
    matches = (
        _text(stata, "xtabond2_e_version") == PROVENANCE.xtabond2_e_version
        and _text(stata, "xtabond2_ado_header") == PROVENANCE.xtabond2_ado_header
    )
    return True, matches


def _parameter_result(paths: SpecConfig) -> dict[str, object]:
    native = _read_params(repository_path(paths["native_params"]), stata=False)
    stata = _read_params(repository_path(paths["stata_params"]), stata=True)
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
    native = _read_one(repository_path(paths["native_diagnostics"]))
    stata = _read_one(repository_path(paths["stata_diagnostics"]))
    native_spec = _text(native, "spec")
    stata_spec = _text(stata, "spec")
    embedded_provenance, embedded_provenance_matches = _embedded_comparator_metadata(stata)
    provenance_hashes = PROVENANCE.output_hashes[spec]
    stata_params_sha256 = _sha256(repository_path(paths["stata_params"]))
    stata_diagnostics_sha256 = _sha256(repository_path(paths["stata_diagnostics"]))
    sample_gate_applies = "native_sample" in paths and "stata_sample" in paths
    native_sample_path = repository_path(paths["native_sample"]) if sample_gate_applies else None
    stata_sample_path = repository_path(paths["stata_sample"]) if sample_gate_applies else None
    if sample_gate_applies:
        assert native_sample_path is not None and stata_sample_path is not None
        native_sample = _read_sample(native_sample_path)
        stata_sample = _read_sample(stata_sample_path)
        same_sample_keys = native_sample.equals(stata_sample)
        native_sample_count = len(native_sample)
        stata_sample_count = len(stata_sample)
        native_sample_sha256 = _sha256(native_sample_path)
        stata_sample_sha256 = _sha256(stata_sample_path)
        sample_hash_matches_provenance = (
            stata_sample_sha256 == provenance_hashes["stata_sample_sha256"]
        )
    else:
        same_sample_keys = True
        native_sample_count = 0
        stata_sample_count = 0
        native_sample_sha256 = None
        stata_sample_sha256 = None
        sample_hash_matches_provenance = True
    output_hashes_match_provenance = (
        stata_params_sha256 == provenance_hashes["stata_params_sha256"]
        and stata_diagnostics_sha256 == provenance_hashes["stata_diagnostics_sha256"]
        and sample_hash_matches_provenance
    )

    row: dict[str, object] = {
        "spec": spec,
        "native_spec": native_spec,
        "stata_spec": stata_spec,
        "same_spec_id": native_spec == stata_spec == spec,
        "native_params_path": paths["native_params"].as_posix(),
        "stata_params_path": paths["stata_params"].as_posix(),
        "native_diagnostics_path": paths["native_diagnostics"].as_posix(),
        "stata_diagnostics_path": paths["stata_diagnostics"].as_posix(),
        "sample_gate_applies": sample_gate_applies,
        "native_sample_path": paths["native_sample"].as_posix() if sample_gate_applies else None,
        "stata_sample_path": paths["stata_sample"].as_posix() if sample_gate_applies else None,
        "certification_registry_path": REGISTRY_PATH.relative_to(REPOSITORY_ROOT).as_posix(),
        "certification_registry_sha256": REGISTRY_SHA256,
        "comparator_provenance_path": REGISTRY.comparator_provenance.as_posix(),
        "comparator_provenance_sha256": PROVENANCE_SHA256,
        "comparator_id": COMPARATOR_ID,
        "comparator_sha256": _sha256(repository_path(COMPARATOR_PATH)),
        "text_digest_algorithm": REGISTRY.text_digest_algorithm,
        "provenance_attestation_kind": PROVENANCE.attestation_kind,
        "provenance_source_log_sha256": PROVENANCE.run_log_sha256,
        "data_sha256": _sha256(repository_path(paths["data"])),
        "do_file_sha256": _sha256(repository_path(paths["do_file"])),
        "builder_sha256": _sha256(repository_path(paths["builder"])),
        "runner_sha256": _sha256(repository_path(paths["runner"])),
        "support_files_sha256": (
            ";".join(
                f"{path.as_posix()}:{_sha256(repository_path(path))}"
                for path in paths.get("support_files", ())
            )
            or None
        ),
        "native_params_sha256": _sha256(repository_path(paths["native_params"])),
        "stata_params_sha256": stata_params_sha256,
        "native_diagnostics_sha256": _sha256(repository_path(paths["native_diagnostics"])),
        "stata_diagnostics_sha256": stata_diagnostics_sha256,
        "native_sample_sha256": native_sample_sha256,
        "stata_sample_sha256": stata_sample_sha256,
        "stata_output_hashes_match_provenance": output_hashes_match_provenance,
        "stata_export_provenance_embedded": embedded_provenance,
        "stata_export_provenance_matches_attestation": embedded_provenance_matches,
        "comparator_provenance_mode": (
            "embedded-export-plus-attestation"
            if embedded_provenance
            else "historical-log-derived-attestation"
        ),
        "expected_stata_version": REGISTRY.expected_stata_version,
        "stata_version": _number(stata, "stata_version"),
        "expected_xtabond2_e_version": REGISTRY.expected_xtabond2_e_version,
        "xtabond2_e_version": PROVENANCE.xtabond2_e_version,
        "expected_xtabond2_ado_header": REGISTRY.expected_xtabond2_ado_header,
        "xtabond2_ado_header": PROVENANCE.xtabond2_ado_header,
        "xtabond2_ado_sha256": PROVENANCE.xtabond2_ado_sha256,
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
        "native_sample_count": native_sample_count,
        "stata_sample_count": stata_sample_count,
        "same_sample_keys": same_sample_keys,
        **_parameter_result(paths),
    }

    row["same_nobs"] = row["native_nobs"] == row["stata_nobs"] == paths["expected_nobs"]
    row["same_stata_version"] = (
        row["stata_version"] == PROVENANCE.stata_version == row["expected_stata_version"]
    )
    row["same_xtabond2_e_version"] = row["xtabond2_e_version"] == row["expected_xtabond2_e_version"]
    row["same_xtabond2_ado_header"] = (
        row["xtabond2_ado_header"] == row["expected_xtabond2_ado_header"]
    )
    row["same_n_groups"] = (
        row["native_n_groups"] == row["stata_n_groups"] == paths["expected_n_groups"]
    )
    row["same_instrument_count"] = (
        row["native_n_instruments"] == row["stata_n_instruments"] == paths["expected_instruments"]
    )
    row["same_overid_df"] = (
        row["native_overid_df"]
        == row["stata_hansen_df"]
        == row["stata_sargan_df"]
        == paths["expected_df"]
    )
    row["stata_hansen_reject_005"] = float(row["stata_hansen_p"]) < 0.05
    row["stata_sargan_reject_005"] = float(row["stata_sargan_p"]) < 0.05
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
            "same_spec_id",
            "same_n_groups",
            "same_instrument_count",
            "same_overid_df",
        )
    )
    sample_pass = not sample_gate_applies or (
        same_sample_keys
        and native_sample_count == stata_sample_count == paths["expected_nobs"]
        and sample_hash_matches_provenance
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
    comparator_pass = all(
        bool(row[name])
        for name in (
            "same_stata_version",
            "same_xtabond2_e_version",
            "same_xtabond2_ado_header",
            "stata_output_hashes_match_provenance",
        )
    ) and (not embedded_provenance or embedded_provenance_matches is True)
    diagnostic_pass = comparator_pass and count_pass and sample_pass and overid_pass and ar_pass
    parameter_pass = row["parameter_status"] == "PASS_PARAMETER_PARITY"
    row["count_status"] = "PASS" if count_pass else "FAIL"
    row["sample_status"] = (
        "PASS_EXACT_SAMPLE_KEYS"
        if sample_gate_applies and sample_pass
        else "FAIL_SAMPLE_KEYS"
        if sample_gate_applies
        else "NOT_APPLICABLE"
    )
    row["comparator_status"] = "PASS" if comparator_pass else "FAIL"
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
        "same_spec_id",
        "same_stata_version",
        "same_xtabond2_e_version",
        "same_xtabond2_ado_header",
        "stata_output_hashes_match_provenance",
        "stata_export_provenance_embedded",
        "comparator_status",
        "same_nobs",
        "sample_gate_applies",
        "same_sample_keys",
        "sample_status",
        "same_n_groups",
        "same_instrument_count",
        "same_overid_df",
        "stata_hansen_p",
        "stata_hansen_reject_005",
        "stata_sargan_p",
        "stata_sargan_reject_005",
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
        f"This certificate compares native SystemGMMKit with Stata `xtabond2` on {len(SPECS)}",
        "maintained, specification-aligned fixtures. Claims are benchmark-specific.",
        "The maintained specification list and numerical gates come from",
        f"`{REGISTRY_PATH.relative_to(REPOSITORY_ROOT).as_posix()}`.",
        "Comparator identity is carried by the path-free, machine-generated provenance",
        f"attestation `{REGISTRY.comparator_provenance.as_posix()}`. Each tracked Stata",
        "diagnostic export embeds the comparator metadata; the attestation cross-checks it",
        "against allowlisted fields from the completed local run log and binds the exact export",
        "hashes. The source log is not committed because it contains machine-specific paths;",
        "its hash and this limitation are preserved in the attestation.",
        "",
        frame[display_columns].to_markdown(index=False),
        "",
        "## Gates",
        "",
        "- expected parameter sets: exact and unique; coefficients and standard errors: finite",
        "- standard errors: strictly positive",
        "- Stata and xtabond2 versions: exact match to the certification registry",
        f"- coefficient absolute differences: `<= {COEF_TOL:g}`",
        "- Windmeijer standard-error relative differences: specification-specific",
        "  tolerances recorded in `se_rel_tol`",
        "- observations, groups, instruments, and overidentification degrees of freedom: exact",
        "- exact `(id, t)` estimation-sample keys for specifications that declare sample artifacts",
        f"- Hansen/Sargan statistic and p-value absolute differences: `<= {OVERID_STAT_TOL:g}`",
        f"- signed AR(1)/AR(2) z-statistic absolute differences: `<= {AR_Z_TOL:g}`",
        f"- AR(1)/AR(2) p-value absolute differences: `<= {AR_P_TOL:g}`",
        "",
        "Overall status passes only when both parameter and diagnostic gates pass.",
        "Parity status means cross-software agreement on the maintained fixture; it does not",
        "endorse instrument validity or the model specification. The Stata Hansen/Sargan",
        "p-values and reject-at-0.05 flags are reported explicitly and are not parity gates.",
        "SHA-256 hashes bind the certificate to the registry, fixture, do-file, and exact",
        "native and Stata parameter and diagnostic exports. The Stata-reported date and time",
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
