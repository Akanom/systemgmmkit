"""Reproducible native dynamic-panel GMM performance benchmark.

Run from the repository root after installing the project in an isolated environment.
The benchmark keeps data generation outside timed regions and reports cold fit time,
warm fit time, and Python allocation peaks separately.
"""

from __future__ import annotations

import argparse
import cProfile
import gc
import importlib.metadata
import io
import json
import os
import platform
import pstats
import statistics
import sys
import time
import tracemalloc
from contextlib import redirect_stdout
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import scipy

import systemgmmkit
from systemgmmkit import DynamicPanelSpec, GMMStyle, IVStyle, run_native_dynamic_panel_gmm


@dataclass(frozen=True)
class BenchmarkCase:
    name: str
    n_entities: int
    n_periods: int
    transformation: str
    system: bool
    max_lag: int
    steps: str = "twostep"
    collapse: bool = True
    windmeijer: bool = False
    gap_fraction: float = 0.0
    unsorted: bool = False


QUICK_CASES = (
    BenchmarkCase("small_difference_fd_onestep", 24, 10, "fd", False, 3, steps="onestep"),
    BenchmarkCase("small_unbalanced_difference_fd", 28, 11, "fd", False, 3, gap_fraction=0.08),
    BenchmarkCase("medium_system_fd_twostep", 60, 12, "fd", True, 4),
    BenchmarkCase(
        "gapped_unsorted_system_fod_windmeijer",
        48,
        12,
        "fod",
        True,
        4,
        windmeijer=True,
        gap_fraction=0.08,
        unsorted=True,
    ),
)
FULL_CASES = QUICK_CASES + (
    BenchmarkCase("uncollapsed_difference_fd", 40, 12, "fd", False, 4, collapse=False),
    BenchmarkCase("instrument_heavy_system_fd", 48, 18, "fd", True, 7),
    BenchmarkCase("large_n_short_t_system_fd", 180, 10, "fd", True, 4),
    BenchmarkCase("large_t_difference_fod", 60, 24, "fod", False, 8, gap_fraction=0.04),
    BenchmarkCase("related_system_lag_2", 60, 12, "fd", True, 2),
    BenchmarkCase("related_system_lag_3", 60, 12, "fd", True, 3),
    BenchmarkCase("related_system_lag_4", 60, 12, "fd", True, 4),
)


def _panel(case: BenchmarkCase) -> pd.DataFrame:
    rng = np.random.default_rng(20260728)
    rows: list[dict[str, float | int]] = []
    entity_effects = rng.normal(scale=0.45, size=case.n_entities)
    for entity in range(case.n_entities):
        previous = float(rng.normal())
        for period in range(case.n_periods):
            x = float(rng.normal())
            w = float(rng.normal())
            error = float(rng.normal(scale=0.4))
            y = 0.52 * previous + 0.65 * x - 0.25 * w + entity_effects[entity] + error
            rows.append({"id": entity, "time": period, "y": y, "x": x, "w": w})
            previous = y
    data = pd.DataFrame(rows)
    if case.gap_fraction:
        removable = (data["time"] > 1) & (data["time"] < case.n_periods - 1)
        draws = rng.random(len(data))
        data = data.loc[~(removable & (draws < case.gap_fraction))].copy()
    if case.unsorted:
        data = data.sample(frac=1.0, random_state=20260728).copy()
    return data


def _spec(case: BenchmarkCase) -> DynamicPanelSpec:
    return DynamicPanelSpec(
        dependent="y",
        regressors=["L1.y", "x", "w"],
        gmm=[
            GMMStyle(variable="L1.y", min_lag=2, max_lag=case.max_lag),
            GMMStyle(variable="x", min_lag=2, max_lag=case.max_lag),
        ],
        iv=[IVStyle(variable="w", eq="level")],
        time_dummies=False,
        system=case.system,
        collapse=case.collapse,
        transformation=case.transformation,  # type: ignore[arg-type]
        steps=case.steps,  # type: ignore[arg-type]
        name=case.name,
    )


def _fit(case: BenchmarkCase, data: pd.DataFrame, engine: str) -> Any:
    return run_native_dynamic_panel_gmm(
        _spec(case),
        data,
        entity="id",
        time="time",
        windmeijer=case.windmeijer,
        preparation_engine=engine,
    )


def _timed_fit(case: BenchmarkCase, data: pd.DataFrame, engine: str) -> tuple[float, Any]:
    gc.collect()
    started = time.perf_counter()
    result = _fit(case, data, engine)
    return time.perf_counter() - started, result


def _measure(
    case: BenchmarkCase, data: pd.DataFrame, engine: str, repetitions: int
) -> dict[str, Any]:
    cold_seconds, result = _timed_fit(case, data, engine)
    warm_seconds: list[float] = []
    for _ in range(repetitions):
        elapsed, result = _timed_fit(case, data, engine)
        warm_seconds.append(elapsed)

    gc.collect()
    tracemalloc.start()
    _fit(case, data, engine)
    _, peak_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return {
        "engine": engine,
        "cold_seconds": cold_seconds,
        "warm_seconds": warm_seconds,
        "warm_median_seconds": statistics.median(warm_seconds),
        "warm_min_seconds": min(warm_seconds),
        "python_peak_bytes": peak_bytes,
        "nobs_reported": result.nobs,
        "n_groups": result.n_groups,
        "n_instruments": result.n_instruments,
        "parameters": result.params.to_dict(),
        "diagnostics": {
            "hansen_p": result.hansen_p,
            "sargan_p": result.sargan_p,
            "ar1_p": result.ar1_p,
            "ar2_p": result.ar2_p,
        },
    }


def _scalar_equal(left: Any, right: Any) -> bool:
    if left is None or right is None:
        return left is right
    return bool(
        left == right
        or (np.isscalar(left) and np.isscalar(right) and np.isnan(left) and np.isnan(right))
    )


def _exactly_equal(left: Any, right: Any) -> bool:
    arrays_equal = all(
        np.array_equal(np.asarray(a), np.asarray(b), equal_nan=True)
        for a, b in (
            (left.params, right.params),
            (left.std_errors, right.std_errors),
            (left.residuals, right.residuals),
        )
    )
    diagnostics_equal = all(
        _scalar_equal(getattr(left, name), getattr(right, name))
        for name in ("nobs", "n_groups", "n_instruments", "hansen_p", "ar1_p", "ar2_p")
    )
    return arrays_equal and diagnostics_equal


def _profile(case: BenchmarkCase, data: pd.DataFrame, engine: str, limit: int) -> str:
    profiler = cProfile.Profile()
    profiler.enable()
    _fit(case, data, engine)
    profiler.disable()
    output = io.StringIO()
    pstats.Stats(profiler, stream=output).sort_stats("cumulative").print_stats(limit)
    return output.getvalue()


def _environment() -> dict[str, Any]:
    numpy_config = io.StringIO()
    with redirect_stdout(numpy_config):
        np.show_config()
    try:
        numba_version = importlib.metadata.version("numba")
    except importlib.metadata.PackageNotFoundError:
        numba_version = None
    try:
        installed_version = importlib.metadata.version("systemgmmkit")
    except importlib.metadata.PackageNotFoundError:
        installed_version = None
    return {
        "python": sys.version,
        "platform": platform.platform(),
        "processor": platform.processor(),
        "systemgmmkit": systemgmmkit.__version__,
        "systemgmmkit_source": systemgmmkit.__version__,
        "systemgmmkit_installed_distribution": installed_version,
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "scipy": scipy.__version__,
        "numba": numba_version,
        "thread_environment": {
            name: os.environ.get(name)
            for name in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS")
        },
        "numpy_config": numpy_config.getvalue(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", choices=("quick", "full"), default="quick")
    parser.add_argument("--case", help="Run one named case from the selected suite.")
    parser.add_argument("--engine", choices=("reference", "accelerated", "both"), default="both")
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument(
        "--profile-case", help="Include a cumulative cProfile report for this case."
    )
    parser.add_argument("--profile-limit", type=int, default=30)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.repetitions < 1:
        parser.error("--repetitions must be at least one")

    cases = list(QUICK_CASES if args.suite == "quick" else FULL_CASES)
    if args.case:
        cases = [case for case in cases if case.name == args.case]
        if not cases:
            parser.error(f"unknown case for {args.suite!r} suite: {args.case}")
    engines = [args.engine] if args.engine != "both" else ["reference", "accelerated"]

    records: list[dict[str, Any]] = []
    profiles: dict[str, str] = {}
    for case in cases:
        data = _panel(case)
        measurements = [_measure(case, data, engine, args.repetitions) for engine in engines]
        exact_parity = None
        if args.engine == "both":
            exact_parity = _exactly_equal(
                _fit(case, data, "reference"),
                _fit(case, data, "accelerated"),
            )
        records.append(
            {
                "case": asdict(case),
                "input_rows": len(data),
                "n_entities_input": int(data["id"].nunique()),
                "n_periods_input": int(data["time"].nunique()),
                "n_regressors": 3,
                "n_outcome_categories": None,
                "covariance_type": "native robust",
                "measurements": measurements,
                "reference_accelerated_exact_parity": exact_parity,
            }
        )
        if args.profile_case == case.name:
            for engine in engines:
                profiles[f"{case.name}:{engine}"] = _profile(case, data, engine, args.profile_limit)

    payload = {
        "benchmark": "systemgmmkit-native-gmm",
        "timing_contract": "full fit; data generation excluded; perf_counter wall time",
        "memory_contract": "tracemalloc Python allocation peak from a separate fit; not process RSS",
        "suite": args.suite,
        "repetitions": args.repetitions,
        "environment": _environment(),
        "records": records,
        "profiles": profiles,
    }
    serialized = json.dumps(payload, indent=2, allow_nan=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized + "\n", encoding="utf-8")
    print(serialized)


if __name__ == "__main__":
    main()
