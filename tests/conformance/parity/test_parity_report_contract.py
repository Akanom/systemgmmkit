from __future__ import annotations

import pytest

REQUIRED_PARITY_REPORT_COLUMNS = [
    "spec",
    "native_nobs",
    "native_n_instruments",
    "pydynpd_nobs",
    "pydynpd_n_groups",
    "pydynpd_n_instruments",
    "hansen_p",
    "ar1_p",
    "ar2_p",
    "status",
    "original_status",
    "blocks_release",
    "policy_message",
    "same_instrument_count",
    "max_abs_coef_diff",
    "mean_abs_coef_diff",
    "sign_match_rate",
]


@pytest.mark.conformance
@pytest.mark.parity
def test_parity_report_required_columns_are_stable():
    assert "spec" in REQUIRED_PARITY_REPORT_COLUMNS
    assert "status" in REQUIRED_PARITY_REPORT_COLUMNS
    assert "original_status" in REQUIRED_PARITY_REPORT_COLUMNS
    assert "blocks_release" in REQUIRED_PARITY_REPORT_COLUMNS
    assert "max_abs_coef_diff" in REQUIRED_PARITY_REPORT_COLUMNS
    assert "sign_match_rate" in REQUIRED_PARITY_REPORT_COLUMNS
