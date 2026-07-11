"""Post-estimation and visualization workflow.

Run:
    python examples/08_postestimation_visualization_workflow.py
"""

from __future__ import annotations

from _shared_panel_data import ensure_results_dir, make_static_panel, write_table_pair

from systemgmmkit import (
    OLSSpec,
    coefficient_plot,
    qq_residual_plot,
    residual_histogram,
    residuals_vs_fitted_plot,
    run_ols,
)
from systemgmmkit.ml import quick_postestimation


def main() -> None:
    df = make_static_panel().dropna(subset=["q_lag2"]).copy()

    result = run_ols(
        OLSSpec(
            dependent="growth",
            regressors=["investment", "leverage"],
            controls=["size", "cashflow"],
            covariance="robust",
            name="postestimation_ols",
        ),
        df,
        entity="firm_id",
        time="year",
    )

    summary = quick_postestimation(
        result,
        df,
        y="growth",
        variables=["investment", "leverage", "size", "cashflow"],
        lincoms={
            "investment plus cashflow": "investment + cashflow",
        },
        wald_tests={
            "joint slopes": ["investment", "leverage", "size", "cashflow"],
        },
        include_vcov=True,
        strict=False,
    )

    results = ensure_results_dir()
    (results / "08_postestimation_summary.md").write_text(summary.to_markdown(), encoding="utf-8")

    if summary.marginal_effects is not None:
        write_table_pair(summary.marginal_effects.reset_index(drop=True), "08_marginal_effects")

    figures = ensure_results_dir("figures")
    coefficient_plot(
        result,
        title="OLS coefficient estimates",
        subtitle="Static panel example with robust standard errors.",
        save=figures / "08_coefficient_plot.png",
    )
    residuals_vs_fitted_plot(
        fitted=result.fitted,
        residuals=result.resid,
        title="Residuals against fitted values",
        subtitle="Checks whether fitted values leave visible residual structure.",
        save=figures / "08_residuals_vs_fitted.png",
    )
    residual_histogram(
        result.resid,
        title="Residual histogram",
        subtitle="Distribution of model residuals.",
        save=figures / "08_residual_histogram.png",
    )
    qq_residual_plot(
        result.resid,
        title="Residual Q-Q check",
        subtitle="Normal-reference residual diagnostic.",
        save=figures / "08_qq_residual_plot.png",
    )

    print("Post-estimation metrics")
    print(summary.metrics)
    print("\nWrote markdown and figures under examples/results/08_*")


if __name__ == "__main__":
    main()
