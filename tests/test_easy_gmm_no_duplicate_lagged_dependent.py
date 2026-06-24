from __future__ import annotations

from types import SimpleNamespace

import pandas as pd

from systemgmmkit.easy import difference_gmm, system_gmm
from systemgmmkit.pydynpd_backend import build_pydynpd_command


def _panel() -> pd.DataFrame:
    rows = []
    for entity in range(1, 5):
        for time in range(1, 8):
            rows.append(
                {
                    "id": entity,
                    "t": time,
                    "risk": float(entity + time),
                    "x": float(time),
                    "z": float(entity),
                }
            )
    return pd.DataFrame(rows)


def _patch_runners(monkeypatch):
    import systemgmmkit as s

    def fake_runner(**kwargs):
        return SimpleNamespace(
            backend=kwargs.get("backend"),
            nobs=None,
            n_groups=None,
            n_instruments=None,
        )

    monkeypatch.setattr(s, "run_system_gmm", fake_runner)
    monkeypatch.setattr(s, "run_difference_gmm", fake_runner)


def _assert_no_duplicate_symbolic_lag(workflow):
    command = build_pydynpd_command(workflow.spec)
    gmm_vars = [block.variable for block in workflow.spec.gmm]

    assert "L1.risk" not in workflow.spec.regressors
    assert "L1.risk" not in command
    assert "L1_risk" in workflow.spec.regressors
    assert "L1_risk" in gmm_vars
    assert "risk" not in gmm_vars
    assert "gmm(risk" not in command
    assert "gmm(L1_risk" in command


def test_easy_system_gmm_does_not_duplicate_lagged_dependent(monkeypatch):
    _patch_runners(monkeypatch)

    workflow = system_gmm(
        data=_panel(),
        entity="id",
        time="t",
        dependent="risk",
        regressors=["x", "z"],
        predetermined=["x"],
        exogenous=["z"],
        lagged_dependent=1,
        lagged_dependent_role="endogenous",
        backend="native",
        return_workflow=True,
    )

    _assert_no_duplicate_symbolic_lag(workflow)


def test_easy_difference_gmm_does_not_duplicate_lagged_dependent(monkeypatch):
    _patch_runners(monkeypatch)

    workflow = difference_gmm(
        data=_panel(),
        entity="id",
        time="t",
        dependent="risk",
        regressors=["x", "z"],
        predetermined=["x"],
        exogenous=["z"],
        lagged_dependent=1,
        lagged_dependent_role="endogenous",
        backend="native",
        return_workflow=True,
    )

    _assert_no_duplicate_symbolic_lag(workflow)
