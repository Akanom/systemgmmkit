"""Reproducible static-estimator performance benchmark.

Run from the repository root with ``src`` on ``PYTHONPATH``. Data generation is
excluded from timed regions. The harness reports first-fit and repeated warm-fit
wall time, a separate ``tracemalloc`` allocation peak, estimator dimensions, and
reference/accelerated output identity where an accelerated preparation path is
available.
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
from typing import Any, Literal

import numpy as np
import pandas as pd
import scipy

import systemgmmkit
from systemgmmkit import (
    FixedEffectsSpec,
    OLSSpec,
    PanelIVSpec,
    PooledOLSSpec,
    RandomEffectsSpec,
    run_fixed_effects_native,
    run_ols,
    run_panel_2sls,
    run_pooled_ols,
    run_random_effects,
)

Estimator = Literal["ols", "pooled_ols", "fixed_effects", "random_effects", "panel_iv"]


@dataclass(frozen=True)
class BenchmarkCase:
    name: str
    estimator: Estimator
    n_entities: int
    n_periods: int
    n_regressors: int
    covariance: str
    entity_effects: bool = False
    time_effects: bool = False
    unbalanced_fraction: float = 0.0
    unsorted: bool = False

    @property
    def supports_acceleration(self) -> bool:
        return self.estimator in {"fixed_effects", "panel_iv"}


QUICK_CASES = (
    BenchmarkCase("ols_robust", "ols", 2_000, 8, 6, "robust"),
    BenchmarkCase("pooled_ols_clustered", "pooled_ols", 1_500, 8, 6, "clustered"),
    BenchmarkCase("two_way_fixed_effects", "fixed_effects", 100, 8, 3, "clustered", True, True),
    BenchmarkCase(
        "unbalanced_random_effects",
        "random_effects",
        2_000,
        8,
        4,
        "robust",
        unbalanced_fraction=0.08,
        unsorted=True,
    ),
    BenchmarkCase("panel_iv", "panel_iv", 250, 8, 3, "robust"),
    BenchmarkCase("panel_iv_lsdv", "panel_iv", 80, 8, 3, "robust", True, True, unsorted=True),
)

FULL_CASES = QUICK_CASES + (
    BenchmarkCase("large_ols_robust", "ols", 10_000, 10, 8, "robust"),
    BenchmarkCase("large_pooled_ols_clustered", "pooled_ols", 6_000, 8, 8, "clustered"),
    BenchmarkCase(
        "large_two_way_fixed_effects",
        "fixed_effects",
        240,
        8,
        4,
        "clustered",
        True,
        True,
    ),
    BenchmarkCase(
        "large_unbalanced_random_effects",
        "random_effects",
        10_000,
        8,
        6,
        "clustered",
        unbalanced_fraction=0.08,
        unsorted=True,
    ),
)


def _panel(case: BenchmarkCase) -> pd.DataFrame:
    rng = np.random.default_rng(20260728)
    nobs = case.n_entities * case.n_periods
    entity = np.repeat(np.arange(case.n_entities, dtype=np.int64), case.n_periods)
    period = np.tile(np.arange(case.n_periods, dtype=np.int64), case.n_entities)
    regressors = rng.normal(size=(nobs, case.n_regressors))
    alpha = rng.normal(scale=0.7, size=case.n_entities)[entity]
    tau = 0.08 * period
    instrument = rng.normal(size=nobs)
    endogenous = 0.75 * instrument + 0.25 * alpha + rng.normal(scale=0.45, size=nobs)
    beta = np.linspace(0.25, 0.85, case.n_regressors)
    outcome = 1.0 + regressors @ beta + 1.1 * endogenous + alpha + tau
    outcome += rng.normal(scale=0.35, size=nobs)

    data: dict[str, np.ndarray] = {
        "entity": entity,
        "time": period,
        "y": outcome,
        "endogenous": endogenous,
        "instrument": instrument,
    }
    for index in range(case.n_regressors):
        data[f"x{index + 1}"] = regressors[:, index]
    frame = pd.DataFrame(data)
    if case.unbalanced_fraction:
        internal = (frame["time"] > 0) & (frame["time"] < case.n_periods - 1)
        remove = internal & (rng.random(len(frame)) < case.unbalanced_fraction)
        frame = frame.loc[~remove].copy()
    if case.unsorted:
        frame = frame.sample(frac=1.0, random_state=20260728).copy()
    return frame


def _regressors(case: BenchmarkCase) -> list[str]:
    return [f"x{index + 1}" for index in range(case.n_regressors)]


def _fit(case: BenchmarkCase, data: pd.DataFrame, engine: str) -> Any:
    regressors = _regressors(case)
    if case.estimator == "ols":
        return run_ols(OLSSpec("y", regressors, covariance=case.covariance), data)
    if case.estimator == "pooled_ols":
        return run_pooled_ols(
            PooledOLSSpec("y", regressors, covariance=case.covariance),
            data,
            entity="entity",
            time="time",
        )
    if case.estimator == "fixed_effects":
        kwargs = {"preparation_engine": engine} if engine != "reference" else {}
        return run_fixed_effects_native(
            FixedEffectsSpec(
                "y",
                regressors,
                entity_effects=case.entity_effects,
                time_effects=case.time_effects,
                covariance=case.covariance,  # type: ignore[arg-type]
            ),
            data,
            entity="entity",
            time="time",
            **kwargs,
        )
    if case.estimator == "random_effects":
        return run_random_effects(
            RandomEffectsSpec(
                "y",
                regressors,
                covariance=case.covariance,  # type: ignore[arg-type]
            ),
            data,
            entity="entity",
            time="time",
        )
    kwargs = {"preparation_engine": engine} if engine != "reference" else {}
    return run_panel_2sls(
        PanelIVSpec(
            "y",
            exog=regressors,
            endogenous=["endogenous"],
            instruments=["instrument"],
            entity_effects=case.entity_effects,
            time_effects=case.time_effects,
            covariance=case.covariance,  # type: ignore[arg-type]
        ),
        data,
        entity="entity",
        time="time",
        **kwargs,
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
    warm_seconds = [_timed_fit(case, data, engine)[0] for _ in range(repetitions)]
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
        "nobs_reported": int(result.nobs),
        "rank": int(getattr(result, "rank", len(result.params))),
        "n_parameters_reported": int(len(result.params)),
    }


def _exactly_equal(left: Any, right: Any) -> bool:
    series = ("params", "std_errors", "residuals", "fitted_values")
    for name in series:
        left_value = getattr(left, name, None)
        right_value = getattr(right, name, None)
        if left_value is None:
            alias = "residual_values" if name == "residuals" else "fitted_values_series"
            left_value = getattr(left, alias, None)
            right_value = getattr(right, alias, None)
        if left_value is not None and not np.array_equal(
            np.asarray(left_value), np.asarray(right_value), equal_nan=True
        ):
            return False
    scalar_names = ("nobs", "rank", "df_resid", "sigma_e2", "sigma_alpha2")
    return all(getattr(left, name, None) == getattr(right, name, None) for name in scalar_names)


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
        installed_version = importlib.metadata.version("systemgmmkit")
    except importlib.metadata.PackageNotFoundError:
        installed_version = None
    return {
        "python": sys.version,
        "platform": platform.platform(),
        "processor": platform.processor(),
        "systemgmmkit_source": systemgmmkit.__version__,
        "systemgmmkit_installed_distribution": installed_version,
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "scipy": scipy.__version__,
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
    parser.add_argument("--profile-case")
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

    records: list[dict[str, Any]] = []
    profiles: dict[str, str] = {}
    for case in cases:
        data = _panel(case)
        requested = [args.engine] if args.engine != "both" else ["reference", "accelerated"]
        engines = requested if case.supports_acceleration else ["reference"]
        measurements = [_measure(case, data, engine, args.repetitions) for engine in engines]
        exact_parity = None
        if engines == ["reference", "accelerated"]:
            exact_parity = _exactly_equal(
                _fit(case, data, "reference"), _fit(case, data, "accelerated")
            )
        records.append(
            {
                "case": asdict(case),
                "input_rows": len(data),
                "n_entities_input": int(data["entity"].nunique()),
                "n_periods_input": int(data["time"].nunique()),
                "n_excluded_instruments": 1 if case.estimator == "panel_iv" else None,
                "iteration_count": None,
                "convergence_status": "closed_form",
                "measurements": measurements,
                "reference_accelerated_exact_parity": exact_parity,
            }
        )
        if args.profile_case == case.name:
            for engine in engines:
                profiles[f"{case.name}:{engine}"] = _profile(case, data, engine, args.profile_limit)

    payload = {
        "benchmark": "systemgmmkit-static-estimators",
        "timing_contract": "full fit; data generation excluded; perf_counter wall time",
        "memory_contract": "separate-fit tracemalloc Python allocation peak; not process RSS",
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
