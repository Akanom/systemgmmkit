from __future__ import annotations

import gc
import json
import multiprocessing as mp
import platform
import statistics
import time
import traceback
import tracemalloc
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(".")
DATA = ROOT / "Data/Processed/22_dynamic_gmm_controlled_panel.csv"
OUT = ROOT / "Artifacts/Joss/tables/28_performance_benchmarks"
OUT.mkdir(parents=True, exist_ok=True)

REPETITIONS = 1
TIMEOUT_SECONDS = 180

SUBSETS = [
    {"size_label": "tiny", "max_entities": 30},
    {"size_label": "small", "max_entities": 60},
]


def try_construct(cls, variants, label):
    errors = []

    for args, kwargs in variants:
        try:
            return cls(*args, **kwargs)
        except Exception as exc:
            errors.append({
                "label": label,
                "args": repr(args),
                "kwargs": repr(kwargs),
                "error": repr(exc),
            })

    raise RuntimeError(f"Could not construct {label}. Errors: {errors}")


def make_gmm_style(sgk, variable: str):
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


def make_iv_style(sgk, variable: str):
    IVStyle = sgk.IVStyle

    variants = [
        ((variable,), {}),
        ((), {"variable": variable}),
        ((), {"var": variable}),
        ((), {"name": variable}),
        ((), {"varname": variable}),
    ]

    return try_construct(IVStyle, variants, f"IVStyle({variable})")


def build_dynamic_spec(sgk, system: bool):
    gmm = [
        make_gmm_style(sgk, "L1_y"),
        make_gmm_style(sgk, "x_pred"),
    ]
    iv = [make_iv_style(sgk, "x_exog")]

    regressors = ["x_pred", "x_exog", "L1_y"]

    builder = sgk.build_system_gmm_spec if system else sgk.build_difference_gmm_spec

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
    ]

    errors = []

    for kwargs in attempts:
        try:
            return builder(**kwargs)
        except Exception as exc:
            errors.append({"builder": builder.__name__, "kwargs": repr(kwargs), "error": repr(exc)})

    DynamicPanelSpec = getattr(sgk, "DynamicPanelSpec", None)

    if DynamicPanelSpec is not None:
        for kwargs in attempts:
            try:
                return DynamicPanelSpec(**kwargs)
            except Exception as exc:
                errors.append({"builder": "DynamicPanelSpec", "kwargs": repr(kwargs), "error": repr(exc)})

    raise RuntimeError(f"Could not build dynamic-GMM spec. Errors: {errors}")


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


def worker(queue, benchmark, system, data_payload):
    try:
        import systemgmmkit as sgk

        df = pd.DataFrame(data_payload)

        spec = build_dynamic_spec(sgk, system=system)
        runner = sgk.run_system_gmm if system else sgk.run_difference_gmm

        gc.collect()
        tracemalloc.start()
        start = time.perf_counter()

        result = runner(spec, df, entity="id", time="time")

        elapsed = time.perf_counter() - start
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        row = {
            "benchmark": benchmark,
            "status": "OK",
            "elapsed_seconds": elapsed,
            "peak_memory_mb": peak / (1024 * 1024),
            "result_type": type(result).__name__,
        }

        diag = extract_diagnostics(result)

        queue.put({
            "row": row,
            "diagnostics": diag,
        })

    except Exception as exc:
        queue.put({
            "row": {
                "benchmark": benchmark,
                "status": "ERROR",
                "stage": "worker",
                "error": repr(exc),
                "traceback": traceback.format_exc(),
            },
            "diagnostics": {},
        })


def summarize(values):
    return {
        "mean": statistics.mean(values),
        "median": statistics.median(values),
        "min": min(values),
        "max": max(values),
        "stdev": statistics.stdev(values) if len(values) > 1 else 0.0,
    }


def write_outputs(rows, diagnostics, audit):
    runs = pd.DataFrame(rows)
    runs_path = OUT / "28_dynamic_gmm_performance_runs_long.csv"
    runs.to_csv(runs_path, index=False)

    diagnostics_df = pd.DataFrame(diagnostics)
    diagnostics_df.to_csv(OUT / "28_dynamic_gmm_performance_diagnostics.csv", index=False)

    ok = runs[runs["status"].eq("OK")].copy()

    summary_rows = []
    if not ok.empty:
        for keys, group in ok.groupby(["benchmark", "size_label", "n_rows", "n_entities", "n_periods"]):
            benchmark, size_label, n_rows, n_entities, n_periods = keys

            es = summarize(group["elapsed_seconds"].dropna().tolist())
            ms = summarize(group["peak_memory_mb"].dropna().tolist())

            summary_rows.append({
                "benchmark": benchmark,
                "size_label": size_label,
                "n_rows": int(n_rows),
                "n_entities": int(n_entities),
                "n_periods": int(n_periods),
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
    summary.to_csv(OUT / "28_dynamic_gmm_performance_summary.csv", index=False)

    errors = runs[runs["status"].ne("OK")].copy()
    errors.to_csv(OUT / "28_dynamic_gmm_performance_errors.csv", index=False)

    md = "# Artifact 28B: Dynamic-GMM Performance Benchmark\n\n"

    md += "## Sample Audit\n\n"
    md += pd.DataFrame(audit).to_markdown(index=False)

    md += "\n\n## Runtime and Memory Summary\n\n"
    if summary.empty:
        md += "No successful dynamic-GMM benchmark runs completed. Inspect `28_dynamic_gmm_performance_errors.csv`.\n"
    else:
        md += summary.to_markdown(index=False)

    if not errors.empty:
        md += "\n\n## Errors / Timeouts\n\n"
        cols = [c for c in ["benchmark", "size_label", "rep", "status", "stage", "error"] if c in errors.columns]
        md += errors[cols].to_markdown(index=False)

    if not diagnostics_df.empty:
        md += "\n\n## Diagnostics Snapshot\n\n"
        md += diagnostics_df.to_markdown(index=False)

    md += "\n\n## Interpretation\n\n"
    md += (
        "Artifact 28B reports controlled dynamic-GMM performance using bounded subprocess runs. "
        "Difference GMM and System GMM are benchmarked separately from static/panel/IV workflows "
        "because instrument construction, weighting matrices, and two-step covariance correction can dominate runtime. "
        "Runs that exceed the timeout are reported transparently rather than blocking artifact generation. "
        "These benchmarks are reproducibility-oriented and hardware-dependent; they are not absolute speed claims.\n"
    )

    md_path = OUT / "28_dynamic_gmm_performance_summary.md"
    md_path.write_text(md, encoding="utf-8")

    return runs, summary, errors, diagnostics_df, md


def main():
    import systemgmmkit as sgk

    df = pd.read_csv(DATA).sort_values(["id", "time"]).copy()

    if "L1_y" not in df.columns:
        df["L1_y"] = df.groupby("id")["y"].shift(1)

    rows = []
    diagnostics = []
    audit = []

    configs = [
        ("Difference GMM", False),
        ("System GMM", True),
    ]

    ctx = mp.get_context("spawn")

    for subset in SUBSETS:
        size_label = subset["size_label"]
        max_entities = subset["max_entities"]

        ids = sorted(df["id"].unique())[:max_entities]
        sub = df[df["id"].isin(ids)].copy()

        audit.append({
            "size_label": size_label,
            "rows": int(len(sub)),
            "entities": int(sub["id"].nunique()),
            "periods": int(sub["time"].nunique()),
            "missing_L1_y": int(sub["L1_y"].isna().sum()),
            "systemgmmkit_version": getattr(sgk, "__version__", "unknown"),
            "timeout_seconds": TIMEOUT_SECONDS,
        })

        payload = sub.to_dict(orient="list")

        for benchmark, system in configs:
            for rep in range(1, REPETITIONS + 1):
                print(f"[RUN] {benchmark} | {size_label} | rep {rep}/{REPETITIONS}", flush=True)

                queue = ctx.Queue()
                proc = ctx.Process(
                    target=worker,
                    args=(queue, benchmark, system, payload),
                )

                start = time.perf_counter()
                proc.start()
                proc.join(TIMEOUT_SECONDS)
                wall = time.perf_counter() - start

                if proc.is_alive():
                    proc.terminate()
                    proc.join()

                    row = {
                        "benchmark": benchmark,
                        "size_label": size_label,
                        "rep": rep,
                        "status": "TIMEOUT",
                        "stage": "run",
                        "elapsed_seconds": wall,
                        "peak_memory_mb": np.nan,
                        "result_type": None,
                        "error": f"Exceeded timeout of {TIMEOUT_SECONDS} seconds",
                        "n_rows": int(len(sub)),
                        "n_entities": int(sub["id"].nunique()),
                        "n_periods": int(sub["time"].nunique()),
                    }

                    rows.append(row)

                else:
                    if queue.empty():
                        row = {
                            "benchmark": benchmark,
                            "size_label": size_label,
                            "rep": rep,
                            "status": "ERROR",
                            "stage": "process",
                            "elapsed_seconds": wall,
                            "peak_memory_mb": np.nan,
                            "result_type": None,
                            "error": f"Process exited without queue output. exitcode={proc.exitcode}",
                            "n_rows": int(len(sub)),
                            "n_entities": int(sub["id"].nunique()),
                            "n_periods": int(sub["time"].nunique()),
                        }
                        rows.append(row)
                    else:
                        result = queue.get()
                        row = result["row"]
                        row.update({
                            "size_label": size_label,
                            "rep": rep,
                            "n_rows": int(len(sub)),
                            "n_entities": int(sub["id"].nunique()),
                            "n_periods": int(sub["time"].nunique()),
                        })
                        rows.append(row)

                        diag = result.get("diagnostics", {})
                        diag.update({
                            "benchmark": benchmark,
                            "size_label": size_label,
                            "rep": rep,
                            "status": row["status"],
                        })
                        diagnostics.append(diag)

                # checkpoint after every run
                write_outputs(rows, diagnostics, audit)

    env = {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "processor": platform.processor(),
        "systemgmmkit_version": getattr(sgk, "__version__", "unknown"),
        "systemgmmkit_path": getattr(sgk, "__file__", "unknown"),
        "repetitions": REPETITIONS,
        "timeout_seconds": TIMEOUT_SECONDS,
        "subsets": SUBSETS,
    }

    (OUT / "28_dynamic_gmm_performance_environment.json").write_text(
        json.dumps(env, indent=2),
        encoding="utf-8",
    )

    _, _, _, _, md = write_outputs(rows, diagnostics, audit)
    print()
    print(md)


if __name__ == "__main__":
    main()
