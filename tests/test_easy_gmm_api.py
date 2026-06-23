import pandas as pd

import systemgmmkit
from systemgmmkit import DynamicGMMWorkflowResult, difference_gmm, system_gmm


def _panel():
    return pd.DataFrame(
        {
            "firm": [1, 1, 1, 2, 2, 2],
            "year": [1, 2, 3, 1, 2, 3],
            "y": [1.0, 1.2, 1.4, 2.0, 2.1, 2.4],
            "x": [0.2, 0.3, 0.5, 0.1, 0.4, 0.6],
            "z": [1.0, 1.0, 1.0, 2.0, 2.0, 2.0],
        }
    )


def test_system_gmm_easy_api_creates_lag_and_defaults_unclassified_to_exogenous(monkeypatch):
    captured = {}

    def fake_build(**kwargs):
        captured["spec_kwargs"] = kwargs
        return {"spec": kwargs}

    def fake_run(spec, data, *, entity, time, backend="auto", windmeijer=None):
        captured["run"] = {
            "spec": spec,
            "data": data,
            "entity": entity,
            "time": time,
            "backend": backend,
            "windmeijer": windmeijer,
        }
        return {"ok": True}

    monkeypatch.setattr(systemgmmkit, "build_system_gmm_spec", fake_build)
    monkeypatch.setattr(systemgmmkit, "run_system_gmm", fake_run)

    result = system_gmm(
        data=_panel(),
        entity="firm",
        time="year",
        dependent="y",
        regressors=["x"],
        controls=["z"],
        gmm_lags=(2, 2),
        collapse=True,
        windmeijer=True,
    )

    assert result == {"ok": True}
    assert "L1_y" in captured["spec_kwargs"]["regressors"]
    assert "x" in captured["spec_kwargs"]["regressors"]
    assert "z" in captured["spec_kwargs"]["regressors"]
    assert "L1_y" in captured["spec_kwargs"]["endogenous"]
    assert "x" in captured["spec_kwargs"]["exogenous"]
    assert "z" in captured["spec_kwargs"]["exogenous"]
    assert captured["spec_kwargs"]["gmm_lags"] == (2, 2)
    assert captured["run"]["windmeijer"] is True
    assert len(captured["run"]["data"]) == 4


def test_difference_gmm_easy_api_can_return_workflow(monkeypatch):
    captured = {}

    def fake_build(**kwargs):
        captured["spec_kwargs"] = kwargs
        return {"spec": kwargs}

    def fake_run(spec, data, *, entity, time, backend="auto", windmeijer=None):
        return {"model": "difference", "rows": len(data)}

    monkeypatch.setattr(systemgmmkit, "build_difference_gmm_spec", fake_build)
    monkeypatch.setattr(systemgmmkit, "run_difference_gmm", fake_run)

    workflow = difference_gmm(
        data=_panel(),
        entity="firm",
        time="year",
        dependent="y",
        regressors=["x"],
        exogenous=["x"],
        lagged_dependent=1,
        gmm_lags=(2, 3),
        return_workflow=True,
    )

    assert isinstance(workflow, DynamicGMMWorkflowResult)
    assert workflow.result == {"model": "difference", "rows": 4}
    assert workflow.model == "difference"
    assert workflow.gmm_lags == (2, 3)
    assert "L1_y" in workflow.regressors
    assert "L1_y" in workflow.endogenous
    assert "L1_y" in workflow.data.columns


def test_easy_api_rejects_invalid_lag_window():
    try:
        system_gmm(
            data=_panel(),
            entity="firm",
            time="year",
            dependent="y",
            regressors=["x"],
            gmm_lags=(4, 2),
        )
    except ValueError as exc:
        assert "gmm_lags stop" in str(exc)
    else:
        raise AssertionError("Expected invalid lag window to raise ValueError")
