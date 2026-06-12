from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "parity" / "xtabond2" / "specs" / "system_gmm_three_way_controls"


@pytest.mark.parity
def test_system_gmm_three_way_controls_certified_against_xtabond2_artifacts() -> None:
    required = [
        OUT / "summary.csv",
        OUT / "native_vs_stata_params.csv",
        OUT / "native_diagnostics.csv",
        OUT / "stata_diagnostics.csv",
        OUT / "stata_params.csv",
        OUT / "stata_V.csv",
        OUT / "stata_b.csv",
    ]

    missing = [path for path in required if not path.exists()]
    assert not missing, "Missing three-way controls parity artifacts: " + ", ".join(
        str(path) for path in missing
    )

    summary = pd.read_csv(OUT / "summary.csv").iloc[0]

    assert summary["spec"] == "system_gmm_three_way_controls"
    assert summary["status"] == "COMPARISON_GENERATED"
    assert int(summary["n_params_native"]) == 10
    assert int(summary["n_params_stata"]) == 10
    assert float(summary["max_abs_coef_diff"]) < 1e-6
    assert float(summary["mean_abs_coef_diff"]) < 1e-6
    assert float(summary["max_rel_se_diff"]) < 1e-5
    assert float(summary["mean_rel_se_diff"]) < 1e-5

    params = pd.read_csv(OUT / "native_vs_stata_params.csv")
    expected_params = {
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
    assert set(params["param"]) == expected_params

    native_diag = pd.read_csv(OUT / "native_diagnostics.csv").iloc[0]
    stata_diag = pd.read_csv(OUT / "stata_diagnostics.csv").iloc[0]

    assert int(native_diag["native_nobs"]) == int(stata_diag["stata_nobs"]) == 1248
    assert int(native_diag["native_n_instruments"]) == int(stata_diag["stata_n_instruments"]) == 16
    assert native_diag["native_covariance_type"] == "robust-clustered-two-step-windmeijer"

    native_hansen_p = float(native_diag["native_hansen_p"])
    stata_hansen_p = float(stata_diag["stata_hansen_p"])
    assert abs(native_hansen_p - stata_hansen_p) < 1e-6
