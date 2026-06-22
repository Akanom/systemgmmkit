from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

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


class DynamicPanelDemoResult:
    """
    Lightweight fitted-result object used only to demonstrate the ML workflow
    layer around dynamic panel-style coefficient names.
    """

    def __init__(self) -> None:
        self.params = pd.Series(
            {
                "L1.y": 0.60,
                "x": 1.20,
                "w": -0.30,
                "_con": 0.50,
            }
        )
        self.diagnostics = {
            "hansen_p": 0.25,
            "ar2_p": 0.40,
            "n_instruments": 8,
        }


class StaticSearchDemoResult:
    """
    Lightweight fitted-result object used for the GMMGridSearch scaffold demo.
    """

    def __init__(self) -> None:
        self.params = pd.Series(
            {
                "x": 2.00,
                "z": -0.50,
                "_con": 1.00,
            }
        )
        self.diagnostics = {
            "hansen_p": 0.22,
            "ar2_p": 0.35,
            "n_instruments": 10,
        }


def make_static_panel() -> pd.DataFrame:
    rows: list[dict[str, float | int]] = []

    for entity in range(1, 7):
        entity_effect = 0.15 * entity
        for t in range(1, 13):
            x = 0.8 * t + 0.2 * entity
            z = 1.5 + 0.1 * t + 0.05 * entity
            y = 1.0 + 2.0 * x - 0.5 * z + entity_effect
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
    rows: list[dict[str, float | int]] = []

    for entity in range(1, 7):
        y_prev = 1.0 + 0.2 * entity
        for t in range(1, 13):
            x = 2.0 + 0.15 * t + 0.05 * entity
            w = 1.0 if entity % 2 == 0 else 0.0
            y = 0.60 * y_prev + 1.20 * x - 0.30 * w + 0.50
            rows.append(
                {
                    "id": entity,
                    "t": t,
                    "y": y,
                    "x": x,
                    "w": w,
                }
            )
            y_prev = y

    return pd.DataFrame(rows)


def write_csv(df: pd.DataFrame, path: Path) -> None:
    df.to_csv(path, index=False)


def write_json(obj: dict[str, Any], path: Path) -> None:
    path.write_text(json.dumps(obj, indent=2, default=str), encoding="utf-8")


def fit_full_ols(data: pd.DataFrame) -> Any:
    spec = OLSSpec(
        dependent="y",
        regressors=["x", "z"],
        covariance="robust",
    )
    return run_ols(spec, data)


def fit_short_ols(data: pd.DataFrame) -> Any:
    spec = OLSSpec(
        dependent="y",
        regressors=["x"],
        covariance="robust",
    )
    return run_ols(spec, data)


def run_smoke(outdir: Path) -> dict[str, Any]:
    outdir.mkdir(parents=True, exist_ok=True)

    static_df = make_static_panel()
    dynamic_df = make_dynamic_panel()

    write_csv(static_df, outdir / "static_panel.csv")
    write_csv(dynamic_df, outdir / "dynamic_panel.csv")

    # --------------------------------------------------------
    # 1. Prediction, fitted values, residuals with real OLS
    # --------------------------------------------------------
    full_ols = fit_full_ols(static_df)
    short_ols = fit_short_ols(static_df)

    pred = predict(full_ols, static_df)
    fit = fitted_values(full_ols, static_df)
    err = residuals(full_ols, static_df, y="y")

    pred_table = static_df[["id", "t", "y", "x", "z"]].copy()
    pred_table["prediction"] = pred.to_numpy()
    pred_table["fitted"] = fit.to_numpy()
    pred_table["residual"] = err.to_numpy()

    write_csv(pred_table, outdir / "ols_predictions_residuals.csv")

    # --------------------------------------------------------
    # 2. Panel cross-validation
    # --------------------------------------------------------
    cv_scores = cross_validate_panel(
        estimator=fit_full_ols,
        data=static_df,
        y="y",
        time="t",
        cv=PanelTimeSeriesSplit(
            n_splits=4,
            min_train_periods=6,
            test_periods=1,
        ),
    )

    write_csv(cv_scores, outdir / "panel_cv_scores.csv")

    # --------------------------------------------------------
    # 3. Model comparison
    # --------------------------------------------------------
    comparison = compare_models(
        {
            "OLS full": full_ols,
            "OLS short": short_ols,
        },
        static_df,
        y="y",
    )

    write_csv(comparison, outdir / "model_comparison.csv")

    # --------------------------------------------------------
    # 4. GMMGridSearch scaffold
    # --------------------------------------------------------
    def build_spec(**kwargs: Any) -> dict[str, Any]:
        return kwargs

    def run_model(spec: dict[str, Any], data: pd.DataFrame, *, entity: str, time: str) -> StaticSearchDemoResult:
        return StaticSearchDemoResult()

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

    search_result = search.fit(static_df)
    write_csv(search_result.results, outdir / "gmm_grid_search.csv")

    # --------------------------------------------------------
    # 5. Recursive forecasting
    # --------------------------------------------------------
    future_exog = pd.DataFrame(
        [
            {"id": entity, "t": t, "x": 2.0 + 0.15 * t + 0.05 * entity, "w": 1.0 if entity % 2 == 0 else 0.0}
            for entity in range(1, 7)
            for t in range(13, 16)
        ]
    )

    fc = forecast(
        DynamicPanelDemoResult(),
        dynamic_df,
        y="y",
        entity="id",
        time="t",
        horizon=3,
        future_exog=future_exog,
    )

    write_csv(fc, outdir / "forecast.csv")

    # --------------------------------------------------------
    # 6. Forecast backtesting
    # --------------------------------------------------------
    def dynamic_result_factory(data: pd.DataFrame) -> DynamicPanelDemoResult:
        return DynamicPanelDemoResult()

    backtest = backtest_forecast(
        result_factory=dynamic_result_factory,
        data=dynamic_df,
        y="y",
        entity="id",
        time="t",
        horizon=3,
        min_train_periods=6,
        max_cutoffs=3,
    )

    write_csv(backtest, outdir / "forecast_backtest.csv")

    # --------------------------------------------------------
    # 7. Summary
    # --------------------------------------------------------
    summary = {
        "status": "PASS",
        "outputs": {
            "static_panel": "static_panel.csv",
            "dynamic_panel": "dynamic_panel.csv",
            "ols_predictions_residuals": "ols_predictions_residuals.csv",
            "panel_cv_scores": "panel_cv_scores.csv",
            "model_comparison": "model_comparison.csv",
            "gmm_grid_search": "gmm_grid_search.csv",
            "forecast": "forecast.csv",
            "forecast_backtest": "forecast_backtest.csv",
        },
        "row_counts": {
            "static_panel": int(len(static_df)),
            "dynamic_panel": int(len(dynamic_df)),
            "ols_predictions_residuals": int(len(pred_table)),
            "panel_cv_scores": int(len(cv_scores)),
            "model_comparison": int(len(comparison)),
            "gmm_grid_search": int(len(search_result.results)),
            "forecast": int(len(fc)),
            "forecast_backtest": int(len(backtest)),
        },
        "best_gmm_spec": search_result.best_spec,
    }

    write_json(summary, outdir / "summary.json")

    readme = f"""# systemgmmkit ML Workflow Smoke Demo

This folder contains outputs from the ML-style workflow smoke script.

The smoke script demonstrates the additive workflow layer around already accepted estimators.

## Outputs

| File | Purpose |
|---|---|
| `static_panel.csv` | Synthetic static panel dataset |
| `dynamic_panel.csv` | Synthetic dynamic panel dataset |
| `ols_predictions_residuals.csv` | Prediction, fitted values, and residuals from real OLS |
| `panel_cv_scores.csv` | Panel time-series cross-validation scores |
| `model_comparison.csv` | ML-style comparison of fitted econometric models |
| `gmm_grid_search.csv` | GMM specification-search scaffold output |
| `forecast.csv` | Recursive dynamic-panel forecast output |
| `forecast_backtest.csv` | Expanding-window forecast backtest scores |
| `summary.json` | Machine-readable smoke-run summary |

## Status

PASS

## Design principle

The workflow layer does not modify estimator internals. It wraps already fitted results with prediction, validation, comparison, forecasting, and backtesting utilities.
"""

    (outdir / "README.md").write_text(readme, encoding="utf-8")

    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--outdir",
        default="artifacts/ml_workflow",
        help="Output directory for smoke artifacts.",
    )
    args = parser.parse_args()

    summary = run_smoke(Path(args.outdir))
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
