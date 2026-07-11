"""Runnable FE, RE, IV/2SLS, and GMM-spec usage example.

This file keeps the older example name but no longer requires a local
``panel_data.csv``. It uses the same generated panel as the comprehensive
examples so users can run it immediately.
"""

from __future__ import annotations

from _shared_panel_data import ensure_results_dir, make_static_panel

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
    df = make_static_panel().dropna(subset=["q_lag2"]).copy()

    suite = build_panel_model_suite(
        name="growth_model",
        dependent="growth",
        regressors=["investment", "cashflow"],
        controls=["size", "leverage"],
        endogenous=["investment"],
        predetermined=["cashflow"],
        exogenous=["size", "leverage"],
        gmm_lags=(2, 3),
        system=True,
    )

    fe_result = run_fixed_effects(
        suite.fixed_effects,
        df,
        entity="firm_id",
        time="year",
    )

    re_result = run_random_effects(
        RandomEffectsSpec(
            dependent="growth",
            regressors=["investment", "cashflow", "size", "leverage"],
            covariance="clustered",
            name="growth_random_effects",
        ),
        df,
        entity="firm_id",
        time="year",
    )

    iv_result = run_panel_2sls(
        PanelIVSpec(
            dependent="growth",
            exog=["cashflow", "size", "leverage"],
            endogenous=["investment"],
            instruments=["q_lag2"],
            entity_effects=True,
            time_effects=True,
            covariance="robust",
            name="growth_panel_2sls",
        ),
        df,
        entity="firm_id",
        time="year",
    )

    results = ensure_results_dir()
    table_path = export_regression_table(
        [fe_result, re_result, iv_result],
        results / "fe_re_iv_gmm_usage_coefficients.md",
        fmt="markdown",
        model_names=["Two-way FE", "Random effects", "Panel IV/2SLS"],
    )
    command_path = results / "fe_re_iv_gmm_usage_system_gmm_command.txt"
    command_path.write_text(build_pydynpd_command(suite.dynamic_gmm), encoding="utf-8")

    print(fe_result.to_markdown())
    print("\nSystem GMM command scaffold")
    print(build_pydynpd_command(suite.dynamic_gmm))
    print(f"\nWrote {table_path} and {command_path}")


if __name__ == "__main__":
    main()
