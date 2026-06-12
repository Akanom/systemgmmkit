from __future__ import annotations

import pytest

DIAGNOSTIC_CONFORMANCE_TARGETS = {
    "hausman_fe_re": "HIGH",
    "breusch_pagan_lm_re_vs_pooled": "HIGH",
    "wooldridge_serial_correlation": "HIGH",
    "pesaran_cd_cross_sectional_dependence": "HIGH",
    "modified_wald_groupwise_heteroskedasticity": "MEDIUM_HIGH",
    "ar1": "VERY_HIGH",
    "ar2": "VERY_HIGH",
    "hansen": "VERY_HIGH",
    "sargan": "VERY_HIGH",
    "diff_hansen": "VERY_HIGH",
    "instrument_count": "VERY_HIGH",
    "instrument_matrix": "VERY_HIGH",
    "missing_data_estimation_sample": "VERY_HIGH",
    "balanced_unbalanced_panel_handling": "VERY_HIGH",
}


@pytest.mark.conformance
def test_required_diagnostic_targets_are_registered():
    required = {
        "hausman_fe_re",
        "breusch_pagan_lm_re_vs_pooled",
        "wooldridge_serial_correlation",
        "pesaran_cd_cross_sectional_dependence",
        "ar1",
        "ar2",
        "hansen",
        "sargan",
        "diff_hansen",
        "instrument_count",
        "missing_data_estimation_sample",
    }

    assert required.issubset(DIAGNOSTIC_CONFORMANCE_TARGETS)
