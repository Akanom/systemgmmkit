"""Compare native FD Difference GMM with fixed xtabond2 matrix exports."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

SCRIPT_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_SOURCE_ROOT = SCRIPT_REPOSITORY_ROOT / "src"

FIXTURES = (
    (
        "paired-fd-balanced-xtabond2",
        "artifacts/parity/xtabond2/system_gmm_benchmark.csv",
    ),
    (
        "paired-fd-unbalanced-xtabond2",
        "artifacts/parity/xtabond2/specs/system_gmm_unbalanced_panel/fixture.csv",
    ),
    (
        "paired-fd-variable-missing-xtabond2",
        "artifacts/parity/xtabond2/specs/system_gmm_variable_missing/fixture.csv",
    ),
)

STATA_MOMENT_ORDER = (
    "D:iv:w",
    "D:L1.y:L2",
    "D:x:L2",
    "D:L1.y:L3",
    "D:x:L3",
)

ABSOLUTE_TOLERANCES = {
    "coefficient": 2e-7,
    "covariance": 5e-8,
    "criterion_weighting_matrix": 2e-9,
    "summed_residual_moment": 2e-5,
    "hansen_j": 1e-6,
    "hansen_p": 2e-7,
    "sargan_j": 2e-6,
    "sargan_p": 3e-7,
    "ar_z": 2e-6,
    "ar_p": 2e-7,
}

TOLERANCE_KEYS = {
    "coefficient": "coefficient",
    "covariance": "covariance",
    "criterion_weighting_matrix": "criterion_weighting_matrix",
    "summed_residual_moment": "summed_residual_moment",
    "hansen_j": "hansen_j",
    "hansen_p": "hansen_p",
    "sargan_j": "sargan_j",
    "sargan_p": "sargan_p",
    "ar1_z": "ar_z",
    "ar1_p": "ar_p",
    "ar2_z": "ar_z",
    "ar2_p": "ar_p",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sample_keys(frame: pd.DataFrame) -> list[list[int]]:
    return [
        [int(entity), int(time)]
        for entity, time in frame.loc[:, ["id", "t"]]
        .sort_values(["id", "t"])
        .itertuples(index=False, name=None)
    ]


def _sample_key_sha256(keys: list[list[int]]) -> str:
    return hashlib.sha256(json.dumps(keys, separators=(",", ":")).encode("utf-8")).hexdigest()


def _numeric_matrix(path: Path) -> np.ndarray:
    frame = pd.read_csv(path).apply(pd.to_numeric, errors="coerce")
    frame = frame.dropna(axis=1, how="all").dropna(axis=0, how="all")
    matrix = frame.to_numpy(dtype=float)
    if matrix.size == 0 or not np.isfinite(matrix).all():
        raise ValueError(f"Stata matrix is empty or nonfinite: {path}")
    return matrix


def _load_source_bound_provider() -> tuple[Any, Any]:
    if str(SCRIPT_SOURCE_ROOT) not in sys.path:
        sys.path.insert(0, str(SCRIPT_SOURCE_ROOT))
    package = importlib.import_module("systemgmmkit")
    package_path = Path(package.__file__).resolve()
    try:
        package_path.relative_to(SCRIPT_SOURCE_ROOT)
    except ValueError as exc:
        raise RuntimeError(
            f"Comparator imported {package_path}, outside source root {SCRIPT_SOURCE_ROOT}."
        ) from exc
    native_module = importlib.import_module("systemgmmkit.native_gmm")
    return package, native_module.run_native_dynamic_panel_gmm


def _load_installed_provider(*, expected_version: str) -> tuple[Any, Any]:
    package = importlib.import_module("systemgmmkit")
    package_path = Path(package.__file__).resolve()
    try:
        package_path.relative_to(SCRIPT_SOURCE_ROOT)
    except ValueError:
        pass
    else:
        raise RuntimeError(
            "Installed-provider comparison imported the checkout source instead of a distribution."
        )
    if package.__version__ != expected_version:
        raise RuntimeError(
            f"Installed provider version is {package.__version__!r}; expected {expected_version!r}."
        )
    native_module = importlib.import_module("systemgmmkit.native_gmm")
    return package, native_module.run_native_dynamic_panel_gmm


def _difference_spec(*, provider: Any, name: str = "difference_gmm_xtabond2_parity") -> Any:
    return provider.DynamicPanelSpec(
        dependent="y",
        regressors=["L1.y", "x", "w"],
        gmm=[
            provider.GMMStyle(variable="L1.y", min_lag=2, max_lag=3),
            provider.GMMStyle(variable="x", min_lag=2, max_lag=3),
        ],
        iv=[provider.IVStyle(variable="w", eq="diff")],
        time_dummies=False,
        system=False,
        collapse=True,
        transformation="fd",
        steps="twostep",
        name=name,
    )


def compare(
    *, repository_root: Path, stata_root: Path, provider_mode: str = "source"
) -> list[dict[str, Any]]:
    repository_root = repository_root.resolve()
    if repository_root != SCRIPT_REPOSITORY_ROOT:
        raise ValueError(
            f"The comparator is source-bound to its containing repository: {SCRIPT_REPOSITORY_ROOT}"
        )
    reference = json.loads(
        (
            repository_root
            / "artifacts"
            / "parity"
            / "xtabond2"
            / "difference_gmm_fd"
            / "xtabond2_reference_v1.json"
        ).read_text(encoding="utf-8")
    )
    if reference["absolute_tolerances"] != ABSOLUTE_TOLERANCES:
        raise ValueError("The comparator tolerances differ from the fixed reference artifact.")
    if provider_mode == "source":
        provider, run_native_dynamic_panel_gmm = _load_source_bound_provider()
    elif provider_mode == "installed":
        provider, run_native_dynamic_panel_gmm = _load_installed_provider(
            expected_version=reference["provider_version"]
        )
    else:
        raise ValueError("provider_mode must be 'source' or 'installed'.")
    provider_module_path = Path(provider.__file__).resolve()
    if provider_mode == "source":
        provider_location = provider_module_path.relative_to(repository_root).as_posix()
    else:
        provider_location = "site-packages/systemgmmkit/__init__.py"

    rows: list[dict[str, Any]] = []
    previous_dump_root = os.environ.get("SYSTEMGMMKIT_NATIVE_DIAGNOSTIC_DUMP_DIR")
    try:
        with tempfile.TemporaryDirectory(prefix="systemgmmkit-fd-parity-") as temporary:
            os.environ["SYSTEMGMMKIT_NATIVE_DIAGNOSTIC_DUMP_DIR"] = temporary
            for fixture_id, relative_data_path in FIXTURES:
                expected = reference["fixtures"][fixture_id]
                data_path = repository_root / relative_data_path
                if _sha256(data_path) != expected["data_sha256"]:
                    raise ValueError(f"Input fixture hash differs for {fixture_id}.")

                result = run_native_dynamic_panel_gmm(
                    _difference_spec(provider=provider, name=fixture_id),
                    pd.read_csv(data_path),
                    entity="id",
                    time="t",
                    windmeijer=True,
                )
                oracle_dir = stata_root / fixture_id
                source_paths = {
                    "b": oracle_dir / "difference_b.csv",
                    "V": oracle_dir / "difference_V.csv",
                    "A2": oracle_dir / "difference_A2.csv",
                    "Ze": oracle_dir / "difference_Ze.csv",
                    "diagnostics": oracle_dir / "difference_diagnostics.csv",
                    "sample": oracle_dir / "difference_sample.csv",
                }
                for source_name, source_path in source_paths.items():
                    if _sha256(source_path) != expected["source_csv_sha256"][source_name]:
                        raise ValueError(
                            f"Stata {source_name} source hash differs for {fixture_id}."
                        )

                stata_b = _numeric_matrix(source_paths["b"]).reshape(-1)
                stata_v = _numeric_matrix(source_paths["V"])
                stata_a2 = _numeric_matrix(source_paths["A2"])
                stata_ze = _numeric_matrix(source_paths["Ze"]).reshape(-1)
                diagnostics = pd.read_csv(source_paths["diagnostics"]).iloc[0]
                stata_sample_frame = pd.read_csv(source_paths["sample"])
                stata_sample = _sample_keys(
                    stata_sample_frame.loc[stata_sample_frame["e_sample"].astype(int) == 1]
                )
                if _sample_key_sha256(stata_sample) != expected["sample_key_sha256"]:
                    raise ValueError(f"Stata sample-key digest differs for {fixture_id}.")

                dump_dir = Path(temporary) / fixture_id
                native_moment_order = tuple(
                    (dump_dir / "instrument_names.txt").read_text(encoding="utf-8").splitlines()
                )
                native_sample = _sample_keys(pd.read_csv(dump_dir / "row_index.csv"))
                if set(native_moment_order) != set(STATA_MOMENT_ORDER):
                    raise ValueError(
                        f"Moment identities differ for {fixture_id}: {native_moment_order!r}"
                    )
                permutation = [native_moment_order.index(name) for name in STATA_MOMENT_ORDER]
                with np.load(dump_dir / "matrices.npz") as matrices:
                    native_a2 = matrices["W_final"][np.ix_(permutation, permutation)]
                    native_ze = (matrices["Z"].T @ matrices["residuals_final"]).reshape(-1)[
                        permutation
                    ]
                native_b = result.params.to_numpy(dtype=float)
                native_v = result.covariance.to_numpy(dtype=float)

                differences = {
                    "coefficient": float(np.max(np.abs(native_b - stata_b))),
                    "covariance": float(np.max(np.abs(native_v - stata_v))),
                    "criterion_weighting_matrix": float(np.max(np.abs(native_a2 - stata_a2))),
                    "summed_residual_moment": float(np.max(np.abs(native_ze - stata_ze))),
                    "hansen_j": abs(float(result.hansen_j_stat) - float(diagnostics["hansen_j"])),
                    "hansen_p": abs(float(result.hansen_p) - float(diagnostics["hansen_p"])),
                    "sargan_j": abs(float(result.sargan_j_stat) - float(diagnostics["sargan_j"])),
                    "sargan_p": abs(float(result.sargan_p) - float(diagnostics["sargan_p"])),
                    "ar1_z": abs(float(result.ar1_z) - float(diagnostics["ar1_z"])),
                    "ar1_p": abs(float(result.ar1_p) - float(diagnostics["ar1_p"])),
                    "ar2_z": abs(float(result.ar2_z) - float(diagnostics["ar2_z"])),
                    "ar2_p": abs(float(result.ar2_p) - float(diagnostics["ar2_p"])),
                }
                within_tolerance = {
                    name: value <= ABSOLUTE_TOLERANCES[TOLERANCE_KEYS[name]]
                    for name, value in differences.items()
                }
                count_identity_exact = (
                    result.nobs == int(diagnostics["nobs"])
                    and result.n_groups == int(diagnostics["n_groups"])
                    and result.n_instruments == int(diagnostics["n_instruments"])
                    and result.overid_df == int(diagnostics["hansen_df"])
                )
                sample_identity_exact = native_sample == stata_sample
                parameter_identity_exact = list(result.params.index) == ["L1.y", "x", "w"]
                rows.append(
                    {
                        "fixture_id": fixture_id,
                        "provider_mode": provider_mode,
                        "provider_version": provider.__version__,
                        "provider_location": provider_location,
                        "maximum_absolute_differences": differences,
                        "within_tolerance": within_tolerance,
                        "parity_passed": (
                            all(within_tolerance.values())
                            and count_identity_exact
                            and sample_identity_exact
                            and parameter_identity_exact
                        ),
                        "tolerances": dict(ABSOLUTE_TOLERANCES),
                        "moment_identity_exact": True,
                        "sample_identity_exact": sample_identity_exact,
                        "count_identity_exact": count_identity_exact,
                        "parameter_identity_exact": parameter_identity_exact,
                        "sample_key_sha256": _sample_key_sha256(native_sample),
                        "provider_native_moment_order": list(native_moment_order),
                        "stata_moment_order": list(STATA_MOMENT_ORDER),
                        "provider_to_stata_permutation": permutation,
                        "native_hansen_j": float(result.hansen_j_stat),
                        "stata_hansen_j": float(diagnostics["hansen_j"]),
                        "native_parameters": native_b.tolist(),
                        "stata_parameters": stata_b.tolist(),
                        "native_covariance": native_v.tolist(),
                        "stata_covariance": stata_v.tolist(),
                    }
                )
    finally:
        if previous_dump_root is None:
            os.environ.pop("SYSTEMGMMKIT_NATIVE_DIAGNOSTIC_DUMP_DIR", None)
        else:
            os.environ["SYSTEMGMMKIT_NATIVE_DIAGNOSTIC_DUMP_DIR"] = previous_dump_root
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--repository-root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
    )
    parser.add_argument("--stata-root", type=Path, required=True)
    parser.add_argument("--provider-mode", choices=("source", "installed"), default="source")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    rows = compare(
        repository_root=args.repository_root.resolve(),
        stata_root=args.stata_root.resolve(),
        provider_mode=args.provider_mode,
    )
    payload = json.dumps(rows, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        output_path = args.output.resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(payload, encoding="utf-8")
    print(payload, end="")


if __name__ == "__main__":
    main()
