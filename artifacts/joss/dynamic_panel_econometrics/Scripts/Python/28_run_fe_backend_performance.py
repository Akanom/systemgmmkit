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
    return df


def timed_run(func):
    gc.collect()
    tracemalloc.start()
    start = time.perf_counter()
    result = func()
    elapsed = time.perf_counter() - start
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return elapsed, peak / (1024 * 1024), type(result).__name__


def summarize(values):
    return {
        "mean": statistics.mean(values),
        "median": statistics.median(values),
        "min": min(values),
        "max": max(values),
        "stdev": statistics.stdev(values) if len(values) > 1 else 0.0,
    }


def main():
    rows = []

    for size_index, size in enumerate(SIZES):
        label = size["label"]
        n_entities = size["n_entities"]
        n_periods = size["n_periods"]

        print(f"[SIZE] {label}: entities={n_entities}, periods={n_periods}", flush=True)

        df = make_panel(n_entities, n_periods, RNG_SEED + size_index)
        static = df.dropna(subset=["y", "L1_y", "x_pred", "x_exog"]).copy()

        spec = sgk.build_fixed_effects_spec(
            dependent="y",
            regressors=["L1_y", "x_pred", "x_exog"],
            entity_effects=True,
            time_effects=False,
            covariance="unadjusted",
        )

        backends = ["native", "linearmodels"]

        for backend in backends:
            for rep in range(1, REPETITIONS + 1):
                print(f"[RUN] Fixed Effects backend={backend} | {label} | rep {rep}/{REPETITIONS}", flush=True)

                try:
                    elapsed, mem, result_type = timed_run(
                        lambda: sgk.run_fixed_effects(
                            spec,
                            static,
                            entity="id",
                            time="time",
                            prefer_backend=backend,
                        )
                    )

                    rows.append({
                        "benchmark": "Fixed Effects",
                        "backend": backend,
                        "size_label": label,
                        "n_entities": n_entities,
                        "n_periods": n_periods,
                        "n_rows_raw": len(df),
                        "n_rows_static": len(static),
                        "rep": rep,
                        "status": "OK",
                        "elapsed_seconds": elapsed,
                        "peak_memory_mb": mem,
                        "result_type": result_type,
                    })

                except Exception as exc:
                    rows.append({
                        "benchmark": "Fixed Effects",
                        "backend": backend,
                        "size_label": label,
                        "n_entities": n_entities,
                        "n_periods": n_periods,
                        "n_rows_raw": len(df),
                        "n_rows_static": len(static),
                        "rep": rep,
                        "status": "ERROR",
                        "elapsed_seconds": np.nan,
                        "peak_memory_mb": np.nan,
                        "result_type": None,
                        "error": repr(exc),
                    })

    runs = pd.DataFrame(rows)
    runs_path = OUT / "28_fe_backend_performance_runs_long.csv"
    runs.to_csv(runs_path, index=False)

    ok = runs[runs["status"].eq("OK")].copy()

    summary_rows = []
    for keys, group in ok.groupby(["benchmark", "backend", "size_label", "n_entities", "n_periods", "n_rows_raw"]):
        benchmark, backend, size_label, n_entities, n_periods, n_rows_raw = keys

        elapsed = group["elapsed_seconds"].tolist()
        memory = group["peak_memory_mb"].tolist()
        es = summarize(elapsed)
        ms = summarize(memory)

        summary_rows.append({
            "benchmark": benchmark,
            "backend": backend,
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

    summary = pd.DataFrame(summary_rows).sort_values(["backend", "n_rows_raw"])
    summary_path = OUT / "28_fe_backend_performance_summary.csv"
    summary.to_csv(summary_path, index=False)

    md = "# Artifact 28A Addendum: Fixed-Effects Backend Performance\n\n"
    md += "## Runtime and Memory Summary\n\n"
    md += summary.to_markdown(index=False)
    md += "\n\n## Interpretation\n\n"
    md += (
        "This addendum compares the native and linearmodels fixed-effects backends. "
        "The main static benchmark identified fixed effects as the dominant runtime bottleneck. "
        "This backend comparison determines whether the linearmodels backend should be recommended "
        "for larger fixed-effects panels.\n"
    )

    md_path = OUT / "28_fe_backend_performance_summary.md"
    md_path.write_text(md, encoding="utf-8")

    env = {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "systemgmmkit_version": getattr(sgk, "__version__", "unknown"),
        "systemgmmkit_path": getattr(sgk, "__file__", "unknown"),
        "repetitions": REPETITIONS,
        "sizes": SIZES,
    }

    (OUT / "28_fe_backend_performance_environment.json").write_text(
        json.dumps(env, indent=2),
        encoding="utf-8",
    )

    print(f"[DONE] Wrote {runs_path}")
    print(f"[DONE] Wrote {summary_path}")
    print(f"[DONE] Wrote {md_path}")
    print()
    print(md)


if __name__ == "__main__":
    main()
