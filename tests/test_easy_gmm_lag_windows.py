from __future__ import annotations

from types import SimpleNamespace

import pandas as pd

from systemgmmkit.easy import difference_gmm, system_gmm


def _panel() -> pd.DataFrame:
    rows = []
    for entity in range(1, 5):
        for time in range(1, 8):
            rows.append(
                {
                    "id": entity,
                    "t": time,
                    "y": float(entity + time),
                    "x_endog": float(time),
                    "x_pred": float(entity * time),
                    "x_exog": float(entity),
                }
            )
    return pd.DataFrame(rows)


def _patch_runners(monkeypatch):
    """Keep these tests focused on easy-API spec construction.

    The numerical native/pydynpd backends are tested elsewhere. These tests
    should only verify that role-specific and variable-specific lag windows
    are passed through correctly by the easy API.
    """

    import systemgmmkit as s

    def fake_system_runner(**kwargs):
        return SimpleNamespace(
            backend=kwargs.get("backend"),
            estimator="system_gmm",
            nobs=None,
            n_groups=None,
            n_instruments=None,
        )

    def fake_difference_runner(**kwargs):
        return SimpleNamespace(
            backend=kwargs.get("backend"),
            estimator="difference_gmm",
            nobs=None,
            n_groups=None,
            n_instruments=None,
        )

    monkeypatch.setattr(s, "run_system_gmm", fake_system_runner)
    monkeypatch.setattr(s, "run_difference_gmm", fake_difference_runner)


def _lag_map(workflow):
    return {
        block.variable: (block.min_lag, block.max_lag)
        for block in workflow.spec.gmm
    }


def test_easy_system_gmm_supports_role_specific_lag_windows(monkeypatch):
    _patch_runners(monkeypatch)

    workflow = system_gmm(
        data=_panel(),
        entity="id",
        time="t",
        dependent="y",
        regressors=["x_endog", "x_pred", "x_exog"],
        endogenous=["x_endog"],
        predetermined=["x_pred"],
        exogenous=["x_exog"],
        gmm_lags=(2, 2),
        gmm_lags_by_role={
            "endogenous": (2, 4),
            "predetermined": (1, 3),
        },
        backend="native",
        return_workflow=True,
    )

    lag_map = _lag_map(workflow)

    assert lag_map["L1_y"] == (2, 4)
    assert lag_map["x_endog"] == (2, 4)
    assert lag_map["x_pred"] == (1, 3)
    assert "x_exog" not in lag_map
    assert workflow.gmm_lags_by_role == {
        "endogenous": (2, 4),
        "predetermined": (1, 3),
    }


def test_easy_system_gmm_variable_lags_override_role_and_global_lags(monkeypatch):
    _patch_runners(monkeypatch)

    workflow = system_gmm(
        data=_panel(),
        entity="id",
        time="t",
        dependent="y",
        regressors=["x_endog", "x_pred", "x_exog"],
        endogenous=["x_endog"],
        predetermined=["x_pred"],
        exogenous=["x_exog"],
        gmm_lags=(2, 2),
        gmm_lags_by_role={
            "endogenous": (2, 4),
            "predetermined": (1, 3),
        },
        gmm_lags_by_variable={
            "L1_y": (3, 5),
            "x_endog": (4, 6),
            "x_pred": (2, 2),
        },
        backend="native",
        return_workflow=True,
    )

    lag_map = _lag_map(workflow)

    assert lag_map["L1_y"] == (3, 5)
    assert lag_map["x_endog"] == (4, 6)
    assert lag_map["x_pred"] == (2, 2)
    assert "x_exog" not in lag_map
    assert workflow.gmm_lags_by_variable == {
        "L1_y": (3, 5),
        "x_endog": (4, 6),
        "x_pred": (2, 2),
    }


def test_easy_difference_gmm_supports_same_lag_window_api(monkeypatch):
    _patch_runners(monkeypatch)

    workflow = difference_gmm(
        data=_panel(),
        entity="id",
        time="t",
        dependent="y",
        regressors=["x_endog", "x_pred", "x_exog"],
        endogenous=["x_endog"],
        predetermined=["x_pred"],
        exogenous=["x_exog"],
        gmm_lags=(2, 2),
        gmm_lags_by_role={
            "endogenous": (2, 3),
            "predetermined": (1, 2),
        },
        gmm_lags_by_variable={
            "x_endog": (3, 4),
        },
        backend="native",
        return_workflow=True,
    )

    lag_map = _lag_map(workflow)

    assert workflow.spec.system is False
    assert lag_map["L1_y"] == (2, 3)
    assert lag_map["x_endog"] == (3, 4)
    assert lag_map["x_pred"] == (1, 2)
    assert "x_exog" not in lag_map
