"""
ML-style workflow example for systemgmmkit.

This example demonstrates:
- prediction
- fitted values
- residuals
- panel cross-validation
- GMM specification search scaffold

The workflow layer is additive. It does not change the validated estimators.
"""

import pandas as pd

from systemgmmkit.ml import (
    GMMGridSearch,
    PanelTimeSeriesSplit,
    cross_validate_panel,
    fitted_values,
    predict,
    residuals,
)


class ExampleResult:
    def __init__(self):
        self.params = pd.Series({"x": 2.0, "w": -1.0, "_con": 0.5})
        self.diagnostics = {
            "hansen_p": 0.25,
            "ar2_p": 0.40,
            "n_instruments": 8,
        }


def main() -> None:
    df = pd.DataFrame({
        "id": [1, 1, 1, 1, 2, 2, 2, 2],
        "t":  [1, 2, 3, 4, 1, 2, 3, 4],
        "y":  [2, 4, 6, 8, 3, 5, 7, 9],
        "x":  [1, 2, 3, 4, 1, 2, 3, 4],
        "w":  [0, 0, 0, 0, 1, 1, 1, 1],
    })

    result = ExampleResult()

    print("Predictions")
    print(predict(result, df))

    print("\nFitted values")
    print(fitted_values(result, df))

    print("\nResiduals")
    print(residuals(result, df, y="y"))

    def estimator(data):
        return ExampleResult()

    cv_scores = cross_validate_panel(
        estimator=estimator,
        data=df,
        y="y",
        time="t",
        cv=PanelTimeSeriesSplit(
            n_splits=2,
            min_train_periods=2,
            test_periods=1,
        ),
    )

    print("\nPanel CV scores")
    print(cv_scores)

    def build_spec(**kwargs):
        return kwargs

    def run_model(spec, data, *, entity, time):
        return ExampleResult()

    search = GMMGridSearch(
        build_spec=build_spec,
        run_model=run_model,
        param_grid=[
            {"lag_window": (2, 2), "collapse": True},
            {"lag_window": (2, 3), "collapse": True},
        ],
        y="y",
        entity="id",
        time="t",
        diagnostic_rules={
            "hansen_p": (">", 0.05),
            "ar2_p": (">", 0.05),
        },
        test_size=1,
    )

    search_result = search.fit(df)

    print("\nGMM search table")
    print(search_result.results)

    print("\nBest spec")
    print(search_result.best_spec)


if __name__ == "__main__":
    main()
