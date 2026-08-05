from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from scripts.parity.system_gmm_certification_registry import (
    REGISTRY_PATH,
    SpecConfig,
    canonical_text_sha256,
    certification_registry_sha256,
    comparator_provenance_sha256,
    load_certification_registry,
    load_comparator_provenance,
)

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "artifacts" / "parity" / "xtabond2"
REGISTRY = load_certification_registry(REGISTRY_PATH)
PROVENANCE = load_comparator_provenance(REGISTRY)
SPECS = REGISTRY.specifications
COEF_TOL = REGISTRY.tolerances.coefficient_absolute
AR_Z_TOL = REGISTRY.tolerances.ar_z_absolute
AR_P_TOL = REGISTRY.tolerances.ar_p_value_absolute
OVERID_STAT_TOL = REGISTRY.tolerances.overidentification_statistic_absolute
OVERID_P_TOL = REGISTRY.tolerances.overidentification_p_value_absolute


def _repo(path: Path) -> Path:
    return ROOT / path


def _one(path: Path) -> pd.Series:
    frame = pd.read_csv(path)
    assert len(frame) == 1, path
    return frame.iloc[0]


def _sha256(path: Path) -> str:
    return canonical_text_sha256(path)


def _normalise_stata_params(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path).rename(
        columns={"parm": "param", "estimate": "stata_coef", "stderr": "stata_std_err"}
    )
    frame["param"] = frame["param"].replace({"L.y": "L1.y", "_cons": "_con"})
    return frame[["param", "stata_coef", "stata_std_err"]]


def _exact_int(value: object, label: str) -> int:
    number = float(value)
    assert np.isfinite(number), label
    assert number.is_integer(), label
    return int(number)


def _assert_parameter_gate(
    spec: str,
    paths: SpecConfig,
    native_path: Path,
) -> None:
    native = pd.read_csv(native_path)
    stata = _normalise_stata_params(_repo(paths["stata_params"]))

    assert native["param"].is_unique, spec
    assert stata["param"].is_unique, spec
    assert set(native["param"]) == set(stata["param"]) == set(paths["expected_params"]), spec

    merged = native.merge(stata, on="param", how="outer", indicator=True)
    assert merged["_merge"].eq("both").all(), spec
    assert len(merged) == len(native) == len(stata) == len(paths["expected_params"]), spec

    numeric = merged[["native_coef", "native_std_err", "stata_coef", "stata_std_err"]]
    assert numeric.notna().all().all(), spec
    assert np.isfinite(numeric.to_numpy(dtype=float)).all(), spec
    assert (merged[["native_std_err", "stata_std_err"]] > 0).all().all(), spec

    coef_diff = (merged["native_coef"] - merged["stata_coef"]).abs()
    relative_se_diff = (merged["native_std_err"] - merged["stata_std_err"]).abs() / merged[
        "stata_std_err"
    ].abs()
    assert float(coef_diff.max(skipna=False)) <= COEF_TOL, spec
    assert float(relative_se_diff.max(skipna=False)) <= float(paths["max_rel_se_diff"]), spec


def _assert_diagnostic_gate(
    spec: str,
    paths: SpecConfig,
    native_path: Path,
) -> None:
    native = _one(native_path)
    stata = _one(_repo(paths["stata_diagnostics"]))
    numeric_pairs = (
        ("native_hansen_j_stat", "stata_hansen"),
        ("native_hansen_p", "stata_hansen_p"),
        ("native_sargan_j_stat", "stata_sargan"),
        ("native_sargan_p", "stata_sargan_p"),
        ("native_ar1_z", "stata_ar1_z"),
        ("native_ar1_p", "stata_ar1_p"),
        ("native_ar2_z", "stata_ar2_z"),
        ("native_ar2_p", "stata_ar2_p"),
    )

    assert native["spec"] == stata["spec"] == spec
    assert (
        float(stata["stata_version"]) == PROVENANCE.stata_version == REGISTRY.expected_stata_version
    )
    assert PROVENANCE.xtabond2_e_version == REGISTRY.expected_xtabond2_e_version
    assert PROVENANCE.xtabond2_ado_header == REGISTRY.expected_xtabond2_ado_header
    assert (
        _sha256(_repo(paths["stata_params"]))
        == PROVENANCE.output_hashes[spec]["stata_params_sha256"]
    )
    assert (
        _sha256(_repo(paths["stata_diagnostics"]))
        == PROVENANCE.output_hashes[spec]["stata_diagnostics_sha256"]
    )
    if "native_sample" in paths and "stata_sample" in paths:
        native_sample = pd.read_csv(_repo(paths["native_sample"]))[["id", "t"]]
        stata_sample = pd.read_csv(_repo(paths["stata_sample"]))[["id", "t"]]
        native_sample = native_sample.sort_values(["id", "t"]).reset_index(drop=True)
        stata_sample = stata_sample.sort_values(["id", "t"]).reset_index(drop=True)
        assert not native_sample.duplicated(["id", "t"]).any(), spec
        assert not stata_sample.duplicated(["id", "t"]).any(), spec
        pd.testing.assert_frame_equal(native_sample, stata_sample, check_dtype=False)
        assert len(native_sample) == int(paths["expected_nobs"]), spec
        assert (
            _sha256(_repo(paths["stata_sample"]))
            == PROVENANCE.output_hashes[spec]["stata_sample_sha256"]
        )
    assert (
        _exact_int(native["native_nobs"], spec)
        == _exact_int(stata["stata_nobs"], spec)
        == int(paths["expected_nobs"])
    )
    assert (
        _exact_int(native["native_n_groups"], spec)
        == _exact_int(stata["stata_n_groups"], spec)
        == int(paths["expected_n_groups"])
    )
    assert (
        _exact_int(native["native_n_instruments"], spec)
        == _exact_int(stata["stata_n_instruments"], spec)
        == int(paths["expected_instruments"])
    )
    assert (
        _exact_int(native["native_overid_df"], spec)
        == _exact_int(stata["stata_hansen_df"], spec)
        == _exact_int(stata["stata_sargan_df"], spec)
        == int(paths["expected_df"])
    )

    values = np.array(
        [
            [float(native[native_name]), float(stata[stata_name])]
            for native_name, stata_name in numeric_pairs
        ]
    )
    assert np.isfinite(values).all(), spec
    for row_index in (1, 3, 5, 7):
        assert ((values[row_index] >= 0) & (values[row_index] <= 1)).all(), spec

    for native_name, stata_name in numeric_pairs[:4]:
        tolerance = OVERID_P_TOL if native_name.endswith("_p") else OVERID_STAT_TOL
        assert abs(float(native[native_name]) - float(stata[stata_name])) <= tolerance
    for native_name, stata_name in numeric_pairs[4:]:
        tolerance = AR_Z_TOL if native_name.endswith("_z") else AR_P_TOL
        assert abs(float(native[native_name]) - float(stata[stata_name])) <= tolerance


@pytest.mark.parity
@pytest.mark.parametrize(("spec", "paths"), SPECS.items())
def test_raw_parameter_artifacts_pass_declared_gates(spec: str, paths: SpecConfig) -> None:
    _assert_parameter_gate(spec, paths, _repo(paths["native_params"]))


@pytest.mark.parity
@pytest.mark.parametrize(("spec", "paths"), SPECS.items())
def test_raw_diagnostic_artifacts_pass_declared_gates(spec: str, paths: SpecConfig) -> None:
    _assert_diagnostic_gate(spec, paths, _repo(paths["native_diagnostics"]))


@pytest.mark.parity
@pytest.mark.parametrize(("spec", "paths"), SPECS.items())
def test_current_native_engine_passes_stata_gates(
    spec: str,
    paths: SpecConfig,
    tmp_path: Path,
) -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    env["SYSTEMGMMKIT_NATIVE_WINDMEIJER"] = "1"
    subprocess.run(
        [sys.executable, str(_repo(paths["builder"]))], cwd=tmp_path, env=env, check=True
    )
    subprocess.run([sys.executable, str(_repo(paths["runner"]))], cwd=tmp_path, env=env, check=True)

    fresh_params = tmp_path / paths["native_params"]
    fresh_diagnostics = tmp_path / paths["native_diagnostics"]
    assert fresh_params.exists(), fresh_params
    assert fresh_diagnostics.exists(), fresh_diagnostics
    _assert_parameter_gate(spec, paths, fresh_params)
    _assert_diagnostic_gate(spec, paths, fresh_diagnostics)


@pytest.mark.parity
def test_machine_readable_diagnostic_certificate_matches_raw_inputs() -> None:
    certificate = pd.read_csv(BASE / "diagnostic_parity_certificate.csv").set_index("spec")
    assert set(certificate.index) == set(SPECS)
    assert certificate["parameter_status"].eq("PASS_PARAMETER_PARITY").all()
    assert certificate["diagnostic_status"].eq("PASS_DIAGNOSTIC_PARITY").all()
    assert certificate["status"].eq("PASS_XTABOND2_PARITY").all()

    for spec, paths in SPECS.items():
        row = certificate.loc[spec]
        assert row["certification_registry_path"] == REGISTRY_PATH.relative_to(ROOT).as_posix()
        assert row["certification_registry_sha256"] == certification_registry_sha256(REGISTRY_PATH)
        assert row["comparator_provenance_path"] == REGISTRY.comparator_provenance.as_posix()
        assert row["comparator_provenance_sha256"] == comparator_provenance_sha256(REGISTRY)
        assert row["provenance_attestation_kind"] == PROVENANCE.attestation_kind
        assert row["provenance_source_log_sha256"] == PROVENANCE.run_log_sha256
        assert bool(row["same_stata_version"])
        assert bool(row["same_xtabond2_e_version"])
        assert bool(row["same_xtabond2_ado_header"])
        assert bool(row["same_spec_id"])
        assert bool(row["stata_output_hashes_match_provenance"])
        if "native_sample" in paths:
            assert bool(row["sample_gate_applies"])
            assert bool(row["same_sample_keys"])
            assert row["sample_status"] == "PASS_EXACT_SAMPLE_KEYS"
            assert row["native_sample_sha256"] == _sha256(_repo(paths["native_sample"]))
            assert row["stata_sample_sha256"] == _sha256(_repo(paths["stata_sample"]))
        else:
            assert not bool(row["sample_gate_applies"])
            assert row["sample_status"] == "NOT_APPLICABLE"
        stata_diagnostics = pd.read_csv(_repo(paths["stata_diagnostics"]))
        embedded_fields = {"xtabond2_e_version", "xtabond2_ado_header"}
        if embedded_fields.issubset(stata_diagnostics.columns):
            assert bool(row["stata_export_provenance_embedded"])
            assert bool(row["stata_export_provenance_matches_attestation"])
            assert row["comparator_provenance_mode"] == "embedded-export-plus-attestation"
        else:
            assert not bool(row["stata_export_provenance_embedded"])
            assert pd.isna(row["stata_export_provenance_matches_attestation"])
            assert row["comparator_provenance_mode"] == "historical-log-derived-attestation"
        assert row["comparator_status"] == "PASS"
        assert row["data_sha256"] == _sha256(_repo(paths["data"]))
        assert row["do_file_sha256"] == _sha256(_repo(paths["do_file"]))
        expected_support_hashes = ";".join(
            f"{path.as_posix()}:{_sha256(_repo(path))}" for path in paths.get("support_files", ())
        )
        if expected_support_hashes:
            assert row["support_files_sha256"] == expected_support_hashes
        else:
            assert pd.isna(row["support_files_sha256"])
        assert row["native_params_sha256"] == _sha256(_repo(paths["native_params"]))
        assert row["stata_params_sha256"] == _sha256(_repo(paths["stata_params"]))
        assert row["native_diagnostics_sha256"] == _sha256(_repo(paths["native_diagnostics"]))
        assert row["stata_diagnostics_sha256"] == _sha256(_repo(paths["stata_diagnostics"]))
        assert bool(row["parameter_set_complete"])
        assert bool(row["parameters_finite"])
        assert bool(row["standard_errors_positive"])
        assert float(row["max_abs_coef_diff"]) <= COEF_TOL
        assert float(row["max_rel_se_diff"]) <= float(paths["max_rel_se_diff"])
        assert float(row["abs_ar1_z_diff"]) <= AR_Z_TOL
        assert float(row["abs_ar1_p_diff"]) <= AR_P_TOL
        assert float(row["abs_ar2_z_diff"]) <= AR_Z_TOL
        assert float(row["abs_ar2_p_diff"]) <= AR_P_TOL
        assert bool(row["stata_hansen_reject_005"]) == (float(row["stata_hansen_p"]) < 0.05)
        assert bool(row["stata_sargan_reject_005"]) == (float(row["stata_sargan_p"]) < 0.05)


def test_stata_and_native_selector_contracts_are_explicit() -> None:
    for paths in SPECS.values():
        do_text = _repo(paths["do_file"]).read_text(encoding="utf-8")
        runner_text = _repo(paths["runner"]).read_text(encoding="utf-8")
        selector_text = "\n".join(
            [
                runner_text,
                *[
                    _repo(path).read_text(encoding="utf-8")
                    for path in paths.get("support_files", ())
                ],
            ]
        )

        assert do_text.startswith(f"version {REGISTRY.stata_syntax_version}\n")
        assert "collapse eq(both)" in do_text
        assert "twostep robust small ///" not in do_text
        assert "stata_ar1_z" in do_text and "stata_ar2_z" in do_text
        assert "gen double stata_version = c(stata_version)" in do_text
        assert "findfile xtabond2.ado" in do_text
        assert "file read `xtabond2_ado_handle' xtabond2_ado_header" in do_text
        assert 'local xtabond2_e_version "`e(version)\'"' in do_text
        assert "gen str20 xtabond2_e_version" in do_text
        assert "gen str80 xtabond2_ado_header" in do_text
        assert "stata_reported_date" in do_text and "stata_reported_time" in do_text
        transformation = paths["transformation"]
        assert (
            f'transformation="{transformation}"' in selector_text
            or f'SYSTEMGMMKIT_NATIVE_TRANSFORMATION", "{transformation}"' in selector_text
        )
        assert 'GMMStyle(variable="L1.y"' in selector_text

        if paths["requires_level_iv"]:
            assert 'eq="level"' in selector_text

    driver = (ROOT / "scripts" / "parity" / "rerun_xtabond2_certification.do").read_text(
        encoding="utf-8"
    )
    assert "args repo" in driver
    assert "C:/Users/" not in driver


def test_generated_stata_fixtures_are_in_sync_with_builders(tmp_path: Path) -> None:
    builders = dict.fromkeys(paths["builder"] for paths in SPECS.values())
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    for builder in builders:
        subprocess.run(
            [sys.executable, str(_repo(builder))],
            cwd=tmp_path,
            env=env,
            check=True,
        )

    for paths in SPECS.values():
        assert canonical_text_sha256(tmp_path / paths["data"]) == canonical_text_sha256(
            _repo(paths["data"])
        )
        assert canonical_text_sha256(tmp_path / paths["do_file"]) == canonical_text_sha256(
            _repo(paths["do_file"])
        )
