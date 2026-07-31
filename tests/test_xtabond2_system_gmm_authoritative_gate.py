from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from pathlib import Path
from typing import TypedDict

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "artifacts" / "parity" / "xtabond2"
AR_Z_TOL = 0.10
AR_P_TOL = 0.03
OVERID_TOL = 1e-6


class SpecConfig(TypedDict):
    native_params: Path
    native_diagnostics: Path
    stata_params: Path
    stata_diagnostics: Path
    data: Path
    do_file: Path
    builder: Path
    runner: Path
    expected_params: frozenset[str]
    expected_instruments: int
    expected_df: int
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
        "builder": ROOT / "scripts" / "parity" / "build_xtabond2_system_gmm_do.py",
        "runner": ROOT / "scripts" / "parity" / "run_native_system_gmm_benchmark.py",
        "expected_params": frozenset({"L1.y", "x", "w", "_con"}),
        "expected_instruments": 8,
        "expected_df": 4,
        "max_rel_se_diff": 1e-6,
    },
    "system_gmm_no_controls": {
        "native_params": BASE / "specs" / "system_gmm_no_controls" / "native_params.csv",
        "native_diagnostics": BASE / "specs" / "system_gmm_no_controls" / "native_diagnostics.csv",
        "stata_params": BASE / "specs" / "system_gmm_no_controls" / "stata_params.csv",
        "stata_diagnostics": BASE / "specs" / "system_gmm_no_controls" / "stata_diagnostics.csv",
        "data": BASE / "specs" / "system_gmm_no_controls" / "system_gmm_no_controls_benchmark.csv",
        "do_file": BASE / "specs" / "system_gmm_no_controls" / "system_gmm_no_controls.do",
        "builder": ROOT / "scripts" / "parity" / "build_xtabond2_system_gmm_no_controls_do.py",
        "runner": ROOT / "scripts" / "parity" / "run_native_system_gmm_no_controls.py",
        "expected_params": frozenset({"L1.y", "x", "_con"}),
        "expected_instruments": 7,
        "expected_df": 4,
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
        "builder": ROOT
        / "scripts"
        / "parity"
        / "build_xtabond2_system_gmm_three_way_controls_do.py",
        "runner": ROOT / "scripts" / "parity" / "run_native_system_gmm_three_way_controls.py",
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
        "expected_instruments": 16,
        "expected_df": 6,
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
        "builder": ROOT
        / "scripts"
        / "parity"
        / "build_xtabond2_system_gmm_decomposition_controls_do.py",
        "runner": ROOT / "scripts" / "parity" / "run_native_system_gmm_decomposition_controls.py",
        "expected_params": frozenset({"L1.y", "x_long", "x_short", "w", "c1", "_con"}),
        "expected_instruments": 12,
        "expected_df": 6,
        "max_rel_se_diff": 1e-6,
    },
}


def _one(path: Path) -> pd.Series:
    frame = pd.read_csv(path)
    assert len(frame) == 1, path
    return frame.iloc[0]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
    stata = _normalise_stata_params(paths["stata_params"])

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
    assert float(coef_diff.max(skipna=False)) <= 1e-6, spec
    assert float(relative_se_diff.max(skipna=False)) <= float(paths["max_rel_se_diff"]), spec


def _assert_diagnostic_gate(
    spec: str,
    paths: SpecConfig,
    native_path: Path,
) -> None:
    native = _one(native_path)
    stata = _one(paths["stata_diagnostics"])
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
    assert _exact_int(native["native_nobs"], spec) == _exact_int(stata["stata_nobs"], spec) == 1248
    assert (
        _exact_int(native["native_n_groups"], spec)
        == _exact_int(stata["stata_n_groups"], spec)
        == 96
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
        assert abs(float(native[native_name]) - float(stata[stata_name])) <= OVERID_TOL
    for native_name, stata_name in numeric_pairs[4:]:
        tolerance = AR_Z_TOL if native_name.endswith("_z") else AR_P_TOL
        assert abs(float(native[native_name]) - float(stata[stata_name])) <= tolerance


@pytest.mark.parity
@pytest.mark.parametrize(("spec", "paths"), SPECS.items())
def test_raw_parameter_artifacts_pass_declared_gates(spec: str, paths: SpecConfig) -> None:
    _assert_parameter_gate(spec, paths, paths["native_params"])


@pytest.mark.parity
@pytest.mark.parametrize(("spec", "paths"), SPECS.items())
def test_raw_diagnostic_artifacts_pass_declared_gates(spec: str, paths: SpecConfig) -> None:
    _assert_diagnostic_gate(spec, paths, paths["native_diagnostics"])


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
    subprocess.run([sys.executable, str(paths["builder"])], cwd=tmp_path, env=env, check=True)
    subprocess.run([sys.executable, str(paths["runner"])], cwd=tmp_path, env=env, check=True)

    fresh_params = tmp_path / paths["native_params"].relative_to(ROOT)
    fresh_diagnostics = tmp_path / paths["native_diagnostics"].relative_to(ROOT)
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
        assert row["data_sha256"] == _sha256(paths["data"])
        assert row["do_file_sha256"] == _sha256(paths["do_file"])
        assert row["native_params_sha256"] == _sha256(paths["native_params"])
        assert row["stata_params_sha256"] == _sha256(paths["stata_params"])
        assert row["native_diagnostics_sha256"] == _sha256(paths["native_diagnostics"])
        assert row["stata_diagnostics_sha256"] == _sha256(paths["stata_diagnostics"])
        assert bool(row["parameter_set_complete"])
        assert bool(row["parameters_finite"])
        assert bool(row["standard_errors_positive"])
        assert float(row["max_abs_coef_diff"]) <= 1e-6
        assert float(row["max_rel_se_diff"]) <= float(paths["max_rel_se_diff"])
        assert float(row["abs_ar1_z_diff"]) <= AR_Z_TOL
        assert float(row["abs_ar1_p_diff"]) <= AR_P_TOL
        assert float(row["abs_ar2_z_diff"]) <= AR_Z_TOL
        assert float(row["abs_ar2_p_diff"]) <= AR_P_TOL


def test_stata_and_native_selector_contracts_are_explicit() -> None:
    for spec, paths in SPECS.items():
        do_text = paths["do_file"].read_text(encoding="utf-8")
        runner_text = paths["runner"].read_text(encoding="utf-8")

        assert do_text.startswith("version 17.0\n")
        assert "collapse eq(both)" in do_text
        assert "twostep robust small ///" not in do_text
        assert "stata_ar1_z" in do_text and "stata_ar2_z" in do_text
        assert "gen double stata_version = c(stata_version)" in do_text
        assert "stata_reported_date" in do_text and "stata_reported_time" in do_text
        if spec == "system_gmm_baseline_controls":
            assert 'SYSTEMGMMKIT_NATIVE_TRANSFORMATION", "fd"' in runner_text
        else:
            assert 'transformation="fd"' in runner_text
        assert 'GMMStyle(variable="L1.y"' in runner_text

        if spec in {
            "system_gmm_baseline_controls",
            "system_gmm_three_way_controls",
            "system_gmm_decomposition_controls",
        }:
            assert 'eq="level"' in runner_text

    driver = (ROOT / "scripts" / "parity" / "rerun_xtabond2_certification.do").read_text(
        encoding="utf-8"
    )
    assert "args repo" in driver
    assert "C:/Users/" not in driver


def test_generated_stata_fixtures_are_in_sync_with_builders(tmp_path: Path) -> None:
    builders = (
        "build_xtabond2_system_gmm_do.py",
        "build_xtabond2_system_gmm_no_controls_do.py",
        "build_xtabond2_system_gmm_three_way_controls_do.py",
        "build_xtabond2_system_gmm_decomposition_controls_do.py",
    )
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    for builder in builders:
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "parity" / builder)],
            cwd=tmp_path,
            env=env,
            check=True,
        )

    for paths in SPECS.values():
        relative_data = paths["data"].relative_to(ROOT)
        relative_do = paths["do_file"].relative_to(ROOT)
        assert (tmp_path / relative_data).read_bytes() == paths["data"].read_bytes()
        assert (tmp_path / relative_do).read_bytes() == paths["do_file"].read_bytes()
