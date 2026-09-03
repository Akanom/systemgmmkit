from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from systemgmmkit import DynamicPanelSpec, GMMStyle, IVStyle
from systemgmmkit.native_gmm import (
    _native_fd_difference_windmeijer_covariance,
    run_native_dynamic_panel_gmm,
)

ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = (
    ROOT / "artifacts" / "parity" / "xtabond2" / "difference_gmm_fd" / "xtabond2_reference_v1.json"
)
REFERENCE = json.loads(REFERENCE_PATH.read_text(encoding="utf-8"))

DATA_PATHS = {
    "paired-fd-balanced-xtabond2": (
        ROOT / "artifacts" / "parity" / "xtabond2" / "system_gmm_benchmark.csv"
    ),
    "paired-fd-unbalanced-xtabond2": (
        ROOT
        / "artifacts"
        / "parity"
        / "xtabond2"
        / "specs"
        / "system_gmm_unbalanced_panel"
        / "fixture.csv"
    ),
    "paired-fd-variable-missing-xtabond2": (
        ROOT
        / "artifacts"
        / "parity"
        / "xtabond2"
        / "specs"
        / "system_gmm_variable_missing"
        / "fixture.csv"
    ),
}

EXPECTED_TOLERANCES = {
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


def _spec(*, name: str) -> DynamicPanelSpec:
    return DynamicPanelSpec(
        dependent="y",
        regressors=["L1.y", "x", "w"],
        gmm=[
            GMMStyle(variable="L1.y", min_lag=2, max_lag=3),
            GMMStyle(variable="x", min_lag=2, max_lag=3),
        ],
        iv=[IVStyle(variable="w", eq="diff")],
        time_dummies=False,
        system=False,
        collapse=True,
        transformation="fd",
        steps="twostep",
        name=name,
    )


def _independent_h_weight(
    *, Z: np.ndarray, row_meta: list[dict[str, object]], groups: list[np.ndarray]
) -> np.ndarray:
    covariance = np.zeros((Z.shape[1], Z.shape[1]), dtype=float)
    for indices in groups:
        Zi = Z[indices, :]
        errors = [row_meta[int(index)]["error_terms"] for index in indices]
        H = np.zeros((len(indices), len(indices)), dtype=float)
        for left, left_terms in enumerate(errors):
            assert isinstance(left_terms, dict)
            for right, right_terms in enumerate(errors):
                assert isinstance(right_terms, dict)
                H[left, right] = sum(
                    float(coefficient) * float(right_terms.get(term, 0.0))
                    for term, coefficient in left_terms.items()
                )
        covariance += Zi.T @ H @ Zi
    return np.linalg.pinv(covariance)


def _sample_key_sha256(frame: pd.DataFrame) -> str:
    keys = [
        [int(entity), int(time)]
        for entity, time in frame.loc[:, ["id", "t"]]
        .sort_values(["id", "t"])
        .itertuples(index=False, name=None)
    ]
    payload = json.dumps(keys, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _canonical_text_sha256(path: Path) -> str:
    payload = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(payload).hexdigest()


@pytest.mark.parity
@pytest.mark.parametrize("fixture_id", tuple(DATA_PATHS))
def test_fd_difference_gmm_matches_fixed_xtabond2_surfaces(
    fixture_id: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert REFERENCE["absolute_tolerances"] == EXPECTED_TOLERANCES
    expected = REFERENCE["fixtures"][fixture_id]
    data_path = DATA_PATHS[fixture_id]
    assert _canonical_text_sha256(data_path) == expected["data_canonical_sha256"]

    monkeypatch.setenv("SYSTEMGMMKIT_NATIVE_DIAGNOSTIC_DUMP_DIR", str(tmp_path))
    result = run_native_dynamic_panel_gmm(
        _spec(name=fixture_id),
        pd.read_csv(data_path),
        entity="id",
        time="t",
        windmeijer=True,
    )

    dump_dir = tmp_path / fixture_id
    with np.load(dump_dir / "matrices.npz") as dump:
        y = dump["y"].copy()
        X = dump["X"].copy()
        Z = dump["Z"].copy()
        W1 = dump["W1"].copy()
        W2 = dump["W_final"].copy()
        residuals1 = dump["residuals_step1"].copy()
        residuals2 = dump["residuals_final"].copy()
        bread2 = dump["bread"].copy()

    native_order = tuple(
        (dump_dir / "instrument_names.txt").read_text(encoding="utf-8").splitlines()
    )
    native_sample = pd.read_csv(dump_dir / "row_index.csv")
    stata_order = tuple(REFERENCE["stata_moment_order"])
    assert set(native_order) == set(stata_order)
    permutation = [native_order.index(name) for name in stata_order]

    native_b = result.params.to_numpy(dtype=float)
    native_v = result.covariance.to_numpy(dtype=float)
    native_a2 = W2[np.ix_(permutation, permutation)]
    native_ze = (Z.T @ residuals2).reshape(-1)[permutation]

    assert np.max(np.abs(native_b - np.asarray(expected["parameters"]))) <= 2e-7
    assert np.max(np.abs(native_v - np.asarray(expected["covariance"]))) <= 5e-8
    assert np.max(np.abs(native_a2 - np.asarray(expected["criterion_weighting_matrix"]))) <= 2e-9
    assert np.max(np.abs(native_ze - np.asarray(expected["summed_residual_moment"]))) <= 2e-5
    assert abs(float(result.hansen_j_stat) - float(expected["hansen_j"])) <= 1e-6
    assert abs(float(result.hansen_p) - float(expected["hansen_p"])) <= 2e-7
    assert abs(float(result.sargan_j_stat) - float(expected["sargan_j"])) <= 2e-6
    assert abs(float(result.sargan_p) - float(expected["sargan_p"])) <= 3e-7
    assert abs(float(result.ar1_z) - float(expected["ar1_z"])) <= 2e-6
    assert abs(float(result.ar1_p) - float(expected["ar1_p"])) <= 2e-7
    assert abs(float(result.ar2_z) - float(expected["ar2_z"])) <= 2e-6
    assert abs(float(result.ar2_p) - float(expected["ar2_p"])) <= 2e-7
    assert result.overid_df == expected["hansen_df"]
    assert result.nobs == expected["nobs"]
    assert result.n_groups == expected["n_groups"]
    assert result.n_instruments == expected["n_instruments"]
    assert list(result.params.index) == ["L1.y", "x", "w"]
    assert _sample_key_sha256(native_sample) == expected["sample_key_sha256"]

    # Regression guard for the original bug: W1 must use Z'HZ, not Z'Z.
    groups = [
        np.asarray(indices, dtype=int)
        for indices in json.loads((dump_dir / "group_indices.json").read_text(encoding="utf-8"))
    ]
    row_meta = json.loads((dump_dir / "row_meta.json").read_text(encoding="utf-8"))
    expected_w1 = _independent_h_weight(Z=Z, row_meta=row_meta, groups=groups)
    np.testing.assert_allclose(W1, expected_w1, rtol=1e-12, atol=1e-12)
    assert np.max(np.abs(W1 - np.linalg.pinv(Z.T @ Z))) > 1e-7

    # The two-step Hansen statistic must use A2 estimated from first-step residuals.
    native_ze_unpermuted = Z.T @ residuals2
    reconstructed_j = float((native_ze_unpermuted.T @ W2 @ native_ze_unpermuted).squeeze())
    assert float(result.hansen_j_stat) == pytest.approx(reconstructed_j, abs=1e-12)

    # The Sargan diagnostic uses first-step residuals and the FD residual
    # variance normalization in xtabond2 3.7.2.
    zte1 = Z.T @ residuals1
    sigma2_step1 = float((residuals1.T @ residuals1).squeeze()) / (2.0 * len(residuals1))
    reconstructed_sargan = float((zte1.T @ W1 @ zte1).squeeze()) / sigma2_step1
    assert float(result.sargan_j_stat) == pytest.approx(reconstructed_sargan, abs=1e-12)

    # The public covariance must be the dedicated FD formula plus xtabond2's
    # registered ``small`` correction, and remain finite and symmetric.
    unscaled_v = _native_fd_difference_windmeijer_covariance(
        X=X,
        Z=Z,
        W1=W1,
        W2=W2,
        bread2=bread2,
        residuals1=residuals1,
        residuals2=residuals2,
        group_indices=groups,
    )
    small = (len(groups) / (len(groups) - 1.0)) * ((len(y) - 1.0) / (len(y) - X.shape[1]))
    np.testing.assert_allclose(native_v, small * unscaled_v, rtol=1e-12, atol=1e-12)
    np.testing.assert_allclose(native_v, native_v.T, rtol=0.0, atol=1e-14)
    assert np.isfinite(native_v).all()


def test_fd_difference_windmeijer_rejects_empty_entity_partition() -> None:
    with pytest.raises(ValueError, match="at least one entity block"):
        _native_fd_difference_windmeijer_covariance(
            X=np.ones((2, 1)),
            Z=np.ones((2, 1)),
            W1=np.ones((1, 1)),
            W2=np.ones((1, 1)),
            bread2=np.ones((1, 1)),
            residuals1=np.ones((2, 1)),
            residuals2=np.ones((2, 1)),
            group_indices=[],
        )


@pytest.mark.parametrize(
    ("groups", "message"),
    [
        ([np.array([], dtype=int), np.array([0, 1])], "empty entity block"),
        ([np.array([0]), np.array([0])], "every stacked row exactly once"),
        ([np.array([0]), np.array([2])], "every stacked row exactly once"),
    ],
)
def test_fd_difference_windmeijer_rejects_invalid_entity_partition(
    groups: list[np.ndarray], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        _native_fd_difference_windmeijer_covariance(
            X=np.ones((2, 1)),
            Z=np.ones((2, 1)),
            W1=np.ones((1, 1)),
            W2=np.ones((1, 1)),
            bread2=np.ones((1, 1)),
            residuals1=np.ones((2, 1)),
            residuals2=np.ones((2, 1)),
            group_indices=groups,
        )


def test_fd_difference_windmeijer_rejects_nonfinite_input() -> None:
    with pytest.raises(ValueError, match="must all be finite"):
        _native_fd_difference_windmeijer_covariance(
            X=np.array([[1.0], [np.nan]]),
            Z=np.ones((2, 1)),
            W1=np.ones((1, 1)),
            W2=np.ones((1, 1)),
            bread2=np.ones((1, 1)),
            residuals1=np.ones((2, 1)),
            residuals2=np.ones((2, 1)),
            group_indices=[np.array([0]), np.array([1])],
        )
