from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from systemgmmkit import OLSSpec, run_ols
from systemgmmkit.ml import (
    GMMGridSearch,
    PanelTimeSeriesSplit,
    backtest_forecast,
    compare_models,
    cross_validate_panel,
    fitted_values,
    forecast,
    predict,
    residuals,
)


class DynamicResult:
    def __init__(self) -> None:
        self.params = pd.Series(
            {
                "L1.y": 0.55,
                "x": 1.20,
                "_con": 0.10,
            }
        )
        self.diagnostics = {
            "hansen_p": 0.25,
            "ar2_p": 0.40,
            "n_instruments": 8,
        }


def make_static_panel() -> pd.DataFrame:
    rows = []

    for entity in range(1, 7):
        for t in range(1, 11):
            x = 1.0 + 0.20 * t + 0.10 * entity
            z = 0.50 + 0.05 * entity
            y = 0.75 + 1.50 * x - 0.40 * z

            rows.append(
                {
                    "id": entity,
                    "t": t,
                    "y": y,
                    "x": x,
                    "z": z,
                }
            )

    return pd.DataFrame(rows)


def make_dynamic_panel() -> pd.DataFrame:
    rows = []

    for entity in range(1, 7):
        y_prev = float(entity)

        for t in range(1, 11):
            x = 1.0 + 0.20 * t + 0.10 * entity
            y = 0.10 + 0.55 * y_prev + 1.20 * x

            rows.append(
                {
                    "id": entity,
                    "t": t,
                    "y": y,
                    "x": x,
                }
            )

            y_prev = y

    return pd.DataFrame(rows)


def fit_ols(data: pd.DataFrame):
    spec = OLSSpec(
        dependent="y",
        regressors=["x", "z"],
        covariance="robust",
    )
    return run_ols(spec, data)


def fit_ols_short(data: pd.DataFrame):
    spec = OLSSpec(
        dependent="y",
        regressors=["x"],
        covariance="robust",
    )
    return run_ols(spec, data)


def write_readme(outdir: Path) -> None:
    readme = """# systemgmmkit ML Workflow Smoke Artifacts

This directory contains reviewer-facing smoke outputs for the additive
`systemgmmkit.ml` workflow layer.

Generated files:

- `static_panel.csv`: synthetic static panel used for OLS workflow checks.
- `dynamic_panel.csv`: synthetic dynamic panel used for forecasting checks.
- `ols_predictions_residuals.csv`: predictions, fitted values, and residuals.
- `panel_cv_scores.csv`: panel time-series cross-validation metrics.
- `model_comparison.csv`: ML-style comparison of fitted model results.
- `gmm_grid_search.csv`: GMM specification-search scaffold output.
- `forecast.csv`: recursive dynamic-panel forecast output.
- `forecast_backtest.csv`: expanding-window forecast backtest metrics.
- `summary.json`: machine-readable run summary.

The smoke script does not alter validated estimator internals.
"""

    (outdir / "README.md").write_text(readme, encoding="utf-8")


def run_smoke(outdir: Path) -> None:
    outdir.mkdir(parents=True, exist_ok=True)

    static_df = make_static_panel()
    dynamic_df = make_dynamic_panel()

    static_df.to_csv(outdir / "static_panel.csv", index=False)
    dynamic_df.to_csv(outdir / "dynamic_panel.csv", index=False)

    ols_full = fit_ols(static_df)
    ols_short = fit_ols_short(static_df)

    pred = predict(ols_full, static_df)
    fit = fitted_values(ols_full, static_df)
    err = residuals(ols_full, static_df, y="y")

    pd.DataFrame(
        {
            "id": static_df["id"],
            "t": static_df["t"],
            "y": static_df["y"],
            "prediction": pred,
            "fitted": fit,
            "residual": err,
        }
    ).to_csv(outdir / "ols_predictions_residuals.csv", index=False)

    comparison = compare_models(
        {
            "OLS full": ols_full,
            "OLS short": ols_short,
        },
        static_df,
        y="y",
    )
    comparison.to_csv(outdir / "model_comparison.csv", index=False)

    cv_scores = cross_validate_panel(
        estimator=fit_ols,
        data=static_df,
        y="y",
        time="t",
        cv=PanelTimeSeriesSplit(
            n_splits=3,
            min_train_periods=5,
            test_periods=1,
        ),
    )
    cv_scores.to_csv(outdir / "panel_cv_scores.csv", index=False)

    future = pd.DataFrame(
        {
            "id": np.repeat(sorted(dynamic_df["id"].unique()), 2),
            "t": list([11, 12]) * dynamic_df["id"].nunique(),
            "x": 3.5,
        }
    )

    fc = forecast(
        DynamicResult(),
        dynamic_df,
        y="y",
        entity="id",
        time="t",
        horizon=2,
        future_exog=future,
        strict=True,
    )
    fc.to_csv(outdir / "forecast.csv", index=False)

    def dynamic_estimator(data: pd.DataFrame):
        return DynamicResult()

    backtest = backtest_forecast(
        result_factory=dynamic_estimator,
        data=dynamic_df,
        y="y",
        entity="id",
        time="t",
        horizon=2,
        min_train_periods=5,
        max_cutoffs=3,
        strict=True,
    )
    backtest.to_csv(outdir / "forecast_backtest.csv", index=False)

    def build_spec(**kwargs):
        return kwargs

    def run_model(spec, data, *, entity, time):
        return DynamicResult()

    search = GMMGridSearch(
        build_spec=build_spec,
        run_model=run_model,
        param_grid=[
            {"lag_window": (2, 2), "collapse": True},
            {"lag_window": (2, 3), "collapse": True},
            {"lag_window": (2, 4), "collapse": True},
        ],
        y="y",
        entity="id",
        time="t",
        diagnostic_rules={
            "hansen_p": (">", 0.05),
            "ar2_p": (">", 0.05),
        },
        test_size=2,
    )

    search_result = search.fit(dynamic_df)
    search_result.results.to_csv(outdir / "gmm_grid_search.csv", index=False)

    write_readme(outdir)

    expected_outputs = [
        "static_panel.csv",
        "dynamic_panel.csv",
        "ols_predictions_residuals.csv",
        "panel_cv_scores.csv",
        "model_comparison.csv",
        "gmm_grid_search.csv",
        "forecast.csv",
        "forecast_backtest.csv",
        "summary.json",
        "README.md",
    ]

    summary = {
        "status": "PASS",
        "static_panel_rows": int(len(static_df)),
        "dynamic_panel_rows": int(len(dynamic_df)),
        "entities": int(dynamic_df["id"].nunique()),
        "periods": int(dynamic_df["t"].nunique()),
        "outputs": expected_outputs,
        "row_counts": {
            "static_panel": int(len(static_df)),
            "dynamic_panel": int(len(dynamic_df)),
            "ols_predictions_residuals": int(len(static_df)),
            "panel_cv_scores": int(len(cv_scores)),
            "model_comparison": int(len(comparison)),
            "gmm_grid_search": int(len(search_result.results)),
            "forecast": int(len(fc)),
            "forecast_backtest": int(len(backtest)),
        },
        "best_gmm_spec": search_result.best_spec,
    }

    with open(outdir / "summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    missing = [name for name in expected_outputs if not (outdir / name).exists()]
    if missing:
        raise RuntimeError(f"Smoke script did not create expected files: {missing}")

    print("PASS")
    print("ML workflow smoke script completed.")
    print(f"Wrote outputs to: {outdir}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run systemgmmkit ML workflow smoke demonstration."
    )
    parser.add_argument(
        "--outdir",
        default="artifacts/ml_workflow",
        help="Directory where smoke-test artifacts should be written.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_smoke(Path(args.outdir))


if __name__ == "__main__":
    main()

