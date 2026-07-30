from __future__ import annotations

import runpy
from pathlib import Path

import systemgmmkit

ROOT = Path(__file__).resolve().parents[1]


def test_native_gmm_benchmark_distinguishes_source_and_installed_versions() -> None:
    namespace = runpy.run_path(str(ROOT / "benchmarks" / "benchmark_native_gmm.py"))

    environment = namespace["_environment"]()

    assert environment["systemgmmkit"] == systemgmmkit.__version__
    assert environment["systemgmmkit_source"] == systemgmmkit.__version__
    assert "systemgmmkit_installed_distribution" in environment
