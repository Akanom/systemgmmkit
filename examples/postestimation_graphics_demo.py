from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from systemgmmkit.postestimation import (
    parameter_impact_plot,
    marginal_effects_plot,
    margins_prediction_plot,
    interaction_plot,
    conditional_effects_plot,
    residuals_vs_fitted_plot,
    qq_residual_plot,
    residual_histogram,
    fixed_effects_plot,
    panel_spaghetti_plot,
    instrument_architecture_plot,
    model_health_panel,
    counterfactual_scenario_plot,
    effect_surface_plot,
    dynamic_persistence_plot,
    export_postestimation_gallery,
)


class DemoResult:
    params = pd.Series({
        "L1.growth": 0.31,
        "techshare": 0.16,
        "polity": 0.05,
        "fragility": -0.12,
        "techshare:polity": 0.04,
        "techshare:fragility": -0.03,
        "_con": 0.02,
    })

    std_errors = pd.Series({
        "L1.growth": 0.08,
        "techshare": 0.05,
        "polity": 0.02,
        "fragility": 0.04,
        "techshare:polity": 0.015,
        "techshare:fragility": 0.014,
        "_con": 0.01,
    })

    rng = np.random.default_rng(42)
    fitted_values = np.linspace(-2, 2, 160)
    residuals = rng.normal(0, 0.8, 160)

    hansen_p = 0.19
    sargan_p = 0.09
    ar1_p = 0.08
    ar2_p = 0.32


def save(fig, figures, name, path):
    figures[name] = path
    plt.close(fig)


def main() -> None:
    out = Path("outputs/sgm_viz_gallery")
    out.mkdir(parents=True, exist_ok=True)

    result = DemoResult()
    figures = {}

    effects = pd.DataFrame({
        "term": ["techshare", "polity", "fragility"],
        "effect": [0.18, 0.04, -0.09],
        "std_error": [0.04, 0.02, 0.03],
    })

    grid = pd.DataFrame({
        "techshare": np.tile(np.linspace(0, 1, 50), 3),
        "pred": np.r_[
            np.linspace(-1.0, 0.7, 50),
            np.linspace(-0.4, 1.0, 50),
            np.linspace(0.2, 1.6, 50),
        ],
        "lo": np.r_[
            np.linspace(-1.25, 0.45, 50),
            np.linspace(-0.65, 0.75, 50),
            np.linspace(-0.05, 1.35, 50),
        ],
        "hi": np.r_[
            np.linspace(-0.75, 0.95, 50),
            np.linspace(-0.15, 1.25, 50),
            np.linspace(0.45, 1.85, 50),
        ],
        "condition": ["Low polity"] * 50 + ["Mean polity"] * 50 + ["High polity"] * 50,
    })

    fe = pd.DataFrame({
        "entity": ["Nigeria", "Ghana", "Kenya", "Ethiopia", "Rwanda", "Tanzania"],
        "effect": [0.80, -0.35, 0.10, -0.15, 0.35, 0.05],
        "std_error": [0.22, 0.18, 0.13, 0.16, 0.19, 0.12],
    })

    rng = np.random.default_rng(7)
    countries = ["Nigeria", "Ghana", "Kenya", "Ethiopia", "Rwanda", "Tanzania", "Uganda", "Senegal"]
    panel = pd.DataFrame({
        "country": np.repeat(countries, 21),
        "year": list(range(2000, 2021)) * len(countries),
        "growth": rng.normal(0.15, 0.75, 21 * len(countries)).cumsum(),
    })

    instr = pd.DataFrame({
        "lag": range(1, 9),
        "instruments": [12, 45, 70, 82, 90, 76, 55, 40],
    })

    scenario = pd.DataFrame({
        "year": list(range(2000, 2021)) * 3,
        "pred": np.r_[
            np.linspace(-1.2, 0.8, 21),
            np.linspace(-0.8, 1.5, 21),
            np.linspace(-0.4, 2.0, 21),
        ],
        "scenario": ["Baseline"] * 21 + ["High techshare"] * 21 + ["High institutions"] * 21,
    })

    surface = pd.DataFrame({
        "techshare": np.repeat(np.linspace(0, 1, 22), 22),
        "polity": np.tile(np.linspace(-2, 2, 22), 22),
    })
    surface["pred"] = (
        -0.4
        + 1.1 * surface["techshare"]
        + 0.25 * surface["polity"]
        + 0.35 * surface["techshare"] * surface["polity"]
        - 0.25 * surface["techshare"] ** 2
    )

    plot_jobs = [
        ("01_parameter_impact", lambda p: parameter_impact_plot(result, save=p)),
        ("02_marginal_response", lambda p: marginal_effects_plot(effects, save=p)),
        ("03_prediction_path", lambda p: margins_prediction_plot(grid, x="techshare", y="pred", lower="lo", upper="hi", group="condition", save=p)),
        ("04_interaction_response", lambda p: interaction_plot(grid, x="techshare", y="pred", moderator="condition", save=p)),
        ("05_conditional_effect_path", lambda p: conditional_effects_plot(grid, x="techshare", effect="pred", condition="condition", lower="lo", upper="hi", save=p)),
        ("06_model_fit_residual_map", lambda p: residuals_vs_fitted_plot(result, save=p)),
        ("07_residual_distribution_check", lambda p: qq_residual_plot(result.residuals, save=p)),
        ("08_residual_density_profile", lambda p: residual_histogram(result.residuals, save=p)),
        ("09_panel_trajectory_map", lambda p: panel_spaghetti_plot(panel, entity="country", time="year", y="growth", highlight=["Nigeria", "Ghana"], save=p)),
        ("10_unit_effect_profile", lambda p: fixed_effects_plot(fe, save=p)),
        ("11_instrument_architecture", lambda p: instrument_architecture_plot(instr, save=p)),
        ("12_model_health_panel", lambda p: model_health_panel({"Hansen": 0.19, "Sargan": 0.09, "AR(1)": 0.08, "AR(2)": 0.32}, save=p)),
        ("13_scenario_response_path", lambda p: counterfactual_scenario_plot(scenario, time="year", y="pred", scenario="scenario", save=p)),
        ("14_effect_surface", lambda p: effect_surface_plot(surface, x="techshare", y="polity", z="pred", save=p)),
        ("15_dynamic_persistence_path", lambda p: dynamic_persistence_plot(0.31, periods=20, save=p)),
    ]

    for name, fn in plot_jobs:
        path = out / f"{name}.png"
        fig = fn(path)
        save(fig, figures, name, path)

    gallery = export_postestimation_gallery(
        figures,
        output_html=out / "gallery.html",
        title="SGM-Viz post-estimation graphics gallery",
        description="A unified visual language combining econometric rigor, publication quality, enterprise polish, and decision-oriented storytelling.",
    )

    print(f"Wrote SGM-Viz figures to: {out.resolve()}")
    print(f"Wrote SGM-Viz gallery to: {gallery.resolve()}")


if __name__ == "__main__":
    main()
