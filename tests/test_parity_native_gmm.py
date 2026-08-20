import numpy as np
import pandas as pd

from systemgmmkit import (
    build_difference_gmm_spec,
    build_fixed_effects_spec,
    build_system_gmm_spec,
    run_native_dynamic_panel_gmm,
    stata_xtabond2_command,
    stata_xtreg_fe_command,
    write_stata_parity_do_file,
)
from systemgmmkit.postestimation import vcov


def make_dynamic_panel() -> pd.DataFrame:
    rows = []
    for i in range(8):
        y_prev = 0.2 * i
        for t in range(8):
            x = 0.1 * i + 0.2 * t + ((i + t) % 3) * 0.05
            y = 0.4 * y_prev + 1.2 * x + i * 0.1 + t * 0.02
            rows.append({"id": i, "t": t, "y": y, "x": x, "z": x + 0.1})
            y_prev = y
    return pd.DataFrame(rows)


def test_stata_parity_commands_are_generated(tmp_path):
    fe = build_fixed_effects_spec(dependent="y", regressors=["x"], time_effects=True)
    gmm = build_system_gmm_spec(dependent="y", regressors=["x"], endogenous=["x"])

    fe_cmd = stata_xtreg_fe_command(fe, entity="id", time="t")
    gmm_cmd = stata_xtabond2_command(gmm, entity="id", time="t")

    assert "xtreg y x i.t, fe" in fe_cmd
    assert "xtabond2 y L1.y x" in gmm_cmd
    assert "gmmstyle(y, lag(2 3) collapse)" in gmm_cmd

    out = write_stata_parity_do_file(
        tmp_path / "parity.do",
        data_path="panel.csv",
        entity="id",
        time="t",
        fixed_effects=[fe],
        dynamic_gmm=[gmm],
    )
    assert out.exists()
    assert "xtabond2" in out.read_text(encoding="utf-8")


def test_native_dynamic_panel_gmm_runs():
    df = make_dynamic_panel()
    spec = build_difference_gmm_spec(
        dependent="y",
        regressors=["x"],
        endogenous=["x"],
        exogenous=[],
        dependent_lag_limits=(2, 3),
    )
    result = run_native_dynamic_panel_gmm(spec, df, entity="id", time="t")

    assert result.nobs > 0
    assert result.n_instruments > 0
    assert "L1.y" in result.params.index
    assert "x" in result.params.index
    assert result.backend == "native-gmm"


def test_native_windmeijer_preserves_point_estimates_and_j_stat():
    df = make_dynamic_panel()
    spec = build_system_gmm_spec(
        dependent="y",
        regressors=["x"],
        endogenous=["x"],
        exogenous=[],
        dependent_lag_limits=(2, 3),
        collapse=True,
    )

    uncorrected = run_native_dynamic_panel_gmm(
        spec,
        df,
        entity="id",
        time="t",
        windmeijer=False,
    )
    corrected = run_native_dynamic_panel_gmm(
        spec,
        df,
        entity="id",
        time="t",
        windmeijer=True,
    )

    assert uncorrected.covariance_type == "robust-clustered-two-step-uncorrected"
    assert corrected.covariance_type == "robust-clustered-two-step-windmeijer"
    assert uncorrected.covariance_correction == "none"
    assert uncorrected.covariance_reference is None
    assert corrected.covariance_correction == "windmeijer_2005"
    assert corrected.covariance_reference == "10.1016/j.jeconom.2004.02.005"

    pd.testing.assert_series_equal(
        uncorrected.params,
        corrected.params,
        check_names=False,
        rtol=1e-10,
        atol=1e-10,
    )

    if uncorrected.j_stat is not None and corrected.j_stat is not None:
        assert np.isclose(uncorrected.j_stat, corrected.j_stat, rtol=1e-10, atol=1e-10)

    corrected_se = corrected.std_errors.reindex(corrected.params.index).to_numpy(dtype=float)
    uncorrected_se = uncorrected.std_errors.reindex(corrected.params.index).to_numpy(dtype=float)

    assert np.all(np.isfinite(corrected_se))
    assert np.any(np.abs(corrected_se - uncorrected_se) > 1e-12)

    assert corrected.covariance is not None
    covariance = corrected.covariance
    assert covariance.index.equals(corrected.params.index)
    assert covariance.columns.equals(corrected.params.index)
    assert np.isfinite(covariance.to_numpy(dtype=float)).all()
    np.testing.assert_allclose(
        covariance.to_numpy(dtype=float),
        covariance.to_numpy(dtype=float).T,
        rtol=1e-12,
        atol=1e-12,
    )
    np.testing.assert_allclose(
        np.sqrt(np.diag(covariance.to_numpy(dtype=float))),
        corrected_se,
        rtol=1e-12,
        atol=1e-12,
    )
    pd.testing.assert_frame_equal(vcov(corrected), covariance)
