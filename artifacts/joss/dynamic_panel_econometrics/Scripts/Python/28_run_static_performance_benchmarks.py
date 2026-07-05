from __future__ import annotations

import gc
import json
import platform
import statistics
import time
import tracemalloc
from pathlib import Path

import numpy as np
import pandas as pd

import systemgmmkit as sgk

OUT = Path("Artifacts/Joss/tables/28_performance_benchmarks")
OUT.mkdir(parents=True, exist_ok=True)

REPETITIONS = 3
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

            rows.append({
                "id": i + 1,
                "time": t + 1,
                "y": y,
                "x_pred": x_pred,
                "x_exog": x_exog,
            })

            y_prev = y

    df = pd.DataFrame(rows).sort_values(["id", "time"]).reset_index(drop=True)
    df["L1_y"] = df.groupby("id")["y"].shift(1)
    df["L2_x_pred"] = df.groupby("id")["x_pred"].shift(2)
    return df


def timed_run(func):
    gc.collect()
    tracemalloc.start()
    start = time.perf_counter()
    result = func()
    elapsed = time.perf_counter() - start
    _, peak = tracemalloc.get_traced_memory()
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


def main():
    all_runs = []

    for size_index, size in enumerate(SIZES):
        label = size["label"]
        n_entities = size["n_entities"]
        n_periods = size["n_periods"]

        print(f"[SIZE] {label}: entities={n_entities}, periods={n_periods}", flush=True)

        df = make_panel(n_entities, n_periods, RNG_SEED + size_index)
        static = df.dropna(subset=["y", "L1_y", "x_pred", "x_exog"]).copy()
        iv = df.dropna(subset=["y", "L1_y", "x_pred", "x_exog", "L2_x_pred"]).copy()

        benchmarks = []

        benchmarks.append((
            "OLS",
            lambda: sgk.run_ols(
                sgk.OLSSpec(
                    dependent="y",
                    regressors=["L1_y", "x_pred", "x_exog"],
                ),
                static,
            ),
        ))

        benchmarks.append((
            "Pooled OLS",
            lambda: sgk.run_pooled_ols(
                sgk.PooledOLSSpec(
                    dependent="y",
                    regressors=["L1_y", "x_pred", "x_exog"],
                ),
                static,
            ),
        ))

        benchmarks.append((
            "Fixed Effects",
            lambda: sgk.run_fixed_effects(
                sgk.build_fixed_effects_spec(
                    dependent="y",
                    regressors=["L1_y", "x_pred", "x_exog"],
                    entity_effects=True,
                    time_effects=False,
                    covariance="unadjusted",
                ),
                static,
                entity="id",
                time="time",
                prefer_backend="native",
            ),
        ))

        benchmarks.append((
            "Random Effects",
            lambda: sgk.run_random_effects(
                sgk.RandomEffectsSpec(
                    dependent="y",
                    regressors=["L1_y", "x_pred", "x_exog"],
                    covariance="unadjusted",
                    add_constant=True,
                ),
                static,
                entity="id",
                time="time",
            ),
        ))

        benchmarks.append((
            "2SLS",
            lambda: sgk.run_panel_2sls(
                sgk.PanelIVSpec(
                    dependent="y",
                    exog=["L1_y", "x_exog"],
                    endogenous=["x_pred"],
                    instruments=["L2_x_pred"],
                    covariance="unadjusted",
                    add_constant=True,
                ),
                iv,
                entity="id",
                time="time",
            ),
        ))

        for benchmark_name, func in benchmarks:
            for rep in range(1, REPETITIONS + 1):
                print(f"[RUN] {benchmark_name} | {label} | rep {rep}/{REPETITIONS}", flush=True)

                try:
                    result = timed_run(func)
                    row = {
                        "benchmark": benchmark_name,
                        "size_label": label,
                        "n_entities": n_entities,
                        "n_periods": n_periods,
                        "n_rows_raw": len(df),
                        "n_rows_static": len(static),
                        "n_rows_iv": len(iv),
                        "rep": rep,
                        "status": "OK",
                        **result,
                    }
                except Exception as exc:
                    row = {
                        "benchmark": benchmark_name,
                        "size_label": label,
                        "n_entities": n_entities,
                        "n_periods": n_periods,
                        "n_rows_raw": len(df),
                        "n_rows_static": len(static),
                        "n_rows_iv": len(iv),
                        "rep": rep,
                        "status": "ERROR",
                        "elapsed_seconds": np.nan,
                        "peak_memory_mb": np.nan,
                        "result_type": None,
                        "error": repr(exc),
                    }

                all_runs.append(row)

    runs = pd.DataFrame(all_runs)
    runs_path = OUT / "28_static_performance_runs_long.csv"
    runs.to_csv(runs_path, index=False)

    ok = runs[runs["status"].eq("OK")].copy()

    summary_rows = []
    for keys, group in ok.groupby(["benchmark", "size_label", "n_entities", "n_periods", "n_rows_raw"]):
        benchmark, size_label, n_entities, n_periods, n_rows_raw = keys

        elapsed = group["elapsed_seconds"].dropna().tolist()
        memory = group["peak_memory_mb"].dropna().tolist()

        es = summarize(elapsed)
        ms = summarize(memory)

        summary_rows.append({
            "benchmark": benchmark,
            "size_label": size_label,
            "n_entities": n_entities,
            "n_periods": n_periods,
            "n_rows_raw": n_rows_raw,
            "repetitions": len(group),
            "mean_seconds": es["mean"],
            "median_seconds": es["median"],
            "min_seconds": es["min"],
            "max_seconds": es["max"],
            "mean_peak_memory_mb": ms["mean"],
            "max_peak_memory_mb": ms["max"],
        })

    summary = pd.DataFrame(summary_rows).sort_values(["benchmark", "n_rows_raw"])
    summary_path = OUT / "28_static_performance_summary.csv"
    summary.to_csv(summary_path, index=False)

    errors = runs[runs["status"].ne("OK")].copy()
    errors_path = OUT / "28_static_performance_errors.csv"
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

    (OUT / "28_static_performance_environment.json").write_text(
        json.dumps(env, indent=2),
        encoding="utf-8",
    )

    md = "# Artifact 28A: Static, Panel, and IV Performance Benchmarks\n\n"
    md += "## Runtime and Memory Summary\n\n"
    md += summary.to_markdown(index=False)

    if not errors.empty:
        md += "\n\n## Errors\n\n"
        md += errors.to_markdown(index=False)

    md += "\n\n## Interpretation\n\n"
    md += (
        "This artifact reports runtime and traced Python peak memory for systemgmmkit "
        "static, panel, and IV workflows. It covers OLS, pooled OLS, fixed effects, "
        "random effects, and 2SLS across increasing synthetic panel sizes. "
        "These are reproducibility-oriented benchmarks, not hardware-independent "
        "speed claims. Dynamic-GMM performance is intentionally benchmarked separately "
        "because GMM instrument construction can dominate runtime and should not block "
        "the static performance artifact.\n"
    )

    md_path = OUT / "28_static_performance_summary.md"
    md_path.write_text(md, encoding="utf-8")

    print(f"[DONE] Wrote {runs_path}", flush=True)
    print(f"[DONE] Wrote {summary_path}", flush=True)
    print(f"[DONE] Wrote {errors_path}", flush=True)
    print(f"[DONE] Wrote {md_path}", flush=True)
    print()
    print(md)


if __name__ == "__main__":
    main()
