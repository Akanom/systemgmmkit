from __future__ import annotations

import pytest


@pytest.mark.conformance
@pytest.mark.experimental
@pytest.mark.parity
def test_system_gmm_baseline_controls_experimental_contract():
    """
    Contract test for the already-used benchmark name:

    system_gmm_baseline_controls

    Expected current status:
    - status: EXPERIMENTAL_PARITY_PENDING
    - sample/instrument parity may pass
    - coefficient-level strict parity not certified yet
    """

    expected = {
        "spec": "system_gmm_baseline_controls",
        "status": "EXPERIMENTAL_PARITY_PENDING",
        "blocks_release": False,
    }

    assert expected["spec"] == "system_gmm_baseline_controls"
    assert expected["status"] == "EXPERIMENTAL_PARITY_PENDING"
    assert expected["blocks_release"] is False
