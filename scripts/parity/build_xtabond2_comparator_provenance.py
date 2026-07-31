from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

if __package__:
    from .system_gmm_certification_registry import (
        HISTORICAL_ATTESTATION_KIND,
        HISTORICAL_CAPTURE_METHOD,
        REGISTRY_PATH,
        REPOSITORY_ROOT,
        canonical_text_sha256,
        certification_registry_sha256,
        load_certification_registry,
        repository_path,
    )
else:
    from system_gmm_certification_registry import (
        HISTORICAL_ATTESTATION_KIND,
        HISTORICAL_CAPTURE_METHOD,
        REGISTRY_PATH,
        REPOSITORY_ROOT,
        canonical_text_sha256,
        certification_registry_sha256,
        load_certification_registry,
        repository_path,
    )

GENERATOR_PATH = Path("scripts/parity/build_xtabond2_comparator_provenance.py")
BEGIN_MARKER = "SYSTEMGMMKIT_XTABOND2_RERUN_BEGIN"
COMPLETE_MARKER = "SYSTEMGMMKIT_XTABOND2_RERUN_COMPLETE"


def _output_lines(text: str) -> list[str]:
    """Return Stata output lines while excluding echoed commands and continuations."""
    return [
        line.strip()
        for line in text.splitlines()
        if line.strip() and not line.lstrip().startswith((".", ">"))
    ]


def _values(lines: list[str], key: str) -> list[str]:
    prefix = f"{key}="
    return [line.removeprefix(prefix).strip() for line in lines if line.startswith(prefix)]


def _single(values: list[str], label: str) -> str:
    if len(values) != 1:
        raise ValueError(f"Expected exactly one {label}, found {len(values)}.")
    return values[0]


def _parse_spec_versions(lines: list[str]) -> tuple[list[str], dict[str, str]]:
    order: list[str] = []
    versions: dict[str, str] = {}
    active_spec: str | None = None
    version_pattern = re.compile(r'^e\(version\)\s*:\s*"([^"]+)"$')

    for line in lines:
        if line.startswith("SYSTEMGMMKIT_RUNNING="):
            active_spec = line.partition("=")[2].strip()
            if active_spec in order:
                raise ValueError(f"Duplicate certification marker for {active_spec}.")
            order.append(active_spec)
            continue
        match = version_pattern.fullmatch(line)
        if match is None:
            continue
        if active_spec is None:
            raise ValueError("Found xtabond2 e(version) before a specification marker.")
        if active_spec in versions:
            raise ValueError(f"Duplicate xtabond2 e(version) for {active_spec}.")
        versions[active_spec] = match.group(1)

    return order, versions


def build_attestation(log_path: Path, ado_path: Path) -> dict[str, object]:
    registry = load_certification_registry(REGISTRY_PATH)
    log_text = log_path.read_text(encoding="utf-8", errors="strict")
    lines = _output_lines(log_text)

    if lines.count(BEGIN_MARKER) != 1 or lines.count(COMPLETE_MARKER) != 1:
        raise ValueError("Certification log is missing a unique begin or completion marker.")
    begin_index = lines.index(BEGIN_MARKER)
    complete_index = lines.index(COMPLETE_MARKER)
    if begin_index >= complete_index:
        raise ValueError("Certification completion marker precedes the begin marker.")
    run_lines = lines[begin_index + 1 : complete_index]
    outside_run = lines[:begin_index] + lines[complete_index + 1 :]
    if any(
        line.startswith("SYSTEMGMMKIT_RUNNING=") or line.startswith("e(version)")
        for line in outside_run
    ):
        raise ValueError("Certification specification evidence occurs outside the run boundary.")

    order, versions = _parse_spec_versions(run_lines)
    expected_order = list(registry.specifications)
    if order != expected_order or set(versions) != set(expected_order):
        raise ValueError("Certification log does not cover the registry specifications exactly.")
    unique_versions = set(versions.values())
    if unique_versions != {registry.expected_xtabond2_e_version}:
        raise ValueError(f"Unexpected xtabond2 e(version) values: {sorted(unique_versions)}")

    stata_versions = _values(run_lines, "stata_version")
    stata_version = float(_single(stata_versions, "Stata version"))
    if stata_version != registry.expected_stata_version:
        raise ValueError(f"Unexpected Stata version: {stata_version}")

    start_dates = _values(run_lines, "stata_current_date")
    start_times = _values(run_lines, "stata_current_time")
    end_lines = lines[complete_index + 1 :]
    end_dates = _values(end_lines, "stata_current_date")
    end_times = _values(end_lines, "stata_current_time")
    if any(len(values) != 1 for values in (start_dates, start_times, end_dates, end_times)):
        raise ValueError("Certification log must contain start and end Stata timestamps.")

    ado_lines = ado_path.read_text(encoding="utf-8", errors="strict").splitlines()
    ado_header = next((line.strip() for line in ado_lines if line.strip()), "")
    if ado_header != registry.expected_xtabond2_ado_header:
        raise ValueError(f"Unexpected installed xtabond2 ado header: {ado_header!r}")
    if run_lines.count(ado_header) != 1:
        raise ValueError(
            "Certification log does not contain the expected xtabond2 ado header once."
        )

    output_hashes: dict[str, dict[str, str]] = {}
    for spec_id, config in registry.specifications.items():
        output_hashes[spec_id] = {
            "stata_params_sha256": canonical_text_sha256(repository_path(config["stata_params"])),
            "stata_diagnostics_sha256": canonical_text_sha256(
                repository_path(config["stata_diagnostics"])
            ),
        }

    return {
        "schema_version": 1,
        "attestation_kind": HISTORICAL_ATTESTATION_KIND,
        "capture_method": HISTORICAL_CAPTURE_METHOD,
        "text_digest_algorithm": registry.text_digest_algorithm,
        "registry_path": REGISTRY_PATH.relative_to(REPOSITORY_ROOT).as_posix(),
        "registry_sha256": certification_registry_sha256(REGISTRY_PATH),
        "generator": GENERATOR_PATH.as_posix(),
        "generator_sha256": canonical_text_sha256(repository_path(GENERATOR_PATH)),
        "run_log_sha256": canonical_text_sha256(log_path),
        "source_log_committed": False,
        "source_binding_limitation": (
            "The local source log records completed runs and comparator versions but not output "
            "hashes; tracked output hashes were observed when this sanitized attestation was "
            "generated."
        ),
        "stata_version": stata_version,
        "stata_flavor": _single(_values(run_lines, "stata_flavor"), "Stata flavor"),
        "stata_os": _single(_values(run_lines, "stata_os"), "Stata operating system"),
        "stata_machine_type": _single(
            _values(run_lines, "stata_machine_type"), "Stata machine type"
        ),
        "stata_reported_start": f"{start_dates[0]} {start_times[0]}",
        "stata_reported_end": f"{end_dates[0]} {end_times[0]}",
        "xtabond2_e_version": next(iter(unique_versions)),
        "xtabond2_ado_header": ado_header,
        "xtabond2_ado_sha256": canonical_text_sha256(ado_path),
        "xtabond2_ado_hash_observation": (
            "Observed from the installed ado at attestation generation; the certification log "
            "records the matching ado header and e(version), not the ado hash."
        ),
        "certified_specifications": expected_order,
        "output_hashes": output_hashes,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build a path-free xtabond2 provenance attestation from a local Stata log."
    )
    parser.add_argument("--log", type=Path, required=True, help="Completed Stata certification log")
    parser.add_argument(
        "--ado", type=Path, required=True, help="Installed xtabond2.ado used by Stata"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output JSON; defaults to the registry-declared provenance artifact",
    )
    args = parser.parse_args()

    registry = load_certification_registry(REGISTRY_PATH)
    output_path = args.output or repository_path(registry.comparator_provenance)
    attestation = build_attestation(args.log.resolve(), args.ado.resolve())
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(attestation, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
