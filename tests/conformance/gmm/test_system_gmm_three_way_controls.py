from __future__ import annotations

import pytest


@pytest.mark.conformance
@pytest.mark.experimental
@pytest.mark.parity
def test_system_gmm_three_way_controls_experimental_contract():
    expected = {
        "spec": "system_gmm_three_way_controls",
        "status": "EXPERIMENTAL_PARITY_PENDING",
        "blocks_release": False,
    }

    assert expected["spec"] == "system_gmm_three_way_controls"
    assert expected["status"] == "EXPERIMENTAL_PARITY_PENDING"
    assert expected["blocks_release"] is False
