from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd
import pytest

from scripts.parity import build_certification_report as report_builder
from scripts.parity import compare_xtabond2_ar_diagnostics as comparator
from scripts.parity.apply_xtabond2_system_gmm_certificate import (
    LEGACY_BASELINE_SPEC,
    UNIFIED_CERTIFICATE,
    build_legacy_projection,
)
from scripts.parity.build_xtabond2_certification_driver import (
    DRIVER_PATH,
    render_stata_driver,
)
from scripts.parity.build_xtabond2_comparator_provenance import (
    BEGIN_MARKER,
    COMPLETE_MARKER,
    build_attestation,
)
from scripts.parity.system_gmm_certification_registry import (
    REGISTRY_PATH,
    REPOSITORY_ROOT,
    canonical_text_sha256,
    certification_registry_sha256,
    comparator_provenance_sha256,
    load_certification_registry,
    load_comparator_provenance,
)

PATH_FIELDS = (
    "data",
    "do_file",
    "builder",
    "runner",
    "native_params",
    "native_diagnostics",
    "stata_params",
    "stata_diagnostics",
)


def test_registry_is_portable_and_declares_the_maintained_six_specs() -> None:
    registry = load_certification_registry(REGISTRY_PATH)

    assert registry.schema_version == 1
    assert len(registry.specifications) == 6
    assert registry.oracle == "Stata xtabond2"
    assert certification_registry_sha256(REGISTRY_PATH)

    for spec_id, config in registry.specifications.items():
        assert spec_id.startswith("system_gmm_")
        for field in PATH_FIELDS:
            path = config[field]
            assert isinstance(path, Path)
            assert not path.is_absolute()
            assert ".." not in path.parts
            assert (REPOSITORY_ROOT / path).is_file()
        for path in config.get("support_files", ()):
            assert not path.is_absolute()
            assert ".." not in path.parts
            assert (REPOSITORY_ROOT / path).is_file()


def test_comparator_provenance_is_sanitized_and_bound_to_tracked_outputs() -> None:
    registry = load_certification_registry(REGISTRY_PATH)
    provenance = load_comparator_provenance(registry)
    provenance_path = REPOSITORY_ROOT / registry.comparator_provenance
    serialized = provenance_path.read_text(encoding="utf-8")

    assert provenance.attestation_kind == "historical-log-derived"
    assert provenance.registry_sha256 == certification_registry_sha256(REGISTRY_PATH)
    assert comparator_provenance_sha256(registry)
    assert provenance.source_log_committed is False
    assert tuple(registry.specifications) == provenance.certified_specifications
    assert "C:\\Users\\" not in serialized
    assert "C:/Users/" not in serialized
    assert "OneDrive" not in serialized
    assert "license" not in serialized.lower()
    assert "serial" not in serialized.lower()

    for spec_id, config in registry.specifications.items():
        hashes = provenance.output_hashes[spec_id]
        assert hashes["stata_params_sha256"] == canonical_text_sha256(
            REPOSITORY_ROOT / config["stata_params"]
        )
        assert hashes["stata_diagnostics_sha256"] == canonical_text_sha256(
            REPOSITORY_ROOT / config["stata_diagnostics"]
        )
        if "stata_sample" in config:
            assert hashes["stata_sample_sha256"] == canonical_text_sha256(
                REPOSITORY_ROOT / config["stata_sample"]
            )


def _synthetic_certification_log(*, complete_before_specs: bool = False) -> str:
    registry = load_certification_registry(REGISTRY_PATH)
    preamble = [
        BEGIN_MARKER,
        "stata_current_date=01 Jan 2000",
        "stata_current_time=00:00:00",
        f"stata_version={registry.expected_stata_version:g}",
        "stata_flavor=IC",
        "stata_os=Windows",
        "stata_machine_type=PC (64-bit x86-64)",
        registry.expected_xtabond2_ado_header,
    ]
    specs: list[str] = []
    for spec_id in registry.specifications:
        specs.extend(
            [
                f"SYSTEMGMMKIT_RUNNING={spec_id}",
                f'e(version) : "{registry.expected_xtabond2_e_version}"',
            ]
        )
    suffix = [
        "stata_current_date=01 Jan 2000",
        "stata_current_time=00:00:01",
    ]
    if complete_before_specs:
        return "\n".join([*preamble, COMPLETE_MARKER, *specs, *suffix, ""])
    return "\n".join([*preamble, *specs, COMPLETE_MARKER, *suffix, ""])


def test_attestation_parser_rejects_spec_evidence_after_completion(tmp_path: Path) -> None:
    registry = load_certification_registry(REGISTRY_PATH)
    log_path = tmp_path / "certification.log"
    ado_path = tmp_path / "xtabond2.ado"
    ado_path.write_text(registry.expected_xtabond2_ado_header + "\n", encoding="utf-8")
    log_path.write_text(_synthetic_certification_log(complete_before_specs=True), encoding="utf-8")

    with pytest.raises(ValueError, match="outside the run boundary"):
        build_attestation(log_path, ado_path)


def test_attestation_parser_accepts_bounded_allowlisted_evidence(tmp_path: Path) -> None:
    registry = load_certification_registry(REGISTRY_PATH)
    log_path = tmp_path / "certification.log"
    ado_path = tmp_path / "xtabond2.ado"
    ado_path.write_text(registry.expected_xtabond2_ado_header + "\n", encoding="utf-8")
    log_path.write_text(_synthetic_certification_log(), encoding="utf-8")

    attestation = build_attestation(log_path, ado_path)

    assert attestation["certified_specifications"] == list(registry.specifications)
    assert attestation["stata_reported_start"] == "01 Jan 2000 00:00:00"
    assert attestation["stata_reported_end"] == "01 Jan 2000 00:00:01"


def test_attestation_uses_embedded_metadata_when_log_omits_some_ereturn_lists(
    tmp_path: Path,
) -> None:
    registry = load_certification_registry(REGISTRY_PATH)
    log_path = tmp_path / "certification.log"
    ado_path = tmp_path / "xtabond2.ado"
    ado_path.write_text(registry.expected_xtabond2_ado_header + "\n", encoding="utf-8")

    omitted = set(tuple(registry.specifications)[-2:])
    active_spec = ""
    lines: list[str] = []
    for line in _synthetic_certification_log().splitlines():
        if line.startswith("SYSTEMGMMKIT_RUNNING="):
            active_spec = line.split("=", 1)[1]
        if line.startswith("e(version)") and active_spec in omitted:
            continue
        lines.append(line)
        if line == registry.expected_xtabond2_ado_header:
            lines.append(line)
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    attestation = build_attestation(log_path, ado_path)

    assert attestation["certified_specifications"] == list(registry.specifications)


def test_registry_requires_native_and_stata_sample_paths_together(tmp_path: Path) -> None:
    raw = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    raw["specifications"][-1].pop("stata_sample")
    path = tmp_path / "invalid-registry.json"
    path.write_text(json.dumps(raw), encoding="utf-8")

    with pytest.raises(ValueError, match="native_sample and stata_sample together"):
        load_certification_registry(path)


@pytest.mark.parametrize("invalid_value", [float("inf"), float("nan")])
def test_registry_rejects_nonfinite_tolerances(tmp_path: Path, invalid_value: float) -> None:
    raw = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    raw["tolerances"]["coefficient_absolute"] = invalid_value
    path = tmp_path / "invalid-registry.json"
    path.write_text(json.dumps(raw), encoding="utf-8")

    with pytest.raises(ValueError, match="positive number"):
        load_certification_registry(path)


def test_comparator_and_report_builder_consume_the_registry() -> None:
    registry = load_certification_registry(REGISTRY_PATH)
    expected_ids = tuple(registry.specifications)

    assert tuple(comparator.SPECS) == expected_ids
    assert certification_registry_sha256(REGISTRY_PATH) == comparator.REGISTRY_SHA256
    assert expected_ids == report_builder.CERTIFIED_SYSTEM_GMM_SPEC_IDS
    assert frozenset(expected_ids) == report_builder.CERTIFIED_SYSTEM_GMM_SPECS

    rows = [
        comparator._compare_spec(spec_id, config)
        for spec_id, config in registry.specifications.items()
    ]
    assert [row["spec"] for row in rows] == list(expected_ids)
    assert all(row["same_overid_df"] for row in rows)
    assert all(
        row["certification_registry_sha256"] == certification_registry_sha256(REGISTRY_PATH)
        for row in rows
    )

    committed = pd.read_csv(
        REPOSITORY_ROOT
        / comparator.BASE.relative_to(REPOSITORY_ROOT)
        / "diagnostic_parity_certificate.csv"
    )
    expected = pd.DataFrame(rows)
    pd.testing.assert_frame_equal(committed, expected, check_dtype=False)


def test_generated_stata_driver_is_in_sync_with_registry() -> None:
    registry = load_certification_registry(REGISTRY_PATH)
    rendered = render_stata_driver(registry)

    assert DRIVER_PATH.read_text(encoding="utf-8") == rendered
    assert "C:/Users/" not in rendered
    assert "C:\\Users\\" not in rendered

    run_lines = [
        line.removeprefix('display as text "SYSTEMGMMKIT_RUNNING=').removesuffix('"')
        for line in rendered.splitlines()
        if line.startswith('display as text "SYSTEMGMMKIT_RUNNING=')
    ]
    do_lines = [
        line.removeprefix('do "').removesuffix('"')
        for line in rendered.splitlines()
        if line.startswith('do "')
    ]
    assert run_lines == list(registry.specifications)
    assert do_lines == [config["do_file"].as_posix() for config in registry.specifications.values()]


def test_canonical_text_digest_is_independent_of_line_endings(tmp_path: Path) -> None:
    lf = tmp_path / "lf.txt"
    crlf = tmp_path / "crlf.txt"
    lf.write_bytes(b"first\nsecond\n")
    crlf.write_bytes(b"first\r\nsecond\r\n")

    assert canonical_text_sha256(lf) == canonical_text_sha256(crlf)


def test_generated_report_claims_are_in_sync_with_registry() -> None:
    registry = load_certification_registry(REGISTRY_PATH)
    report = report_builder.build_report(generated_at="2000-01-01 00:00:00 UTC")

    registry_relative = REGISTRY_PATH.relative_to(REPOSITORY_ROOT).as_posix()
    assert f"Certification registry: `{registry_relative}`" in report
    assert f"{len(registry.specifications)} aligned specifications" in report
    assert f"{len(registry.specifications)}-spec" in report
    for spec_id in registry.specifications:
        assert f"`{spec_id}`" in report

    committed = (REPOSITORY_ROOT / report_builder.REPORT_PATH).read_text(encoding="utf-8")
    match = re.search(r"^Generated: `([^`]+)`$", committed, flags=re.MULTILINE)
    assert match is not None
    assert committed == report_builder.build_report(generated_at=match.group(1))


def test_legacy_baseline_certificate_is_only_a_unified_projection() -> None:
    source = pd.read_csv(REPOSITORY_ROOT / UNIFIED_CERTIFICATE)
    expected = source.loc[source["spec"].eq(LEGACY_BASELINE_SPEC)].reset_index(drop=True)
    projection = build_legacy_projection()

    assert projection.pop("compatibility_source").eq(UNIFIED_CERTIFICATE.as_posix()).all()
    pd.testing.assert_frame_equal(projection.reset_index(drop=True), expected)
