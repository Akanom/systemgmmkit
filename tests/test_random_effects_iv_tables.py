from pathlib import Path

import pandas as pd

from systemgmmkit import (
    PanelIVSpec,
    RandomEffectsSpec,
    export_regression_table,
    run_panel_2sls,
    run_random_effects,
)


def make_panel() -> pd.DataFrame:
    rows = []
    for i in range(12):
        alpha = i * 0.4
        for t in range(6):
            z = 0.2 * i + 0.3 * t + ((i + t) % 2)
            x1 = 1.5 * z + 0.1 * i + 0.2 * t
            x2 = 0.5 * i - 0.1 * t
            y = 2.0 * x1 - 1.0 * x2 + alpha + 0.3 * t
            rows.append({"id": i, "t": t, "y": y, "x1": x1, "x2": x2, "z": z})
    return pd.DataFrame(rows)


def test_random_effects_runs_and_returns_structural_params():
    df = make_panel()
    spec = RandomEffectsSpec(dependent="y", regressors=["x1", "x2"])
    result = run_random_effects(spec, df, entity="id", time="t")

    assert result.nobs == len(df)
    assert "x1" in result.params.index
    assert "x2" in result.params.index
    assert result.backend == "native-random-effects"
    assert result.theta_by_entity.shape[0] == df["id"].nunique()


def test_panel_2sls_runs_with_entity_and_time_effects():
    df = make_panel()
    spec = PanelIVSpec(
        dependent="y",
        exog=["x2"],
        endogenous=["x1"],
        instruments=["z"],
        entity_effects=True,
        time_effects=True,
    )
    result = run_panel_2sls(spec, df, entity="id", time="t")

    assert result.nobs == len(df)
    assert "x1" in result.params.index
    assert "x2" in result.params.index
    assert result.backend == "native-panel-2sls"
    assert "x1" in result.first_stage_r2


def test_export_regression_table_markdown(tmp_path: Path):
    df = make_panel()
    result = run_random_effects(
        RandomEffectsSpec(dependent="y", regressors=["x1", "x2"]), df, entity="id", time="t"
    )
    out = tmp_path / "results.md"

    export_regression_table([result], out, fmt="markdown")

    assert out.exists()
    assert "x1" in out.read_text(encoding="utf-8")
