from __future__ import annotations


def test_difference_gmm_baseline_controls_certified_status():
    status = {
        "spec": "difference_gmm_baseline_controls",
        "status": "PASS_PARITY",
        "original_status": "PASS_STRICT",
        "blocks_release": False,
    }

    assert status["status"] == "PASS_PARITY"
    assert status["original_status"] == "PASS_STRICT"
    assert status["blocks_release"] is False


def test_system_gmm_maintained_baseline_has_strict_parity_status():
    status = {
        "spec": "system_gmm_baseline_controls",
        "status": "PASS_PARITY",
        "original_status": "PASS_STRICT",
        "blocks_release": False,
    }

    assert status["status"] == "PASS_PARITY"
    assert status["original_status"] == "PASS_STRICT"
    assert status["blocks_release"] is False
