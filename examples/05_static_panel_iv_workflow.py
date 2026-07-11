"""Static panel workflow: OLS, pooled OLS, FE, RE, and panel IV/2SLS.

Run:
    python examples/05_static_panel_iv_workflow.py
"""

from __future__ import annotations

from systemgmmkit import (
    FixedEffectsSpec,
    OLSSpec,
    PanelIVSpec,
    PooledOLSSpec,
    RandomEffectsSpec,
    combine_result_frames,
    run_fixed_effects,
    run_ols,
    run_panel_2sls,
    run_pooled_ols,
    run_random_effects,
)
from systemgmmkit.ml import compare_models, panel_train_test_split, quick_postestimation

from _shared_panel_data import make_static_panel, write_table_pair


ENTITY = "firm_id"
TIME = "year"
Y = "growth"
REGRESSORS = ["investment", "leverage", "size", "cashflow"]


def fit_models(data):
    """Fit the static panel estimators used in the example."""

    ols = run_ols(
        OLSSpec(
            dependent=Y,
            regressors=["investment", "leverage"],
            controls=["size", "cashflow"],
            covariance="robust",
            name="ols_robust",
        ),
        data,
        entity=ENTITY,
        time=TIME,
    )

    pooled = run_pooled_ols(
        PooledOLSSpec(
            dependent=Y,
            regressors=["investment", "leverage"],
            controls=["size", "cashflow"],
            covariance="clustered",
            name="pooled_ols_clustered",
        ),
        data,
        entity=ENTITY,
        time=TIME,
    )

    fixed_effects = run_fixed_effects(
        FixedEffectsSpec(
            dependent=Y,
            regressors=REGRESSORS,
            entity_effects=True,
            time_effects=True,
            covariance="clustered",
            cluster="entity",
            name="two_way_fixed_effects",
        ),
        data,
        entity=ENTITY,
        time=TIME,
    )

    random_effects = run_random_effects(
        RandomEffectsSpec(
            dependent=Y,
            regressors=REGRESSORS,
            covariance="clustered",
            name="random_effects",
        ),
        data,
        entity=ENTITY,
        time=TIME,
    )

    panel_iv = run_panel_2sls(
        PanelIVSpec(
            dependent=Y,
            exog=["leverage", "size", "cashflow"],
            endogenous=["investment"],
            instruments=["q_lag2"],
            entity_effects=True,
            time_effects=True,
            covariance="robust",
            name="panel_2sls_q_lag2",
        ),
        data,
        entity=ENTITY,
        time=TIME,
    )

    return {
        "OLS robust": ols,
        "Pooled OLS clustered": pooled,
        "Two-way FE": fixed_effects,
        "Random effects": random_effects,
        "Panel IV/2SLS": panel_iv,
    }


def main() -> None:
    df = make_static_panel()

    # The IV model needs q_lag2, so keep a common complete sample.
    model_data = df.dropna(subset=["q_lag2"]).copy()
    train, test = panel_train_test_split(model_data, time=TIME, test_size=2)

    models = fit_models(train)

    coefficients = combine_result_frames(
        list(models.values()),
        model_names=list(models.keys()),
    )
    write_table_pair(coefficients, "05_static_panel_iv_coefficients")

    comparison = compare_models(
        models,
        test,
        y=Y,
        raise_on_error=False,
        predict_kwargs={"strict": False},
    )
    write_table_pair(comparison, "05_static_panel_iv_model_comparison")

    post = quick_postestimation(
        models["OLS robust"],
        test,
        y=Y,
        variables=["investment", "leverage", "size", "cashflow"],
        lincoms={
            "investment plus cashflow": "investment + cashflow",
            "investment minus leverage": "investment - leverage",
        },
        wald_tests={
            "investment and cashflow": ["investment", "cashflow"],
        },
        include_vcov=True,
        strict=False,
    )
    post_path = write_table_pair(post.confidence_intervals.reset_index(names="term"), "05_static_panel_iv_confint")[0]
    markdown_path = post_path.with_name("05_static_panel_iv_postestimation.md")
    markdown_path.write_text(post.to_markdown(), encoding="utf-8")

    print("Static panel model comparison")
    print(comparison.round(4).to_string(index=False))
    print("\nWrote results under examples/results/05_static_panel_iv_*")


if __name__ == "__main__":
    main()
