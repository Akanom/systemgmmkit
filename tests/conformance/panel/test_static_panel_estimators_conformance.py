from __future__ import annotations

import pytest

STATIC_PANEL_CONFORMANCE_TARGETS = {
    "pooled_ols": {
        "reference": ["statsmodels.OLS", "Stata reg"],
        "priority": "HIGH",
        "required_status": "STRICT_PARITY_PENDING",
    },
    "fixed_effects": {
        "reference": ["linearmodels.PanelOLS", "Stata xtreg, fe"],
        "priority": "HIGH",
        "required_status": "STRICT_PARITY_PENDING",
    },
    "two_way_fixed_effects": {
        "reference": [
            "linearmodels.PanelOLS(entity_effects=True, time_effects=True)",
            "Stata xtreg, fe + time dummies",
        ],
        "priority": "HIGH",
        "required_status": "STRICT_PARITY_PENDING",
    },
    "random_effects": {
        "reference": ["linearmodels.RandomEffects", "Stata xtreg, re"],
        "priority": "HIGH",
        "required_status": "STRICT_PARITY_PENDING",
    },
    "first_difference": {
        "reference": ["manual differencing", "Stata xtreg, fd"],
        "priority": "HIGH",
        "required_status": "TO_BE_ADDED",
    },
    "panel_iv_2sls": {
        "reference": ["linearmodels.iv.IV2SLS", "Stata ivregress 2sls", "Stata xtivreg"],
        "priority": "HIGH",
        "required_status": "STRICT_PARITY_PENDING",
    },
}


@pytest.mark.conformance
def test_static_panel_conformance_targets_are_registered():
    assert "pooled_ols" in STATIC_PANEL_CONFORMANCE_TARGETS
    assert "fixed_effects" in STATIC_PANEL_CONFORMANCE_TARGETS
    assert "two_way_fixed_effects" in STATIC_PANEL_CONFORMANCE_TARGETS
    assert "random_effects" in STATIC_PANEL_CONFORMANCE_TARGETS
    assert "first_difference" in STATIC_PANEL_CONFORMANCE_TARGETS
    assert "panel_iv_2sls" in STATIC_PANEL_CONFORMANCE_TARGETS


@pytest.mark.conformance
def test_first_difference_is_correctly_marked_to_be_added():
    assert STATIC_PANEL_CONFORMANCE_TARGETS["first_difference"]["required_status"] == "TO_BE_ADDED"
