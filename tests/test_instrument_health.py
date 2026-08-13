from __future__ import annotations

from types import SimpleNamespace

import pandas as pd
import pytest

from systemgmmkit.diagnostics import check_instrument_health
from systemgmmkit.native_gmm import NativeGMMResult
from systemgmmkit.pydynpd_backend import PydynpdGMMResult
from systemgmmkit.spec import DynamicPanelSpec


@pytest.mark.parametrize(
    ("n_instruments", "n_groups", "status"),
    [
        (101, 100, "critical"),
        (100, 100, "approaching"),
        (81, 100, "approaching"),
        (80, 100, "acceptable"),
    ],
)
def test_check_instrument_health_boundaries(n_instruments, n_groups, status):
    result = SimpleNamespace(n_instruments=n_instruments, n_groups=n_groups)
    health = check_instrument_health(result)

    assert health.status == status
    assert health.ratio == pytest.approx(n_instruments / n_groups)
    assert health.proliferation_detected is (status == "critical")


def test_check_instrument_health_handles_missing_counts():
    health = check_instrument_health(SimpleNamespace(n_instruments=12))

    assert health.status == "unavailable"
    assert health.ratio is None


@pytest.mark.parametrize("warning_ratio", [0.0, -0.1, 1.1])
def test_check_instrument_health_validates_warning_ratio(warning_ratio):
    with pytest.raises(ValueError, match="warning_ratio"):
        check_instrument_health(
            SimpleNamespace(n_instruments=1, n_groups=2), warning_ratio=warning_ratio
        )


def test_native_result_summary_includes_instrument_health():
    index = pd.Index(["L1.y"])
    result = NativeGMMResult(
        spec=DynamicPanelSpec(dependent="y", regressors=["L1.y"]),
        nobs=50,
        n_instruments=11,
        params=pd.Series([0.5], index=index),
        std_errors=pd.Series([0.1], index=index),
        zstats=pd.Series([5.0], index=index),
        pvalues=pd.Series([0.0], index=index),
        residuals=pd.Series([0.0]),
        covariance_type="robust",
        backend="native",
        notes=[],
        n_groups=10,
    )

    text = result.to_markdown()
    assert "Instrument health" in text
    assert "CRITICAL" in text
    assert "does not automatically invalidate" not in text


def test_pydynpd_result_summary_includes_instrument_health():
    result = PydynpdGMMResult(
        params=pd.Series({"L1.y": 0.5}),
        std_errors=pd.Series({"L1.y": 0.1}),
        pvalues=pd.Series({"L1.y": 0.0}),
        n_instruments=8,
        n_groups=10,
    )

    text = result.to_markdown()
    assert "Instrument health" in text
    assert "ACCEPTABLE" in text
