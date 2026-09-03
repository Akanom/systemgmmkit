from __future__ import annotations

from pathlib import Path

import pytest

from scripts.parity import compare_fd_difference_gmm_to_xtabond2 as comparator


def test_comparator_loads_provider_from_its_bound_source_tree() -> None:
    provider, runner = comparator._load_source_bound_provider()
    provider_path = Path(provider.__file__).resolve()
    provider_path.relative_to(comparator.SCRIPT_SOURCE_ROOT)
    assert callable(runner)
    assert provider.__version__ == "1.0.5"


def test_comparator_rejects_a_different_repository_root(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="source-bound"):
        comparator.compare(repository_root=tmp_path, stata_root=tmp_path)


def test_sample_key_digest_is_order_invariant() -> None:
    forward = [[1, 2], [1, 3], [2, 2]]
    reverse = list(reversed(forward))
    assert comparator._sample_key_sha256(sorted(forward)) == comparator._sample_key_sha256(
        sorted(reverse)
    )
