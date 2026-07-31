from __future__ import annotations

import pandas as pd
import pytest

from scripts.parity.system_gmm_certification_registry import (
    REGISTRY_PATH,
    REPOSITORY_ROOT,
    load_certification_registry,
)

SPEC_ID = "system_gmm_decomposition_controls"
CERTIFICATE_PATH = (
    REPOSITORY_ROOT / "artifacts" / "parity" / "xtabond2" / "diagnostic_parity_certificate.csv"
)


@pytest.mark.conformance
@pytest.mark.parity
def test_system_gmm_decomposition_controls_certified_contract() -> None:
    registry = load_certification_registry(REGISTRY_PATH)
    certificate = pd.read_csv(CERTIFICATE_PATH).set_index("spec")

    assert SPEC_ID in registry.specifications
    assert SPEC_ID in certificate.index
    row = certificate.loc[SPEC_ID]
    assert row["parameter_status"] == "PASS_PARAMETER_PARITY"
    assert row["diagnostic_status"] == "PASS_DIAGNOSTIC_PARITY"
    assert row["status"] == "PASS_XTABOND2_PARITY"
