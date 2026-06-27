from __future__ import annotations

import numpy as np
import pandas as pd

import systemgmmkit as sgk


def make_panel() -> pd.DataFrame:
    rows = []
    for firm in range(1, 7):
        for year in range(1, 9):
            investment = 0.2 * year + 0.1 * firm
            leverage = 0.5 + 0.03 * firm
            growth = 1.0 + 2.0 * investment - 0.5 * leverage
            rows.append(
                {
                    "firm": firm,
                    "year": year,
                    "growth": growth,
                    "investment": investment,
                    "leverage": leverage,
                }
            )
    return pd.DataFrame(rows)


def main() -> None:
    df = make_panel()

    spec = sgk.OLSSpec(
        dependent="growth",
        regressors=["investment", "leverage"],
        covariance="robust",
    )
    result = sgk.run_ols(spec, df)

    post = sgk.quick_postestimation(
        result,
        df,
        y="growth",
        lincoms={"total_effect": "investment + leverage"},
        wald_tests={"joint_zero": "investment = 0, leverage = 0"},
    )

    print("Parameters")
    print(result.params.round(4))
    print()

    print("Metrics")
    print({key: round(value, 6) for key, value in post.metrics.items()})
    print()

    print("Linear combinations")
    print(post.linear_combinations.round(4))
    print()

    print("Wald tests")
    print(post.wald_tests.round(4))

    assert np.isfinite(post.metrics["rmse"])
    assert post.linear_combinations is not None
    assert post.wald_tests is not None


if __name__ == "__main__":
    main()
