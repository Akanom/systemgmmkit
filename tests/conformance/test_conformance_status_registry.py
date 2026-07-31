from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DIAGNOSTIC_CERTIFICATE = pd.read_csv(
    ROOT / "artifacts" / "parity" / "xtabond2" / "diagnostic_parity_certificate.csv"
).set_index("spec")


def _certified_status(spec: str) -> str:
    return str(DIAGNOSTIC_CERTIFICATE.loc[spec, "status"])


CONFORMANCE_STATUS = {
    "difference_gmm_baseline_controls": {
        "status": "PASS_PARITY",
        "original_status": "PASS_STRICT",
        "blocks_release": False,
        "strict_reference": "xtabond2",
        "auxiliary_comparator": "pydynpd",
    },
    "system_gmm_baseline_controls": {
        "status": _certified_status("system_gmm_baseline_controls"),
        "original_status": "FAIL_PARITY",
        "blocks_release": False,
        "strict_reference": "xtabond2",
        "auxiliary_comparator": "pydynpd",
    },
    "system_gmm_no_controls": {
        "status": _certified_status("system_gmm_no_controls"),
        "original_status": "COMPARISON_GENERATED",
        "blocks_release": False,
        "strict_reference": "xtabond2",
        "auxiliary_comparator": "pydynpd",
    },
    "system_gmm_three_way_controls": {
        "status": _certified_status("system_gmm_three_way_controls"),
        "original_status": "FAIL_PARITY",
        "blocks_release": False,
        "strict_reference": "xtabond2",
        "auxiliary_comparator": "pydynpd",
    },
    "system_gmm_three_way_no_controls": {
        "status": "EXPERIMENTAL_PARITY_PENDING",
        "original_status": "FAIL_PARITY",
        "blocks_release": False,
        "strict_reference": "xtabond2",
        "auxiliary_comparator": "pydynpd",
    },
    "system_gmm_decomposition_controls": {
        "status": _certified_status("system_gmm_decomposition_controls"),
        "original_status": "FAIL_PARITY",
        "blocks_release": False,
        "strict_reference": "xtabond2",
        "auxiliary_comparator": "pydynpd",
    },
}


def test_known_conformance_specs_are_registered():
    required = {
        "difference_gmm_baseline_controls",
        "system_gmm_baseline_controls",
        "system_gmm_no_controls",
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


def test_native_system_gmm_diagnostic_parity_is_bounded():
    diagnostic_parity_specs = [
        "system_gmm_baseline_controls",
        "system_gmm_no_controls",
        "system_gmm_three_way_controls",
        "system_gmm_decomposition_controls",
    ]

    for name in diagnostic_parity_specs:
        spec = CONFORMANCE_STATUS[name]
        certificate = DIAGNOSTIC_CERTIFICATE.loc[name]
        assert certificate["parameter_status"] == "PASS_PARAMETER_PARITY"
        assert certificate["diagnostic_status"] == "PASS_DIAGNOSTIC_PARITY"
        assert spec["status"] == "PASS_XTABOND2_PARITY"
        assert spec["strict_reference"] == "xtabond2"
        assert spec["auxiliary_comparator"] == "pydynpd"

    assert (
        CONFORMANCE_STATUS["system_gmm_three_way_no_controls"]["status"]
        == "EXPERIMENTAL_PARITY_PENDING"
    )
