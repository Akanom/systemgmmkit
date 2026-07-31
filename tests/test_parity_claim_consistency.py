from __future__ import annotations

from pathlib import Path

import pandas as pd

from scripts.parity.system_gmm_certification_registry import (
    REGISTRY_PATH,
    load_certification_registry,
)

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = load_certification_registry(REGISTRY_PATH)


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
        assert "instrument validity" in text

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
    assert "sole specification/oracle/tolerance registry" in readme
    assert "sole specification/oracle/tolerance" in matrix
    assert "sole specification/oracle/tolerance registry" in roadmap


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
    assert "windmeijer-corrected two-step standard errors are not yet certified" not in native_gmm
    assert "sargan parity against xtabond2 is not certified" not in native_gmm


def test_claimed_system_gmm_specs_have_passing_machine_certificate() -> None:
    certificate = pd.read_csv(
        ROOT / "artifacts" / "parity" / "xtabond2" / "diagnostic_parity_certificate.csv"
    )
    assert certificate["spec"].is_unique
    assert len(certificate) == len(REGISTRY.specifications)
    assert tuple(certificate["spec"]) == tuple(REGISTRY.specifications)
    assert certificate["parameter_status"].eq("PASS_PARAMETER_PARITY").all()
    assert certificate["diagnostic_status"].eq("PASS_DIAGNOSTIC_PARITY").all()
    assert certificate["status"].eq("PASS_XTABOND2_PARITY").all()


def test_joss_snapshots_do_not_override_the_unified_certificate() -> None:
    stale_claims = (
        "rely on artifact 24",
        "artifact 24, the maintained",
        "artifact 24: maintained",
        "this is the authoritative parity evidence",
    )
    for path in (ROOT / "artifacts" / "joss").rglob("*"):
        if path.suffix.lower() not in {".md", ".py"}:
            continue
        text = path.read_text(encoding="utf-8").lower()
        for stale_claim in stale_claims:
            assert stale_claim not in text, path

    artifact_24 = _normalized("artifacts/joss/tables/24_maintained_xtabond2_parity/README.md")
    assert "frozen legacy" in artifact_24
    assert "artifacts/parity/xtabond2/" in artifact_24
