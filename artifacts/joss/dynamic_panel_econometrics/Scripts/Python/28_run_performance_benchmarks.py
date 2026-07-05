from __future__ import annotations

import gc
import json
import platform
import statistics
import time
import traceback
import tracemalloc
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path("Artifacts/Joss/tables/28_performance_benchmarks")
OUT.mkdir(parents=True, exist_ok=True)

REPETITIONS = 5
RNG_SEED = 20260705

SIZES = [
    {"label": "small", "n_entities": 120, "n_periods": 10},
    {"label": "medium", "n_entities": 300, "n_periods": 12},
    {"label": "large", "n_entities": 600, "n_periods": 15},
]


def make_panel(n_entities: int, n_periods: int, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    rows = []
    alpha = rng.normal(0.0, 0.6, size=n_entities)

    for i in range(n_entities):
        y_prev = rng.normal()
        for t in range(n_periods):
            x_exog = rng.normal()
            x_pred = 0.45 * y_prev + rng.normal(scale=0.8)
            eps = rng.normal(scale=0.5)
            y = 0.55 * y_prev + 0.30 * x_pred + 0.20 * x_exog + alpha[i] + eps

            rows.append(
                {
                    "id": i + 1,
                    "time": t + 1,
                    "y": y,
                    "x_pred": x_pred,
                    "x_exog": x_exog,
                }
            )

            y_prev = y

    df = pd.DataFrame(rows).sort_values(["id", "time"]).reset_index(drop=True)
    df["L1_y"] = df.groupby("id")["y"].shift(1)
    df["L2_x_pred"] = df.groupby("id")["x_pred"].shift(2)

    return df


def bench_once(name: str, func):
    gc.collect()
    tracemalloc.start()
    start = time.perf_counter()

    result = func()

    elapsed = time.perf_counter() - start
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return {
        "elapsed_seconds": elapsed,
        "peak_memory_mb": peak / (1024 * 1024),
        "result_type": type(result).__name__,
    }


def summarize(values):
    return {
        "mean": statistics.mean(values),
        "median": statistics.median(values),
        "min": min(values),
        "max": max(values),
        "stdev": statistics.stdev(values) if len(values) > 1 else 0.0,
    }


def run_benchmark(name: str, label: str, n_entities: int, n_periods: int, n_rows: int, func):
    runs = []

    for rep in range(REPETITIONS):
        try:
            out = bench_once(name, func)
            runs.append(
                {
                    "benchmark": name,
                    "size_label": label,
                    "n_entities": n_entities,
                    "n_periods": n_periods,
                    "n_rows": n_rows,
                    "rep": rep + 1,
                    "status": "OK",
                    **out,
                }
            )
        except Exception as exc:
            runs.append(
                {
                    "benchmark": name,
                    "size_label": label,
                    "n_entities": n_entities,
                    "n_periods": n_periods,
                    "n_rows": n_rows,
                    "rep": rep + 1,
                    "status": "ERROR",
                    "elapsed_seconds": np.nan,
                    "peak_memory_mb": np.nan,
                    "result_type": None,
                    "error": repr(exc),
                    "traceback": traceback.format_exc(),
                }
            )

    return runs


def main() -> None:
    import systemgmmkit as sgk

    all_runs = []

    for size_index, spec_size in enumerate(SIZES):
        label = spec_size["label"]
        n_entities = spec_size["n_entities"]
        n_periods = spec_size["n_periods"]

        df = make_panel(
            n_entities=n_entities,
            n_periods=n_periods,
            seed=RNG_SEED + size_index,
        )

        static = df.dropna(subset=["y", "L1_y", "x_pred", "x_exog"]).copy()
        iv = df.dropna(subset=["y", "L1_y", "x_pred", "x_exog", "L2_x_pred"]).copy()

        n_rows = len(df)

        # OLS
        def run_ols():
            spec = sgk.OLSSpec(
                dependent="y",
                regressors=["L1_y", "x_pred", "x_exog"],
            )
            return sgk.run_ols(spec, static)

        all_runs.extend(run_benchmark("OLS", label, n_entities, n_periods, n_rows, run_ols))

        # Pooled OLS
        def run_pooled_ols():
            spec = sgk.PooledOLSSpec(
                dependent="y",
                regressors=["L1_y", "x_pred", "x_exog"],
            )
            return sgk.run_pooled_ols(spec, static)

        all_runs.extend(run_benchmark("Pooled OLS", label, n_entities, n_periods, n_rows, run_pooled_ols))

        # Fixed Effects, entity-only, aligned with Artifact 26/27
        def run_fe():
            spec = sgk.build_fixed_effects_spec(
                dependent="y",
                regressors=["L1_y", "x_pred", "x_exog"],
                entity_effects=True,
                time_effects=False,
                covariance="unadjusted",
            )
            return sgk.run_fixed_effects(
                spec,
                static,
                entity="id",
                time="time",
                prefer_backend="native",
            )

        all_runs.extend(run_benchmark("Fixed Effects", label, n_entities, n_periods, n_rows, run_fe))

        # Random Effects
        def run_re():
            spec = sgk.RandomEffectsSpec(
                dependent="y",
                regressors=["L1_y", "x_pred", "x_exog"],
                covariance="unadjusted",
                add_constant=True,
            )
            return sgk.run_random_effects(
                spec,
                static,
                entity="id",
                time="time",
            )

        all_runs.extend(run_benchmark("Random Effects", label, n_entities, n_periods, n_rows, run_re))

        # 2SLS
        def run_2sls():
            spec = sgk.PanelIVSpec(
                dependent="y",
                exog=["L1_y", "x_exog"],
                endogenous=["x_pred"],
                instruments=["L2_x_pred"],
                covariance="unadjusted",
                add_constant=True,
            )
            return sgk.run_panel_2sls(
                spec,
                iv,
                entity="id",
                time="time",
            )

        all_runs.extend(run_benchmark("2SLS", label, n_entities, n_periods, n_rows, run_2sls))

        # Difference GMM, optional
        if hasattr(sgk, "build_difference_gmm_spec") and hasattr(sgk, "run_difference_gmm"):
            def run_diff_gmm():
                spec = sgk.build_difference_gmm_spec(
                    dependent="y",
                    regressors=["x_pred", "x_exog", "L1_y"],
                    gmm_style={
                        "L1_y": {"min_lag": 2, "max_lag": 3},
                        "x_pred": {"min_lag": 2, "max_lag": 3},
                    },
                    iv_style=["x_exog"],
                    collapse=True,
                    steps="twostep",
                    covariance="robust",
                )
                return sgk.run_difference_gmm(
                    spec,
                    df,
                    entity="id",
                    time="time",
                )

            all_runs.extend(run_benchmark("Difference GMM", label, n_entities, n_periods, n_rows, run_diff_gmm))

        # System GMM, optional
        if hasattr(sgk, "build_system_gmm_spec") and hasattr(sgk, "run_system_gmm"):
            def run_sys_gmm():
                spec = sgk.build_system_gmm_spec(
                    dependent="y",
                    regressors=["x_pred", "x_exog", "L1_y"],
                    gmm_style={
                        "L1_y": {"min_lag": 2, "max_lag": 3},
                        "x_pred": {"min_lag": 2, "max_lag": 3},
                    },
                    iv_style=["x_exog"],
                    collapse=True,
                    steps="twostep",
                    covariance="robust",
                )
                return sgk.run_system_gmm(
                    spec,
                    df,
                    entity="id",
                    time="time",
                )

            all_runs.extend(run_benchmark("System GMM", label, n_entities, n_periods, n_rows, run_sys_gmm))

    runs = pd.DataFrame(all_runs)
    runs_path = OUT / "28_performance_runs_long.csv"
    runs.to_csv(runs_path, index=False)

    ok = runs[runs["status"].eq("OK")].copy()

    summary_rows = []

    for keys, group in ok.groupby(["benchmark", "size_label", "n_entities", "n_periods", "n_rows"]):
        benchmark, size_label, n_entities, n_periods, n_rows = keys

        elapsed = group["elapsed_seconds"].dropna().tolist()
        memory = group["peak_memory_mb"].dropna().tolist()

        elapsed_summary = summarize(elapsed)
        memory_summary = summarize(memory)

        summary_rows.append(
            {
                "benchmark": benchmark,
                "size_label": size_label,
                "n_entities": n_entities,
                "n_periods": n_periods,
                "n_rows": n_rows,
                "repetitions": len(group),
                "mean_seconds": elapsed_summary["mean"],
                "median_seconds": elapsed_summary["median"],
                "min_seconds": elapsed_summary["min"],
                "max_seconds": elapsed_summary["max"],
                "stdev_seconds": elapsed_summary["stdev"],
                "mean_peak_memory_mb": memory_summary["mean"],
                "median_peak_memory_mb": memory_summary["median"],
                "max_peak_memory_mb": memory_summary["max"],
            }
        )

    summary = pd.DataFrame(summary_rows).sort_values(
        ["benchmark", "n_rows"]
    )

    summary_path = OUT / "28_performance_summary.csv"
    summary.to_csv(summary_path, index=False)

    errors = runs[runs["status"].ne("OK")].copy()
    errors_path = OUT / "28_performance_errors.csv"
    errors.to_csv(errors_path, index=False)

    env = {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "processor": platform.processor(),
        "systemgmmkit_version": getattr(sgk, "__version__", "unknown"),
        "systemgmmkit_path": getattr(sgk, "__file__", "unknown"),
        "repetitions": REPETITIONS,
        "sizes": SIZES,
    }

    env_path = OUT / "28_performance_environment.json"
    env_path.write_text(json.dumps(env, indent=2), encoding="utf-8")

    md = "# Artifact 28: Performance and Scalability Benchmarks\n\n"

    md += "## Runtime and Memory Summary\n\n"
    md += summary.to_markdown(index=False)

    if not errors.empty:
        md += "\n\n## Non-completed Benchmarks\n\n"
        md += errors[["benchmark", "size_label", "rep", "status", "error"]].to_markdown(index=False)

    md += "\n\n## Interpretation\n\n"
    md += (
        "Artifact 28 reports wall-clock runtime and peak traced Python memory for key "
        "systemgmmkit workflows across increasing synthetic panel sizes. These benchmarks "
        "are intended as reproducibility and scalability evidence, not as absolute hardware-independent "
        "speed claims. Runtime depends on processor, memory, BLAS/LAPACK backend, Python version, "
        "and operating-system state. The benchmark complements the correctness evidence in "
        "Artifacts 22, 24, 25, 26, and 27.\n"
    )

    md_path = OUT / "28_performance_summary.md"
    md_path.write_text(md, encoding="utf-8")

    print(f"[DONE] Wrote {runs_path}")
    print(f"[DONE] Wrote {summary_path}")
    print(f"[DONE] Wrote {errors_path}")
    print(f"[DONE] Wrote {env_path}")
    print(f"[DONE] Wrote {md_path}")
    print()
    print(md)


if __name__ == "__main__":
    main()
