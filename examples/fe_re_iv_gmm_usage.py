"""Generic panel-estimator usage example."""

from __future__ import annotations

import pandas as pd

from systemgmmkit import (
    PanelIVSpec,
    RandomEffectsSpec,
    build_panel_model_suite,
    build_pydynpd_command,
    export_regression_table,
    run_fixed_effects,
    run_panel_2sls,
    run_random_effects,
)


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

    fe_result = run_fixed_effects(suite.fixed_effects, df, entity="firm_id", time="year")

    re_result = run_random_effects(
        RandomEffectsSpec(dependent="investment", regressors=["q", "cashflow", "size", "leverage"]),
        df,
        entity="firm_id",
        time="year",
    )

    iv_result = run_panel_2sls(
        PanelIVSpec(
            dependent="investment",
            exog=["cashflow", "size", "leverage"],
            endogenous=["q"],
            instruments=["q_lag2"],
            entity_effects=True,
            time_effects=True,
        ),
        df,
        entity="firm_id",
        time="year",
    )

    print(fe_result.to_markdown())
    print(re_result.to_markdown())
    print(iv_result.to_markdown())
    print(build_pydynpd_command(suite.dynamic_gmm))

    export_regression_table([fe_result, re_result, iv_result], "panel_results.md", fmt="markdown")


if __name__ == "__main__":
    main()
