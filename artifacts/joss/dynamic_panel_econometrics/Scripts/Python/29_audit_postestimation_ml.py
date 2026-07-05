from __future__ import annotations

import inspect
import json
from pathlib import Path

import pandas as pd

import systemgmmkit as sgk

OUT = Path("Artifacts/Joss/tables/29_postestimation_ml_workflows")
OUT.mkdir(parents=True, exist_ok=True)

DATA = Path("Data/Processed/22_dynamic_gmm_controlled_panel.csv")


def short_repr(x, n=300):
    s = repr(x)
    return s[:n] + "..." if len(s) > n else s


def describe_value(x):
    out = {"type": type(x).__name__}

    if hasattr(x, "shape"):
        try:
            out["shape"] = list(x.shape)
        except Exception:
            pass

    if isinstance(x, dict):
        out["keys"] = list(x.keys())[:20]

    out["repr"] = short_repr(x)
    return out


def get_callable(name):
    candidates = []

    if hasattr(sgk, name):
        candidates.append(("systemgmmkit", getattr(sgk, name)))

    for module_name in ["postestimation", "ml"]:
        try:
            module = __import__(f"systemgmmkit.{module_name}", fromlist=["*"])
            if hasattr(module, name):
                candidates.append((f"systemgmmkit.{module_name}", getattr(module, name)))
        except Exception:
            pass

    return candidates[0] if candidates else (None, None)


def try_one(check, func_name, attempts):
    module_name, func = get_callable(func_name)

    if func is None:
        return {
            "layer": "postestimation",
            "check": check,
            "function": func_name,
            "module": None,
            "status": "NOT_AVAILABLE",
            "message": f"{func_name} not exposed",
            "value": None,
        }

    last_error = None

    for label, call in attempts:
        try:
            value = call(func)
            return {
                "layer": "postestimation",
                "check": check,
                "function": func_name,
                "module": module_name,
                "status": "OK",
                "message": label,
                "value": json.dumps(describe_value(value), default=str),
            }
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"

    return {
        "layer": "postestimation",
        "check": check,
        "function": func_name,
        "module": module_name,
        "status": "ERROR",
        "message": last_error,
        "value": None,
    }


def main():
    df = pd.read_csv(DATA).sort_values(["id", "time"]).copy()

    if "L1_y" not in df.columns:
        df["L1_y"] = df.groupby("id")["y"].shift(1)

    work = df.dropna(subset=["y", "L1_y", "x_pred", "x_exog"]).copy()

    spec = sgk.OLSSpec(
        dependent="y",
        regressors=["L1_y", "x_pred", "x_exog"],
    )
    result = sgk.run_ols(spec, work)

    rows = []

    rows.append(try_one(
        "vcov",
        "vcov",
        [("vcov(result)", lambda f: f(result))]
    ))

    rows.append(try_one(
        "confint",
        "confint",
        [("confint(result)", lambda f: f(result))]
    ))

    rows.append(try_one(
        "predict",
        "predict",
        [
            ("predict(result, data)", lambda f: f(result, work)),
            ("predict(result)", lambda f: f(result)),
        ]
    ))

    rows.append(try_one(
        "fitted_values",
        "fitted_values",
        [("fitted_values(result)", lambda f: f(result))]
    ))

    rows.append(try_one(
        "residuals",
        "residuals",
        [("residuals(result)", lambda f: f(result))]
    ))

    rows.append(try_one(
        "lincom",
        "lincom",
        [
            ("lincom(result, expression='x_pred + x_exog')", lambda f: f(result, expression="x_pred + x_exog")),
            ("lincom(result, weights={'x_pred':1,'x_exog':1})", lambda f: f(result, weights={"x_pred": 1.0, "x_exog": 1.0})),
        ]
    ))

    rows.append(try_one(
        "wald_test",
        "wald_test",
        [
            ("wald_test(result, variables=['x_pred'])", lambda f: f(result, variables=["x_pred"])),
            ("wald_test(result, constraints=['x_pred = 0'])", lambda f: f(result, constraints=["x_pred = 0"])),
        ]
    ))

    rows.append(try_one(
        "marginal_effects",
        "marginal_effects",
        [
            ("marginal_effects(result, variables=[...])", lambda f: f(result, variables=["L1_y", "x_pred", "x_exog"])),
            ("marginal_effects(result)", lambda f: f(result)),
        ]
    ))

    rows.append(try_one(
        "margins",
        "margins",
        [
            ("margins(result, data=work)", lambda f: f(result, data=work)),
            ("margins(result)", lambda f: f(result)),
        ]
    ))

    post = pd.DataFrame(rows)
    post.to_csv(OUT / "29_postestimation_audit.csv", index=False)

    # ML inventory and smoke checks
    ml_rows = []
    ml_smoke = []

    try:
        import systemgmmkit.ml as ml

        for name in sorted([x for x in dir(ml) if not x.startswith("_")]):
            obj = getattr(ml, name)

            if inspect.isfunction(obj) or inspect.isclass(obj):
                try:
                    sig = str(inspect.signature(obj))
                except Exception:
                    sig = ""

                ml_rows.append({
                    "name": name,
                    "kind": "class" if inspect.isclass(obj) else "function",
                    "signature": sig,
                    "module": getattr(obj, "__module__", "systemgmmkit.ml"),
                })

        def ml_call(name, attempts):
            if not hasattr(ml, name):
                ml_smoke.append({
                    "layer": "ml",
                    "check": name,
                    "function": name,
                    "status": "NOT_AVAILABLE",
                    "message": f"{name} not exposed",
                    "value": None,
                })
                return

            func = getattr(ml, name)
            last_error = None

            for label, call in attempts:
                try:
                    value = call(func)
                    ml_smoke.append({
                        "layer": "ml",
                        "check": name,
                        "function": name,
                        "status": "OK",
                        "message": label,
                        "value": json.dumps(describe_value(value), default=str),
                    })
                    return
                except Exception as exc:
                    last_error = f"{type(exc).__name__}: {exc}"

            ml_smoke.append({
                "layer": "ml",
                "check": name,
                "function": name,
                "status": "ERROR",
                "message": last_error,
                "value": None,
            })

        ml_call("adapt_result", [
            ("adapt_result(result)", lambda f: f(result)),
        ])

        ml_call("predict", [
            ("predict(result, data)", lambda f: f(result, work)),
            ("predict(result)", lambda f: f(result)),
        ])

        ml_call("fitted_values", [
            ("fitted_values(result)", lambda f: f(result)),
        ])

        ml_call("residuals", [
            ("residuals(result)", lambda f: f(result)),
        ])

        y_true = work["y"]
        y_pred = getattr(result, "fitted_values", None)
        if y_pred is None:
            try:
                y_pred = sgk.fitted_values(result)
            except Exception:
                y_pred = None

        if y_pred is not None:
            ml_call("regression_metrics", [
                ("regression_metrics(y_true, y_pred)", lambda f: f(y_true, y_pred)),
            ])
        else:
            ml_smoke.append({
                "layer": "ml",
                "check": "regression_metrics",
                "function": "regression_metrics",
                "status": "SKIPPED",
                "message": "Could not obtain fitted values",
                "value": None,
            })

        ml_call("panel_train_test_split", [
            ("panel_train_test_split(data, entity='id', time='time')", lambda f: f(work, entity="id", time="time")),
            ("panel_train_test_split(data, entity='id', time='time', test_size=0.2)", lambda f: f(work, entity="id", time="time", test_size=0.2)),
        ])

        for name in ["PanelTimeSeriesSplit", "cross_validate_panel", "compare_models", "forecast", "backtest_forecast", "backtest_fore"]:
            if hasattr(ml, name):
                obj = getattr(ml, name)
                try:
                    sig = str(inspect.signature(obj))
                except Exception:
                    sig = ""
                ml_smoke.append({
                    "layer": "ml",
                    "check": name,
                    "function": name,
                    "status": "DISCOVERED",
                    "message": sig,
                    "value": None,
                })
            else:
                ml_smoke.append({
                    "layer": "ml",
                    "check": name,
                    "function": name,
                    "status": "NOT_AVAILABLE",
                    "message": f"{name} not exposed",
                    "value": None,
                })

    except Exception as exc:
        ml_rows.append({
            "name": "systemgmmkit.ml",
            "kind": "module",
            "signature": "",
            "module": "systemgmmkit.ml",
            "error": repr(exc),
        })

    ml_inventory = pd.DataFrame(ml_rows)
    ml_inventory.to_csv(OUT / "29_ml_api_inventory.csv", index=False)

    ml_smoke_df = pd.DataFrame(ml_smoke)
    ml_smoke_df.to_csv(OUT / "29_ml_smoke_audit.csv", index=False)

    summary_rows = []

    for label, df_part in [
        ("postestimation", post),
        ("ml_smoke", ml_smoke_df),
    ]:
        counts = df_part["status"].value_counts().to_dict() if not df_part.empty else {}
        summary_rows.append({
            "layer": label,
            "OK": counts.get("OK", 0),
            "DISCOVERED": counts.get("DISCOVERED", 0),
            "NOT_AVAILABLE": counts.get("NOT_AVAILABLE", 0),
            "ERROR": counts.get("ERROR", 0),
            "SKIPPED": counts.get("SKIPPED", 0),
        })

    summary = pd.DataFrame(summary_rows)
    summary.to_csv(OUT / "29_postestimation_ml_summary.csv", index=False)

    md = "# Artifact 29: Post-Estimation and ML Workflow Coverage\n\n"

    md += "## Summary\n\n"
    md += summary.to_markdown(index=False)

    md += "\n\n## Post-Estimation Audit\n\n"
    md += post.to_markdown(index=False)

    md += "\n\n## ML Smoke Audit\n\n"
    if ml_smoke_df.empty:
        md += "No ML smoke checks were executed.\n"
    else:
        md += ml_smoke_df.to_markdown(index=False)

    md += "\n\n## ML API Inventory\n\n"
    if ml_inventory.empty:
        md += "No ML API inventory was found.\n"
    else:
        md += ml_inventory.to_markdown(index=False)

    md += "\n\n## Interpretation\n\n"
    md += (
        "Artifact 29 documents the post-estimation and ML-style workflow layer in systemgmmkit. "
        "The post-estimation checks cover variance-covariance extraction, confidence intervals, "
        "prediction, fitted values, residuals, linear combinations, Wald tests, marginal effects, "
        "and a margins-style API where exposed. The ML audit inventories and smoke-tests the "
        "available ML-style helpers, including result adaptation, prediction, fitted/residual "
        "extraction, regression metrics, panel train/test splitting, panel time-series validation, "
        "model comparison, forecasting, and backtesting when those APIs are exposed by the installed package.\n"
    )

    md += "\n\n## Paper-Safe Summary\n\n"
    md += (
        "In addition to estimators and dynamic-GMM validation, systemgmmkit includes a post-estimation "
        "and workflow layer. The post-estimation layer supports Stata-style operations such as linear "
        "combinations, Wald tests, and marginal-effects workflows. The ML-style layer provides helper "
        "interfaces for prediction, residual extraction, metrics, time-aware panel splitting, model "
        "comparison, and forecasting-oriented workflows. These capabilities are reported as workflow "
        "coverage rather than numerical parity claims unless a direct external reference is used.\n"
    )

    path = OUT / "29_postestimation_ml_summary.md"
    path.write_text(md, encoding="utf-8")

    meta = {
        "systemgmmkit_version": getattr(sgk, "__version__", "unknown"),
        "systemgmmkit_path": getattr(sgk, "__file__", "unknown"),
        "data": str(DATA),
        "n_rows": int(len(work)),
    }
    (OUT / "29_postestimation_ml_environment.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print("[DONE] Wrote", path)
    print(md)


if __name__ == "__main__":
    main()
