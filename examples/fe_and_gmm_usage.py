"""Generic fixed-effects and dynamic-panel GMM usage example."""

from __future__ import annotations

import pandas as pd

from systemgmmkit import build_panel_model_suite, build_pydynpd_command, run_fixed_effects


def main() -> None:
    df = pd.read_csv("panel_data.csv")

    suite = build_panel_model_suite(
        name="investment_model",
        dependent="investment",
        regressors=["q", "cashflow"],
        controls=["size", "leverage"],
        endogenous=["q"],
        predetermined=["cashflow"],
        exogenous=["size", "leverage"],
        system=True,
    )

    fe_result = run_fixed_effects(
        suite.fixed_effects,
        df,
        entity="firm_id",
        time="year",
    )
    print(fe_result.to_markdown())

    print(build_pydynpd_command(suite.dynamic_gmm))


if __name__ == "__main__":
    main()
