from __future__ import annotations

import pandas as pd


def _panel():
    rows = []
    for i in range(8):
        for t in range(5):
            x = float(t + i)
            y = 1.0 + 2.0 * x + i * 0.2 + t * 0.1
            rows.append({"entity": i, "time": t, "y": y, "x": x})
    return pd.DataFrame(rows)


def test_hausman_fe_re_done():
    from systemgmmkit.diagnostics import hausman_fe_re

    result = hausman_fe_re(_panel(), y="y", x=["x"], entity="entity", time="time")

    assert result.name == "hausman_fe_re"
    assert result.statistic >= 0
    assert 0 <= result.pvalue <= 1


def test_breusch_pagan_lm_done():
    from systemgmmkit.diagnostics import breusch_pagan_lm

    result = breusch_pagan_lm(_panel(), y="y", x=["x"], entity="entity", time="time")

    assert result.name == "breusch_pagan_lm_re_vs_pooled"
    assert result.statistic >= 0
    assert 0 <= result.pvalue <= 1


def test_wooldridge_serial_correlation_done():
    from systemgmmkit.diagnostics import wooldridge_serial_correlation

    result = wooldridge_serial_correlation(_panel(), y="y", x=["x"], entity="entity", time="time")

    assert result.name == "wooldridge_serial_correlation"
    assert 0 <= result.pvalue <= 1


def test_pesaran_cd_done():
    from systemgmmkit.diagnostics import pesaran_cd

    residuals = pd.DataFrame(
        {
            "entity": [1, 1, 1, 2, 2, 2, 3, 3, 3],
            "time": [1, 2, 3, 1, 2, 3, 1, 2, 3],
            "residual": [0.1, 0.2, 0.1, 0.2, 0.1, 0.3, -0.1, -0.2, -0.1],
        }
    )

    result = pesaran_cd(residuals, entity="entity", time="time")

    assert result.name == "pesaran_cd_cross_sectional_dependence"
    assert 0 <= result.pvalue <= 1


def test_modified_wald_done():
    from systemgmmkit.diagnostics import modified_wald_groupwise_heteroskedasticity

    residuals = pd.DataFrame(
        {
            "entity": [1, 1, 1, 2, 2, 2, 3, 3, 3],
            "residual": [0.1, 0.2, 0.1, 0.4, 0.5, 0.3, -0.1, -0.2, -0.1],
        }
    )

    result = modified_wald_groupwise_heteroskedasticity(residuals, entity="entity")

    assert result.name == "modified_wald_groupwise_heteroskedasticity"
    assert result.statistic >= 0
    assert 0 <= result.pvalue <= 1
