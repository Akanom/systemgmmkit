from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def _normalized(path: str) -> str:
    text = (ROOT / path).read_text(encoding="utf-8").replace("**", "")
    return " ".join(text.split()).lower()


def test_system_gmm_documents_share_the_diagnostic_certification_boundary() -> None:
    paths = (
        "README.md",
        "docs/parity/system_gmm_parity_matrix.md",
        "docs/validation/CONFORMANCE_ROADMAP.md",
        "artifacts/parity/panel_econometrics_certification_report.md",
    )

    for path in paths:
        text = _normalized(path)
        assert "not currently ci-certified" not in text
        assert "benchmark-specific" in text

    readme = _normalized("README.md")
    matrix = _normalized("docs/parity/system_gmm_parity_matrix.md")
    roadmap = _normalized("docs/validation/CONFORMANCE_ROADMAP.md")
    report = _normalized("artifacts/parity/panel_econometrics_certification_report.md")
    assert "signed arellano-bond ar(1)/ar(2) statistics and p-values" in readme
    assert "pass_xtabond2_parity" in matrix
    assert "pass_xtabond2_parity" in roadmap
    assert "signed ar diagnostics" in report
    assert "outside this certified set" in readme
    assert "system_gmm_three_way_no_controls" in matrix
    assert "experimental_parity_pending" in matrix
    assert "experimental_parity_pending" in roadmap


def test_xtabond2_and_pydynpd_have_distinct_reference_roles() -> None:
    matrix = _normalized("docs/parity/system_gmm_parity_matrix.md")
    readme = _normalized("README.md")
    report = _normalized("artifacts/parity/panel_econometrics_certification_report.md")

    for text in (matrix, readme, report):
        assert "xtabond2 is the formal certification oracle" in text.replace("`", "")
        assert "pydynpd is an optional execution backend and auxiliary comparator" in text.replace(
            "`", ""
        )


def test_runtime_note_states_benchmark_specific_diagnostic_parity() -> None:
    dynamic_panel = _normalized("src/systemgmmkit/dynamic_panel.py")
    native_gmm = _normalized("src/systemgmmkit/native_gmm.py")

    for text in (dynamic_panel, native_gmm):
        assert "signed ar diagnostic parity" in text
        assert "four maintained" in text

    assert "does not imply universal stata identity" in dynamic_panel


def test_claimed_system_gmm_specs_have_passing_machine_certificate() -> None:
    certificate = pd.read_csv(
        ROOT / "artifacts" / "parity" / "xtabond2" / "diagnostic_parity_certificate.csv"
    )
    assert set(certificate["spec"]) == {
        "system_gmm_baseline_controls",
        "system_gmm_no_controls",
        "system_gmm_three_way_controls",
        "system_gmm_decomposition_controls",
    }
    assert certificate["parameter_status"].eq("PASS_PARAMETER_PARITY").all()
    assert certificate["diagnostic_status"].eq("PASS_DIAGNOSTIC_PARITY").all()
    assert certificate["status"].eq("PASS_XTABOND2_PARITY").all()
