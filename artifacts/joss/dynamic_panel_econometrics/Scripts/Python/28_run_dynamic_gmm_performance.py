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

import systemgmmkit as sgk

ROOT = Path(".")
DATA = ROOT / "Data/Processed/22_dynamic_gmm_controlled_panel.csv"
OUT = ROOT / "Artifacts/Joss/tables/28_performance_benchmarks"
OUT.mkdir(parents=True, exist_ok=True)

REPETITIONS = 3


def timed_run(func):
    gc.collect()
    tracemalloc.start()
    start = time.perf_counter()
    result = func()
    elapsed = time.perf_counter() - start
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return result, elapsed, peak / (1024 * 1024)


def summarize(values):
    return {
        "mean": statistics.mean(values),
        "median": statistics.median(values),
        "min": min(values),
        "max": max(values),
        "stdev": statistics.stdev(values) if len(values) > 1 else 0.0,
    }


def try_construct(cls, variants, label):
    errors = []

    for args, kwargs in variants:
        try:
            return cls(*args, **kwargs)
        except Exception as exc:
            errors.append(
                {
                    "label": label,
                    "args": repr(args),
                    "kwargs": repr(kwargs),
                    "error": repr(exc),
                }
            )

    raise RuntimeError(f"Could not construct {label}. Errors: {errors}")


def make_gmm_style(variable: str):
    GMMStyle = sgk.GMMStyle

    variants = [
        ((variable,), {"lag_start": 2, "lag_end": 3}),
        ((variable,), {"min_lag": 2, "max_lag": 3}),
        ((variable,), {"lag_min": 2, "lag_max": 3}),
        ((variable,), {"lags": (2, 3)}),
        ((variable,), {"lag": (2, 3)}),
        ((), {"variable": variable, "lag_start": 2, "lag_end": 3}),
        ((), {"variable": variable, "min_lag": 2, "max_lag": 3}),
        ((), {"variable": variable, "lag_min": 2, "lag_max": 3}),
        ((), {"variable": variable, "lags": (2, 3)}),
        ((variable, 2, 3), {}),
        ((variable, (2, 3)), {}),
    ]

    return try_construct(GMMStyle, variants, f"GMMStyle({variable})")


def make_iv_style(variable: str):
    IVStyle = sgk.IVStyle

    variants = [
        ((variable,), {}),
        ((), {"variable": variable}),
        ((), {"var": variable}),
        ((), {"name": variable}),
        ((), {"varname": variable}),
    ]

    return try_construct(IVStyle, variants, f"IVStyle({variable})")


def build_dynamic_spec(system: bool):
    gmm = [
        make_gmm_style("L1_y"),
        make_gmm_style("x_pred"),
    ]
    iv = [make_iv_style("x_exog")]

    regressors = ["x_pred", "x_exog", "L1_y"]

    if system:
        builder = sgk.build_system_gmm_spec
        model_name = "System GMM"
    else:
        builder = sgk.build_difference_gmm_spec
        model_name = "Difference GMM"

    attempts = [
        {
            "dependent": "y",
            "regressors": regressors,
            "gmm": gmm,
            "iv": iv,
            "time_dummies": False,
            "collapse": True,
            "transformation": "fd",
            "steps": "twostep",
            "system": system,
        },
        {
            "dependent": "y",
            "regressors": regressors,
            "gmm": gmm,
            "iv": iv,
            "time_dummies": False,
            "collapse": True,
            "transformation": "fd",
            "steps": "twostep",
        },
        {
            "dependent": "y",
            "regressors": regressors,
            "gmm_styles": gmm,
            "iv_styles": iv,
            "time_dummies": False,
            "collapse": True,
            "transformation": "fd",
            "steps": "twostep",
        },
        {
            "dependent": "y",
            "regressors": regressors,
            "gmm_style": gmm,
            "iv_style": iv,
            "time_dummies": False,
            "collapse": True,
            "transformation": "fd",
            "steps": "twostep",
        },
    ]

    errors = []

    for kwargs in attempts:
        try:
            return builder(**kwargs)
        except Exception as exc:
            errors.append({"builder": builder.__name__, "kwargs": repr(kwargs), "error": repr(exc)})

    # Last fallback: direct DynamicPanelSpec if exposed.
    DynamicPanelSpec = getattr(sgk, "DynamicPanelSpec", None)

    if DynamicPanelSpec is not None:
        direct_attempts = [
            {
                "dependent": "y",
                "regressors": regressors,
                "gmm": gmm,
                "iv": iv,
                "time_dummies": False,
                "collapse": True,
                "transformation": "fd",
                "steps": "twostep",
                "system": system,
            },
            {
                "dependent": "y",
                "regressors": regressors,
                "gmm_styles": gmm,
                "iv_styles": iv,
                "time_dummies": False,
                "collapse": True,
                "transformation": "fd",
                "steps": "twostep",
                "system": system,
            },
        ]

        for kwargs in direct_attempts:
            try:
                return DynamicPanelSpec(**kwargs)
            except Exception as exc:
                errors.append({"builder": "DynamicPanelSpec", "kwargs": repr(kwargs), "error": repr(exc)})

    (OUT / f"28_{model_name.lower().replace(' ', '_')}_spec_build_errors.json").write_text(
        json.dumps(errors, indent=2),
        encoding="utf-8",
    )

    raise RuntimeError(f"Could not build {model_name} spec. See spec build error JSON.")


def extract_diagnostics(result):
    out = {}

    for attr in [
        "nobs",
        "n_obs",
        "n_groups",
        "n_instruments",
        "covariance_type",
        "hansen_p",
        "sargan_p",
        "ar1_p",
        "ar2_p",
    ]:
        if hasattr(result, attr):
            value = getattr(result, attr)
            if isinstance(value, np.generic):
                value = value.item()
            out[attr] = value

    diagnostics = getattr(result, "diagnostics", None)
    if isinstance(diagnostics, dict):
        for key, value in diagnostics.items():
            if key not in out:
                if isinstance(value, np.generic):
                    value = value.item()
                out[key] = value

    return out


def main():
    df = pd.read_csv(DATA).sort_values(["id", "time"]).copy()

    if "L1_y" not in df.columns:
        df["L1_y"] = df.groupby("id")["y"].shift(1)

    audit = {
        "data_file": str(DATA),
        "rows": int(len(df)),
        "entities": int(df["id"].nunique()),
        "periods": int(df["time"].nunique()),
        "missing_L1_y": int(df["L1_y"].isna().sum()),
        "systemgmmkit_version": getattr(sgk, "__version__", "unknown"),
        "systemgmmkit_path": getattr(sgk, "__file__", "unknown"),
    }

    (OUT / "28_dynamic_gmm_sample_audit.json").write_text(
        json.dumps(audit, indent=2),
        encoding="utf-8",
    )

    rows = []
    diag_rows = []

    configs = [
        ("Difference GMM", False, sgk.run_difference_gmm),
        ("System GMM", True, sgk.run_system_gmm),
    ]

    for benchmark, system, runner in configs:
        print(f"[SPEC] Building {benchmark}", flush=True)

        try:
            spec = build_dynamic_spec(system=system)
            print(f"[SPEC OK] {benchmark}: {type(spec).__name__}", flush=True)
        except Exception as exc:
            for rep in range(1, REPETITIONS + 1):
                rows.append({
                    "benchmark": benchmark,
                    "rep": rep,
                    "status": "ERROR",
                    "stage": "spec_build",
                    "error": repr(exc),
                })
            continue

        for rep in range(1, REPETITIONS + 1):
            print(f"[RUN] {benchmark} | rep {rep}/{REPETITIONS}", flush=True)

            try:
                result, elapsed, memory = timed_run(
                    lambda: runner(spec, df, entity="id", time="time")
                )

                rows.append({
                    "benchmark": benchmark,
                    "rep": rep,
                    "status": "OK",
                    "n_rows": int(len(df)),
                    "n_entities": int(df["id"].nunique()),
                    "n_periods": int(df["time"].nunique()),
                    "elapsed_seconds": elapsed,
                    "peak_memory_mb": memory,
                    "result_type": type(result).__name__,
                })

                d = extract_diagnostics(result)
                d.update({"benchmark": benchmark, "rep": rep, "status": "OK"})
                diag_rows.append(d)

            except Exception as exc:
                rows.append({
                    "benchmark": benchmark,
                    "rep": rep,
                    "status": "ERROR",
                    "stage": "run",
                    "error": repr(exc),
                    "traceback": traceback.format_exc(),
                })

    runs = pd.DataFrame(rows)
    runs_path = OUT / "28_dynamic_gmm_performance_runs_long.csv"
    runs.to_csv(runs_path, index=False)

    diagnostics = pd.DataFrame(diag_rows)
    diagnostics.to_csv(OUT / "28_dynamic_gmm_performance_diagnostics.csv", index=False)

    ok = runs[runs["status"].eq("OK")].copy()

    summary_rows = []
    for benchmark, group in ok.groupby("benchmark"):
        es = summarize(group["elapsed_seconds"].dropna().tolist())
        ms = summarize(group["peak_memory_mb"].dropna().tolist())

        summary_rows.append({
            "benchmark": benchmark,
            "n_rows": int(group["n_rows"].iloc[0]),
            "n_entities": int(group["n_entities"].iloc[0]),
            "n_periods": int(group["n_periods"].iloc[0]),
            "repetitions": len(group),
            "mean_seconds": es["mean"],
            "median_seconds": es["median"],
            "min_seconds": es["min"],
            "max_seconds": es["max"],
            "mean_peak_memory_mb": ms["mean"],
            "max_peak_memory_mb": ms["max"],
            "status": "OK",
        })

    summary = pd.DataFrame(summary_rows)
    summary_path = OUT / "28_dynamic_gmm_performance_summary.csv"
    summary.to_csv(summary_path, index=False)

    errors = runs[runs["status"].ne("OK")].copy()
    errors_path = OUT / "28_dynamic_gmm_performance_errors.csv"
    errors.to_csv(errors_path, index=False)

    env = {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "processor": platform.processor(),
        "systemgmmkit_version": getattr(sgk, "__version__", "unknown"),
        "systemgmmkit_path": getattr(sgk, "__file__", "unknown"),
        "repetitions": REPETITIONS,
        "data_file": str(DATA),
    }

    (OUT / "28_dynamic_gmm_performance_environment.json").write_text(
        json.dumps(env, indent=2),
        encoding="utf-8",
    )

    md = "# Artifact 28B: Dynamic-GMM Performance Benchmark\n\n"

    md += "## Sample Audit\n\n"
    md += pd.DataFrame([audit]).to_markdown(index=False)

    md += "\n\n## Runtime and Memory Summary\n\n"
    if summary.empty:
        md += "No successful dynamic-GMM benchmark runs completed. Inspect `28_dynamic_gmm_performance_errors.csv`.\n"
    else:
        md += summary.to_markdown(index=False)

    if not errors.empty:
        md += "\n\n## Errors\n\n"
        cols = [c for c in ["benchmark", "rep", "stage", "status", "error"] if c in errors.columns]
        md += errors[cols].to_markdown(index=False)

    if not diagnostics.empty:
        md += "\n\n## Diagnostics Snapshot\n\n"
        md += diagnostics.to_markdown(index=False)

    md += "\n\n## Interpretation\n\n"
    md += (
        "Artifact 28B reports controlled-panel performance for Difference GMM and System GMM. "
        "Dynamic-GMM performance is benchmarked separately from static/panel/IV workflows because "
        "instrument construction, weighting matrices, and two-step covariance correction can dominate runtime. "
        "These benchmarks are reproducibility-oriented and hardware-dependent; they are not absolute speed claims.\n"
    )

    md_path = OUT / "28_dynamic_gmm_performance_summary.md"
    md_path.write_text(md, encoding="utf-8")

    print(f"[DONE] Wrote {runs_path}", flush=True)
    print(f"[DONE] Wrote {summary_path}", flush=True)
    print(f"[DONE] Wrote {errors_path}", flush=True)
    print(f"[DONE] Wrote {md_path}", flush=True)
    print()
    print(md)


if __name__ == "__main__":
    main()
