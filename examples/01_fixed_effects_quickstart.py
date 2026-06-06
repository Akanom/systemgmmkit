"""
Minimal Fixed Effects example for systemgmmkit.

Run:
    python examples/01_fixed_effects_quickstart.py
"""

import numpy as np
import pandas as pd

from systemgmmkit import build_fixed_effects_spec, run_fixed_effects


def make_panel_data(n_entities: int = 40, n_periods: int = 8, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []

    entity_effects = rng.normal(0, 1, n_entities)
    time_effects = rng.normal(0, 0.3, n_periods)

    for i in range(n_entities):
        for t in range(n_periods):
            x1 = rng.normal()
            x2 = rng.normal()
            y = 1.0 + 0.7 * x1 - 0.3 * x2 + entity_effects[i] + time_effects[t] + rng.normal(0, 0.5)

            rows.append(
                {
                    "entity_id": i,
                    "year": 2000 + t,
                    "y": y,
                    "x1": x1,
                    "x2": x2,
                }
            )

    return pd.DataFrame(rows)


def main() -> None:
    df = make_panel_data()

    spec = build_fixed_effects_spec(
        dependent="y",
        regressors=["x1", "x2"],
        entity_effects=True,
        time_effects=True,
        covariance="clustered",
        cluster="entity",
        name="two_way_fixed_effects_demo",
    )

    result = run_fixed_effects(
        spec,
        df,
        entity="entity_id",
        time="year",
    )

    print(result.to_markdown())


if __name__ == "__main__":
    main()
