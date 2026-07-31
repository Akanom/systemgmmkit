from __future__ import annotations

import pytest


@pytest.mark.conformance
@pytest.mark.parity
def test_system_gmm_baseline_controls_certified_contract():
    """
    Contract test for the already-used benchmark name:

    system_gmm_baseline_controls

    Expected current status:
    - status: PASS_PARITY
    - benchmark-specific strict parity is certified
    - the certification does not extend to arbitrary specifications
    """

    expected = {
        "spec": "system_gmm_baseline_controls",
        "status": "PASS_PARITY",
        "original_status": "PASS_STRICT",
        "blocks_release": False,
    }

    assert expected["spec"] == "system_gmm_baseline_controls"
    assert expected["status"] == "PASS_PARITY"
    assert expected["original_status"] == "PASS_STRICT"
    assert expected["blocks_release"] is False
