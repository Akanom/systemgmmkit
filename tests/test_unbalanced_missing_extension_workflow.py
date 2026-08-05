from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from scripts.parity.system_gmm_certification_registry import (
    REGISTRY_PATH,
    load_certification_registry,
)

ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = ROOT / "artifacts" / "parity" / "xtabond2" / "specs"


def test_extension_manifest_defers_authority_to_central_registry() -> None:
    manifest = json.loads((CANDIDATES / "unbalanced_missing_extension_manifest.json").read_text())
    registry = load_certification_registry(REGISTRY_PATH)

    assert "certification authority is" in manifest["authority"]
    assert {spec["status"] for spec in manifest["specifications"]} == {"REGISTERED"}
    assert {spec["id"] for spec in manifest["specifications"]}.issubset(registry.specifications)


def test_extension_fixtures_cover_distinct_unbalanced_and_missing_contracts() -> None:
    unbalanced = pd.read_csv(CANDIDATES / "system_gmm_unbalanced_panel" / "fixture.csv")
    variable_missing = pd.read_csv(CANDIDATES / "system_gmm_variable_missing" / "fixture.csv")

    counts = unbalanced.groupby("id")["t"].nunique()
    assert counts.nunique() > 1
    assert unbalanced.sort_values(["id", "t"]).groupby("id")["t"].diff().gt(1).any()
    assert variable_missing[["x", "w"]].isna().any().all()
    assert not variable_missing[["id", "t", "y"]].isna().any().any()


def test_native_sample_keys_are_exact_and_match_reported_n() -> None:
    for spec_id in ("system_gmm_unbalanced_panel", "system_gmm_variable_missing"):
        directory = CANDIDATES / spec_id
        sample = pd.read_csv(directory / "native_sample.csv")
        diagnostic = pd.read_csv(directory / "native_diagnostics.csv").iloc[0]

        assert list(sample.columns) == ["id", "t"]
        assert not sample.duplicated(["id", "t"]).any()
        assert len(sample) == int(diagnostic["native_nobs"])


def test_stata_extension_exports_exact_sample_and_comparator_metadata() -> None:
    driver = (ROOT / "scripts" / "parity" / "rerun_xtabond2_unbalanced_missing.do").read_text()
    assert "SYSTEMGMMKIT_UNBALANCED_MISSING_BEGIN" in driver
    assert "SYSTEMGMMKIT_UNBALANCED_MISSING_COMPLETE" in driver

    for spec_id in ("system_gmm_unbalanced_panel", "system_gmm_variable_missing"):
        do_file = CANDIDATES / spec_id / f"{spec_id}.do"
        text = do_file.read_text()
        assert "e(sample)" in text
        assert "stata_sample.csv" in text
        assert "gen double stata_version = c(stata_version)" in text
        assert "xtabond2_e_version" in text
        assert "xtabond2_ado_header" in text
