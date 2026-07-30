from __future__ import annotations

CONFORMANCE_STATUS = {
    "difference_gmm_baseline_controls": {
        "status": "PASS_PARITY",
        "original_status": "PASS_STRICT",
        "blocks_release": False,
        "strict_reference": "pydynpd/xtabond2",
    },
    "system_gmm_baseline_controls": {
        "status": "PASS_PARITY",
        "original_status": "PASS_STRICT",
        "blocks_release": False,
        "strict_reference": "pydynpd/xtabond2",
    },
    "system_gmm_three_way_controls": {
        "status": "EXPERIMENTAL_PARITY_PENDING",
        "original_status": "FAIL_PARITY",
        "blocks_release": False,
        "strict_reference": "pydynpd/xtabond2",
    },
    "system_gmm_three_way_no_controls": {
        "status": "EXPERIMENTAL_PARITY_PENDING",
        "original_status": "FAIL_PARITY",
        "blocks_release": False,
        "strict_reference": "pydynpd/xtabond2",
    },
    "system_gmm_decomposition_controls": {
        "status": "EXPERIMENTAL_PARITY_PENDING",
        "original_status": "FAIL_PARITY",
        "blocks_release": False,
        "strict_reference": "pydynpd/xtabond2",
    },
}


def test_known_conformance_specs_are_registered():
    required = {
        "difference_gmm_baseline_controls",
        "system_gmm_baseline_controls",
        "system_gmm_three_way_controls",
        "system_gmm_three_way_no_controls",
        "system_gmm_decomposition_controls",
    }

    assert required.issubset(CONFORMANCE_STATUS)


def test_difference_gmm_is_current_strict_pass():
    spec = CONFORMANCE_STATUS["difference_gmm_baseline_controls"]

    assert spec["status"] == "PASS_PARITY"
    assert spec["original_status"] == "PASS_STRICT"
    assert spec["blocks_release"] is False


def test_only_maintained_system_gmm_baseline_is_fully_certified():
    baseline = CONFORMANCE_STATUS["system_gmm_baseline_controls"]
    assert baseline["status"] == "PASS_PARITY"
    assert baseline["original_status"] == "PASS_STRICT"

    system_specs = [
        "system_gmm_three_way_controls",
        "system_gmm_three_way_no_controls",
        "system_gmm_decomposition_controls",
    ]

    for name in system_specs:
        assert CONFORMANCE_STATUS[name]["status"] == "EXPERIMENTAL_PARITY_PENDING"
