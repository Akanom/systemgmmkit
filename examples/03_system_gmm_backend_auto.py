"""
Minimal System GMM example for systemgmmkit.

Run:
    python examples/03_system_gmm_backend_auto.py

Note:
    System GMM uses the validated backend route when backend="auto".
"""

import numpy as np
import pandas as pd

from systemgmmkit import build_system_gmm_spec, run_system_gmm


def make_dynamic_panel(n_entities: int = 80, n_periods: int = 10, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []

    for i in range(n_entities):
        alpha = rng.normal()
        y_lag = rng.normal()

        for t in range(n_periods):
            x1 = rng.normal()
            x2 = rng.normal()
            control = rng.normal()
            error = rng.normal(0, 0.5)

            y = 0.45 * y_lag + 0.6 * x1 - 0.25 * x2 + 0.2 * control + alpha + error

            rows.append(
                {
                    "entity_id": i,
                    "year": 2000 + t,
                    "y": y,
                    "x1": x1,
                    "x2": x2,
                    "control": control,
                }
            )

            y_lag = y

    return pd.DataFrame(rows)


def main() -> None:
    df = make_dynamic_panel()

    spec = build_system_gmm_spec(
        dependent="y",
        regressors=["x1", "x2", "control"],
        endogenous=["x1"],
        predetermined=["x2"],
        exogenous=["control"],
        lag_limits={
            "y": (2, 3),
            "x1": (2, 2),
            "x2": (2, 2),
        },
        collapse=True,
        time_dummies=True,
        steps="twostep",
        name="system_gmm_demo",
    )

    result = run_system_gmm(
        spec,
        df,
        entity="entity_id",
        time="year",
        backend="auto",
    )

    print(result.to_markdown())


if __name__ == "__main__":
    main()
