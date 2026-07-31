from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "parity" / "xtabond2" / "specs" / "system_gmm_no_controls"


@pytest.mark.parity
def test_system_gmm_no_controls_certified_against_xtabond2_artifacts() -> None:
    required = [
        OUT / "native_params.csv",
        OUT / "native_diagnostics.csv",
        OUT / "stata_diagnostics.csv",
        OUT / "stata_params.csv",
        OUT / "stata_V.csv",
        OUT / "stata_b.csv",
    ]

    missing = [path for path in required if not path.exists()]
    assert not missing, "Missing no-controls parity artifacts: " + ", ".join(
        str(path) for path in missing
    )

    native_params = pd.read_csv(OUT / "native_params.csv")
    stata_params = pd.read_csv(OUT / "stata_params.csv").rename(
        columns={"parm": "param", "estimate": "stata_coef", "stderr": "stata_std_err"}
    )
    stata_params["param"] = stata_params["param"].replace({"L.y": "L1.y", "_cons": "_con"})
    params = native_params.merge(stata_params, on="param", how="outer", indicator=True)
    assert params["_merge"].eq("both").all()
    assert set(params["param"]) == {"L1.y", "x", "_con"}
    assert (params["native_coef"] - params["stata_coef"]).abs().max() < 1e-6
    relative_se_diff = (params["native_std_err"] - params["stata_std_err"]).abs() / params[
        "stata_std_err"
    ].abs()
    assert relative_se_diff.max() < 1e-3

    native_diag = pd.read_csv(OUT / "native_diagnostics.csv").iloc[0]
    stata_diag = pd.read_csv(OUT / "stata_diagnostics.csv").iloc[0]

    assert int(native_diag["native_nobs"]) == int(stata_diag["stata_nobs"]) == 1248
    assert int(native_diag["native_n_groups"]) == int(stata_diag["stata_n_groups"]) == 96
    assert int(native_diag["native_n_instruments"]) == int(stata_diag["stata_n_instruments"]) == 7

    assert abs(float(native_diag["native_hansen_p"]) - float(stata_diag["stata_hansen_p"])) < 1e-6
