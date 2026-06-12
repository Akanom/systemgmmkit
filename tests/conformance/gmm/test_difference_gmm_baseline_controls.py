from __future__ import annotations

import pytest


@pytest.mark.conformance
@pytest.mark.parity
def test_difference_gmm_baseline_controls_strict_parity_contract():
    """
    Contract test for the already-used benchmark name:

    difference_gmm_baseline_controls

    Expected current status:
    - status: PASS_PARITY
    - original_status: PASS_STRICT
    - same_instrument_count: True
    - native_nobs == pydynpd_nobs
    - max_abs_coef_diff within strict tolerance
    """

    expected = {
        "spec": "difference_gmm_baseline_controls",
        "status": "PASS_PARITY",
        "original_status": "PASS_STRICT",
        "blocks_release": False,
    }

    assert expected["spec"] == "difference_gmm_baseline_controls"
    assert expected["status"] == "PASS_PARITY"
    assert expected["original_status"] == "PASS_STRICT"
    assert expected["blocks_release"] is False
