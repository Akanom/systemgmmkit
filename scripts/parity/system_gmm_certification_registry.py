from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict, cast

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = (
    REPOSITORY_ROOT / "artifacts" / "parity" / "xtabond2" / "system_gmm_certification_specs.json"
)
HISTORICAL_ATTESTATION_KIND = "historical-log-derived"
HISTORICAL_CAPTURE_METHOD = (
    "allowlisted fields parsed from a completed Stata certification log and hash-bound exports"
)


class RequiredSpecConfig(TypedDict):
    data: Path
    do_file: Path
    builder: Path
    runner: Path
    native_params: Path
    native_diagnostics: Path
    stata_params: Path
    stata_diagnostics: Path
    expected_params: frozenset[str]
    expected_nobs: int
    expected_n_groups: int
    expected_instruments: int
    expected_df: int
    max_rel_se_diff: float
    transformation: str
    requires_level_iv: bool


class SpecConfig(RequiredSpecConfig, total=False):
    native_sample: Path
    stata_sample: Path
    support_files: tuple[Path, ...]


@dataclass(frozen=True)
class CertificationTolerances:
    coefficient_absolute: float
    windmeijer_standard_error_relative_default: float
    overidentification_statistic_absolute: float
    overidentification_p_value_absolute: float
    ar_z_absolute: float
    ar_p_value_absolute: float


@dataclass(frozen=True)
class CertificationRegistry:
    schema_version: int
    oracle: str
    stata_syntax_version: str
    expected_stata_version: float
    expected_xtabond2_e_version: str
    expected_xtabond2_ado_header: str
    comparator_provenance: Path
    text_digest_algorithm: str
    tolerances: CertificationTolerances
    specifications: dict[str, SpecConfig]


class RequiredStataOutputHashes(TypedDict):
    stata_params_sha256: str
    stata_diagnostics_sha256: str


class StataOutputHashes(RequiredStataOutputHashes, total=False):
    stata_sample_sha256: str


@dataclass(frozen=True)
class ComparatorProvenance:
    schema_version: int
    attestation_kind: str
    capture_method: str
    text_digest_algorithm: str
    registry_path: Path
    registry_sha256: str
    generator: Path
    generator_sha256: str
    run_log_sha256: str
    source_log_committed: bool
    source_binding_limitation: str
    stata_version: float
    stata_flavor: str
    stata_os: str
    stata_machine_type: str
    stata_reported_start: str
    stata_reported_end: str
    xtabond2_e_version: str
    xtabond2_ado_header: str
    xtabond2_ado_sha256: str
    xtabond2_ado_hash_observation: str
    certified_specifications: tuple[str, ...]
    output_hashes: dict[str, StataOutputHashes]


_PATH_FIELDS = (
    "data",
    "do_file",
    "builder",
    "runner",
    "native_params",
    "native_diagnostics",
    "stata_params",
    "stata_diagnostics",
)
_OPTIONAL_SAMPLE_PATH_FIELDS = ("native_sample", "stata_sample")
_POSITIVE_INTEGER_FIELDS = (
    "expected_nobs",
    "expected_n_groups",
    "expected_instruments",
    "expected_df",
)
_POSITIVE_TOLERANCE_FIELDS = (
    "coefficient_absolute",
    "windmeijer_standard_error_relative_default",
    "overidentification_statistic_absolute",
    "overidentification_p_value_absolute",
    "ar_z_absolute",
    "ar_p_value_absolute",
)


def _require_mapping(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object.")
    return cast(dict[str, object], value)


def _require_nonempty_string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string.")
    return value.strip()


def _require_positive_number(value: object, label: str) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(float(value))
        or value <= 0
    ):
        raise ValueError(f"{label} must be a positive number.")
    return float(value)


def _require_positive_integer(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{label} must be a positive integer.")
    return value


def _require_repository_path(value: object, label: str) -> Path:
    raw = _require_nonempty_string(value, label)
    path = Path(raw)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"{label} must stay within the repository: {raw!r}")
    if "\\" in raw or '"' in raw or "\n" in raw or "\r" in raw:
        raise ValueError(f"{label} must be a portable forward-slash path: {raw!r}")
    return path


def _require_sha256(value: object, label: str) -> str:
    digest = _require_nonempty_string(value, label).lower()
    if re.fullmatch(r"[0-9a-f]{64}", digest) is None:
        raise ValueError(f"{label} must be a lowercase hexadecimal SHA-256 digest.")
    return digest


def _load_spec(
    raw_spec: object,
    index: int,
    default_se_tolerance: float,
) -> tuple[str, SpecConfig]:
    spec = _require_mapping(raw_spec, f"specifications[{index}]")
    spec_id = _require_nonempty_string(spec.get("id"), f"specifications[{index}].id")

    paths = {
        field: _require_repository_path(spec.get(field), f"{spec_id}.{field}")
        for field in _PATH_FIELDS
    }
    raw_sample_paths = {field: spec.get(field) for field in _OPTIONAL_SAMPLE_PATH_FIELDS}
    if any(value is not None for value in raw_sample_paths.values()) and not all(
        value is not None for value in raw_sample_paths.values()
    ):
        raise ValueError(f"{spec_id} must declare native_sample and stata_sample together.")
    sample_paths = {
        field: _require_repository_path(value, f"{spec_id}.{field}")
        for field, value in raw_sample_paths.items()
        if value is not None
    }
    raw_support_files = spec.get("support_files", [])
    if not isinstance(raw_support_files, list):
        raise ValueError(f"{spec_id}.support_files must be a JSON array.")
    support_files = tuple(
        _require_repository_path(value, f"{spec_id}.support_files") for value in raw_support_files
    )
    if len(support_files) != len(set(support_files)):
        raise ValueError(f"{spec_id}.support_files must not contain duplicates.")

    raw_params = spec.get("expected_params")
    if not isinstance(raw_params, list) or not raw_params:
        raise ValueError(f"{spec_id}.expected_params must be a non-empty JSON array.")
    expected_params = tuple(
        _require_nonempty_string(value, f"{spec_id}.expected_params") for value in raw_params
    )
    if len(expected_params) != len(set(expected_params)):
        raise ValueError(f"{spec_id}.expected_params must not contain duplicates.")

    counts = {
        field: _require_positive_integer(spec.get(field), f"{spec_id}.{field}")
        for field in _POSITIVE_INTEGER_FIELDS
    }
    max_rel_se_diff = _require_positive_number(
        spec.get("max_rel_se_diff", default_se_tolerance), f"{spec_id}.max_rel_se_diff"
    )
    transformation = _require_nonempty_string(
        spec.get("transformation"), f"{spec_id}.transformation"
    ).lower()
    if transformation not in {"fd", "fod"}:
        raise ValueError(f"{spec_id}.transformation must be 'fd' or 'fod'.")
    requires_level_iv = spec.get("requires_level_iv")
    if not isinstance(requires_level_iv, bool):
        raise ValueError(f"{spec_id}.requires_level_iv must be a boolean.")

    config = SpecConfig(
        data=paths["data"],
        do_file=paths["do_file"],
        builder=paths["builder"],
        runner=paths["runner"],
        native_params=paths["native_params"],
        native_diagnostics=paths["native_diagnostics"],
        stata_params=paths["stata_params"],
        stata_diagnostics=paths["stata_diagnostics"],
        expected_params=frozenset(expected_params),
        expected_nobs=counts["expected_nobs"],
        expected_n_groups=counts["expected_n_groups"],
        expected_instruments=counts["expected_instruments"],
        expected_df=counts["expected_df"],
        max_rel_se_diff=max_rel_se_diff,
        transformation=transformation,
        requires_level_iv=requires_level_iv,
    )
    if sample_paths:
        config["native_sample"] = sample_paths["native_sample"]
        config["stata_sample"] = sample_paths["stata_sample"]
    if support_files:
        config["support_files"] = support_files
    return spec_id, config


def load_certification_registry(path: Path = REGISTRY_PATH) -> CertificationRegistry:
    raw = _require_mapping(json.loads(path.read_text(encoding="utf-8")), "registry")

    schema_version = raw.get("schema_version")
    if schema_version != 1:
        raise ValueError(f"Unsupported certification registry schema: {schema_version!r}")

    oracle = _require_nonempty_string(raw.get("oracle"), "oracle")
    stata_syntax_version = _require_nonempty_string(
        raw.get("stata_syntax_version"), "stata_syntax_version"
    )
    expected_stata_version = _require_positive_number(
        raw.get("expected_stata_version"), "expected_stata_version"
    )
    expected_xtabond2_e_version = _require_nonempty_string(
        raw.get("expected_xtabond2_e_version"), "expected_xtabond2_e_version"
    )
    expected_xtabond2_ado_header = _require_nonempty_string(
        raw.get("expected_xtabond2_ado_header"), "expected_xtabond2_ado_header"
    )
    if not expected_xtabond2_ado_header.startswith("*! xtabond2 "):
        raise ValueError("expected_xtabond2_ado_header must be the non-path ado header line.")
    comparator_provenance = _require_repository_path(
        raw.get("comparator_provenance"), "comparator_provenance"
    )
    text_digest_algorithm = _require_nonempty_string(
        raw.get("text_digest_algorithm"), "text_digest_algorithm"
    )
    if text_digest_algorithm != "sha256-lf-v1":
        raise ValueError(f"Unsupported text digest algorithm: {text_digest_algorithm!r}")

    raw_tolerances = _require_mapping(raw.get("tolerances"), "tolerances")
    tolerance_values = {
        field: _require_positive_number(raw_tolerances.get(field), f"tolerances.{field}")
        for field in _POSITIVE_TOLERANCE_FIELDS
    }
    tolerances = CertificationTolerances(**tolerance_values)

    raw_specs = raw.get("specifications")
    if not isinstance(raw_specs, list) or not raw_specs:
        raise ValueError("specifications must be a non-empty JSON array.")

    specifications: dict[str, SpecConfig] = {}
    for index, raw_spec in enumerate(raw_specs):
        spec_id, config = _load_spec(
            raw_spec,
            index,
            tolerances.windmeijer_standard_error_relative_default,
        )
        if spec_id in specifications:
            raise ValueError(f"Duplicate certification specification ID: {spec_id}")
        specifications[spec_id] = config

    return CertificationRegistry(
        schema_version=schema_version,
        oracle=oracle,
        stata_syntax_version=stata_syntax_version,
        expected_stata_version=expected_stata_version,
        expected_xtabond2_e_version=expected_xtabond2_e_version,
        expected_xtabond2_ado_header=expected_xtabond2_ado_header,
        comparator_provenance=comparator_provenance,
        text_digest_algorithm=text_digest_algorithm,
        tolerances=tolerances,
        specifications=specifications,
    )


def repository_path(path: Path) -> Path:
    return REPOSITORY_ROOT / path


def canonical_text_sha256(path: Path) -> str:
    content = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(content).hexdigest()


def certification_registry_sha256(path: Path = REGISTRY_PATH) -> str:
    return canonical_text_sha256(path)


def load_comparator_provenance(
    registry: CertificationRegistry | None = None,
) -> ComparatorProvenance:
    registry = registry or load_certification_registry()
    path = repository_path(registry.comparator_provenance)
    raw = _require_mapping(json.loads(path.read_text(encoding="utf-8")), "provenance")

    schema_version = raw.get("schema_version")
    if schema_version != 1:
        raise ValueError(f"Unsupported comparator provenance schema: {schema_version!r}")
    text_digest_algorithm = _require_nonempty_string(
        raw.get("text_digest_algorithm"), "provenance.text_digest_algorithm"
    )
    if text_digest_algorithm != registry.text_digest_algorithm:
        raise ValueError("Comparator provenance and registry digest algorithms differ.")
    registry_path = _require_repository_path(raw.get("registry_path"), "provenance.registry_path")
    if repository_path(registry_path) != REGISTRY_PATH:
        raise ValueError("Comparator provenance points to a different certification registry.")
    registry_sha256 = _require_sha256(raw.get("registry_sha256"), "provenance.registry_sha256")
    if registry_sha256 != certification_registry_sha256(REGISTRY_PATH):
        raise ValueError("Comparator provenance registry hash is stale.")
    generator = _require_repository_path(raw.get("generator"), "provenance.generator")
    if not repository_path(generator).is_file():
        raise ValueError("Comparator provenance generator does not exist.")
    generator_sha256 = _require_sha256(raw.get("generator_sha256"), "provenance.generator_sha256")
    if generator_sha256 != canonical_text_sha256(repository_path(generator)):
        raise ValueError("Comparator provenance generator hash is stale.")
    source_log_committed = raw.get("source_log_committed")
    if source_log_committed is not False:
        raise ValueError("Historical source log must be declared uncommitted.")

    raw_specifications = raw.get("certified_specifications")
    if not isinstance(raw_specifications, list) or not raw_specifications:
        raise ValueError("provenance.certified_specifications must be a non-empty array.")
    certified_specifications = tuple(
        _require_nonempty_string(value, "provenance.certified_specifications")
        for value in raw_specifications
    )
    if certified_specifications != tuple(registry.specifications):
        raise ValueError("Comparator provenance specification order differs from the registry.")

    raw_output_hashes = _require_mapping(raw.get("output_hashes"), "provenance.output_hashes")
    if set(raw_output_hashes) != set(registry.specifications):
        raise ValueError("Comparator provenance output hashes do not cover the registry exactly.")
    output_hashes: dict[str, StataOutputHashes] = {}
    for spec_id in certified_specifications:
        config = registry.specifications[spec_id]
        hashes = _require_mapping(raw_output_hashes.get(spec_id), f"output_hashes.{spec_id}")
        expected_hash_fields = {"stata_params_sha256", "stata_diagnostics_sha256"}
        if "stata_sample" in config:
            expected_hash_fields.add("stata_sample_sha256")
        if set(hashes) != expected_hash_fields:
            raise ValueError(f"output_hashes.{spec_id} has unexpected fields.")
        output_hashes[spec_id] = StataOutputHashes(
            stata_params_sha256=_require_sha256(
                hashes.get("stata_params_sha256"),
                f"output_hashes.{spec_id}.stata_params_sha256",
            ),
            stata_diagnostics_sha256=_require_sha256(
                hashes.get("stata_diagnostics_sha256"),
                f"output_hashes.{spec_id}.stata_diagnostics_sha256",
            ),
        )
        if "stata_sample" in config:
            output_hashes[spec_id]["stata_sample_sha256"] = _require_sha256(
                hashes.get("stata_sample_sha256"),
                f"output_hashes.{spec_id}.stata_sample_sha256",
            )

    stata_version = _require_positive_number(raw.get("stata_version"), "provenance.stata_version")
    xtabond2_e_version = _require_nonempty_string(
        raw.get("xtabond2_e_version"), "provenance.xtabond2_e_version"
    )
    xtabond2_ado_header = _require_nonempty_string(
        raw.get("xtabond2_ado_header"), "provenance.xtabond2_ado_header"
    )
    if stata_version != registry.expected_stata_version:
        raise ValueError("Comparator provenance Stata version differs from the registry.")
    if xtabond2_e_version != registry.expected_xtabond2_e_version:
        raise ValueError("Comparator provenance e(version) differs from the registry.")
    if xtabond2_ado_header != registry.expected_xtabond2_ado_header:
        raise ValueError("Comparator provenance ado header differs from the registry.")

    attestation_kind = _require_nonempty_string(
        raw.get("attestation_kind"), "provenance.attestation_kind"
    )
    if attestation_kind != HISTORICAL_ATTESTATION_KIND:
        raise ValueError(f"Unsupported comparator attestation kind: {attestation_kind!r}")
    capture_method = _require_nonempty_string(
        raw.get("capture_method"), "provenance.capture_method"
    )
    if capture_method != HISTORICAL_CAPTURE_METHOD:
        raise ValueError(f"Unsupported comparator capture method: {capture_method!r}")

    return ComparatorProvenance(
        schema_version=schema_version,
        attestation_kind=attestation_kind,
        capture_method=capture_method,
        text_digest_algorithm=text_digest_algorithm,
        registry_path=registry_path,
        registry_sha256=registry_sha256,
        generator=generator,
        generator_sha256=generator_sha256,
        run_log_sha256=_require_sha256(raw.get("run_log_sha256"), "provenance.run_log_sha256"),
        source_log_committed=source_log_committed,
        source_binding_limitation=_require_nonempty_string(
            raw.get("source_binding_limitation"), "provenance.source_binding_limitation"
        ),
        stata_version=stata_version,
        stata_flavor=_require_nonempty_string(raw.get("stata_flavor"), "provenance.stata_flavor"),
        stata_os=_require_nonempty_string(raw.get("stata_os"), "provenance.stata_os"),
        stata_machine_type=_require_nonempty_string(
            raw.get("stata_machine_type"), "provenance.stata_machine_type"
        ),
        stata_reported_start=_require_nonempty_string(
            raw.get("stata_reported_start"), "provenance.stata_reported_start"
        ),
        stata_reported_end=_require_nonempty_string(
            raw.get("stata_reported_end"), "provenance.stata_reported_end"
        ),
        xtabond2_e_version=xtabond2_e_version,
        xtabond2_ado_header=xtabond2_ado_header,
        xtabond2_ado_sha256=_require_sha256(
            raw.get("xtabond2_ado_sha256"), "provenance.xtabond2_ado_sha256"
        ),
        xtabond2_ado_hash_observation=_require_nonempty_string(
            raw.get("xtabond2_ado_hash_observation"),
            "provenance.xtabond2_ado_hash_observation",
        ),
        certified_specifications=certified_specifications,
        output_hashes=output_hashes,
    )


def comparator_provenance_sha256(
    registry: CertificationRegistry | None = None,
) -> str:
    registry = registry or load_certification_registry()
    return canonical_text_sha256(repository_path(registry.comparator_provenance))
