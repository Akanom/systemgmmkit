from __future__ import annotations

from types import SimpleNamespace

import pandas as pd

from systemgmmkit.ml import (
    DynamicGMMHybridSearch,
    GMMGridSearch,
    GMMValidityRules,
    auto_dynamic_gmm,
    dynamic_gmm_candidate_grid,
)


class SearchResult:
    def __init__(
        self,
        *,
        label: str,
        coefficient: float = 1.0,
        hansen_p: float = 0.30,
        ar2_p: float = 0.40,
        n_instruments: int = 2,
        n_groups: int = 8,
        succeeded: bool = True,
    ) -> None:
        self.label = label
        self.params = pd.Series({"x": coefficient, "_con": 0.0})
        self.hansen_p = hansen_p
        self.ar2_p = ar2_p
        self.n_instruments = n_instruments
        self.n_groups = n_groups
        self.succeeded = succeeded


def _panel() -> pd.DataFrame:
    rows = []
    for entity in range(1, 5):
        for time in range(1, 7):
            x = float(time)
            rows.append({"id": entity, "t": time, "y": x, "x": x})
    return pd.DataFrame(rows)


def test_dynamic_gmm_candidate_grid_filters_invalid_onestep_windmeijer():
    grid = dynamic_gmm_candidate_grid(
        models=("system",),
        steps=("onestep", "twostep"),
        lag_windows=((2, 2),),
        transformations=("fod",),
        windmeijer_options=(True,),
    )

    assert len(grid) == 1
    assert grid[0]["steps"] == "twostep"
    assert grid[0]["windmeijer"] is True


def test_gmm_grid_search_keeps_best_result_aligned_after_failed_candidate():
    def build_spec(**kwargs):
        return kwargs

    def run_model(spec, data, *, entity, time):
        del data, entity, time
        if spec["name"] == "fails":
            raise RuntimeError("candidate failed")
        return SearchResult(label=spec["name"])

    search = GMMGridSearch(
        build_spec=build_spec,
        run_model=run_model,
        param_grid=[
            {"name": "fails"},
            {"name": "wins"},
        ],
        y="y",
        entity="id",
        time="t",
        validity_rules=GMMValidityRules(),
        test_size=1,
    )

    result = search.fit(_panel())

    assert result.best_result is not None
    assert result.best_result.label == "wins"
    assert result.best_spec == {"name": "wins"}
    assert result.results.loc[0, "error"].startswith("RuntimeError")
    assert result.results.loc[1, "passes_diagnostics"]


def test_gmm_grid_search_honors_maximize_selection_metric():
    def build_spec(**kwargs):
        return kwargs

    def run_model(spec, data, *, entity, time):
        del data, entity, time
        return SearchResult(
            label=spec["name"],
            coefficient=spec["coefficient"],
        )

    search = GMMGridSearch(
        build_spec=build_spec,
        run_model=run_model,
        param_grid=[
            {"name": "poor", "coefficient": 0.0},
            {"name": "best", "coefficient": 1.0},
        ],
        y="y",
        entity="id",
        time="t",
        selection_metric="r2",
        minimize=False,
        test_size=2,
    )

    result = search.fit(_panel())

    assert result.best_result is not None
    assert result.best_result.label == "best"
    assert result.best_spec == {"name": "best", "coefficient": 1.0}


def test_dynamic_gmm_hybrid_search_uses_easy_api_and_rejects_invalid_specs(monkeypatch):
    import systemgmmkit.easy as easy_api

    calls = []

    def fake_system_gmm(**kwargs):
        calls.append(("system", kwargs))
        return SimpleNamespace(
            result=SearchResult(
                label="system",
                n_instruments=10,
                n_groups=4,
            )
        )

    def fake_difference_gmm(**kwargs):
        calls.append(("difference", kwargs))
        return SimpleNamespace(
            result=SearchResult(
                label="difference",
                n_instruments=2,
                n_groups=4,
            )
        )

    monkeypatch.setattr(easy_api, "system_gmm", fake_system_gmm)
    monkeypatch.setattr(easy_api, "difference_gmm", fake_difference_gmm)

    search = DynamicGMMHybridSearch(
        y="y",
        entity="id",
        time="t",
        regressors=["x"],
        exogenous=["x"],
        param_grid=[
            {
                "model": "system",
                "steps": "twostep",
                "gmm_lags": (2, 2),
                "transformation": "fod",
                "collapse": True,
            },
            {
                "model": "difference",
                "steps": "twostep",
                "gmm_lags": (2, 3),
                "transformation": "fd",
                "collapse": True,
            },
        ],
        test_size=1,
    )

    result = search.fit(_panel())

    assert [name for name, _ in calls] == ["system", "difference"]
    assert calls[0][1]["return_workflow"] is True
    assert calls[0][1]["steps"] == "twostep"
    assert calls[1][1]["transformation"] == "fd"
    assert result.best_result is not None
    assert result.best_result.label == "difference"
    assert result.best_spec["model"] == "difference"
    assert not result.results.loc[0, "passes_diagnostics"]
    assert "instrument_count_exceeds_groups" in result.results.loc[0, "rejection_reason"]
    assert "Recommended specification" in result.to_markdown()


def test_auto_dynamic_gmm_is_compact_wrapper_over_hybrid_search(monkeypatch):
    import systemgmmkit.easy as easy_api

    calls = []

    def fake_difference_gmm(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(
            result=SearchResult(
                label="difference",
                n_instruments=2,
                n_groups=4,
            )
        )

    monkeypatch.setattr(easy_api, "difference_gmm", fake_difference_gmm)

    result = auto_dynamic_gmm(
        _panel(),
        y="y",
        entity="id",
        time="t",
        regressors=["x"],
        exogenous=["x"],
        param_grid=[
            {
                "model": "difference",
                "steps": "twostep",
                "gmm_lags": (2, 2),
                "transformation": "fd",
                "collapse": True,
            }
        ],
        test_size=1,
    )

    assert len(calls) == 1
    assert calls[0]["return_workflow"] is True
    assert result.best_result is not None
    assert result.best_result.label == "difference"
    assert result.best_spec["model"] == "difference"
