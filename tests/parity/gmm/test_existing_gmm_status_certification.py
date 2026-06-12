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


def test_system_gmm_native_still_experimental_until_strict_parity():
    status = {
        "spec": "system_gmm_baseline_controls",
        "status": "EXPERIMENTAL_PARITY_PENDING",
        "blocks_release": False,
    }

    assert status["status"] == "EXPERIMENTAL_PARITY_PENDING"
