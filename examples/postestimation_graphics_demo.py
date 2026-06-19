from pathlib import Path

import numpy as np
import pandas as pd

from systemgmmkit.postestimation import (
    coefficient_plot,
    marginal_effects_plot,
    margins_prediction_plot,
    interaction_plot,
    conditional_effects_plot,
    residuals_vs_fitted_plot,
    qq_residual_plot,
    residual_histogram,
    fixed_effects_plot,
    panel_spaghetti_plot,
    instrument_count_plot,
    hansen_ar_diagnostic_plot,
    counterfactual_scenario_plot,
    surface_3d_plot,
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


def main() -> None:
    out = Path("outputs/postestimation_graphics")
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

    for style in ["stata", "journal", "dashboard"]:
        preset = "dashboard" if style == "dashboard" else "paper"

        path = out / f"{style}_01_coefficient_plot.png"
        fig = coefficient_plot(result, style=style, preset=preset, save=path); import matplotlib.pyplot as plt; plt.close(fig)
        figures[f"{style}_coefficient_plot"] = path

        path = out / f"{style}_02_marginal_effects.png"
        marginal_effects_plot(effects, style=style, preset=preset, save=path)
        figures[f"{style}_marginal_effects"] = path

        path = out / f"{style}_03_margins_prediction.png"
        margins_prediction_plot(
            grid,
            x="techshare",
            y="pred",
            lower="lo",
            upper="hi",
            group="condition",
            style=style,
            preset=preset,
            save=path,
        )
        figures[f"{style}_margins_prediction"] = path

        path = out / f"{style}_04_interaction.png"
        interaction_plot(grid, x="techshare", y="pred", moderator="condition", style=style, preset=preset, save=path)
        figures[f"{style}_interaction"] = path

        path = out / f"{style}_05_conditional_effects.png"
        conditional_effects_plot(
            grid,
            x="techshare",
            effect="pred",
            condition="condition",
            lower="lo",
            upper="hi",
            style=style,
            preset=preset,
            save=path,
        )
        figures[f"{style}_conditional_effects"] = path

        path = out / f"{style}_06_residuals_vs_fitted.png"
        residuals_vs_fitted_plot(result, style=style, preset=preset, save=path)
        figures[f"{style}_residuals_vs_fitted"] = path

        path = out / f"{style}_07_qq_residuals.png"
        qq_residual_plot(result.residuals, style=style, preset=preset, save=path)
        figures[f"{style}_qq_residuals"] = path

        path = out / f"{style}_08_residual_histogram.png"
        residual_histogram(result.residuals, style=style, preset=preset, save=path)
        figures[f"{style}_residual_histogram"] = path

        path = out / f"{style}_09_panel_spaghetti.png"
        panel_spaghetti_plot(
            panel,
            entity="country",
            time="year",
            y="growth",
            highlight=["Nigeria", "Ghana"],
            style=style,
            preset=preset,
            save=path,
        )
        figures[f"{style}_panel_spaghetti"] = path

        path = out / f"{style}_10_fixed_effects.png"
        fixed_effects_plot(fe, style=style, preset=preset, save=path)
        figures[f"{style}_fixed_effects"] = path

        path = out / f"{style}_11_instrument_count.png"
        instrument_count_plot(instr, style=style, preset=preset, save=path)
        figures[f"{style}_instrument_count"] = path

        path = out / f"{style}_12_hansen_ar.png"
        hansen_ar_diagnostic_plot(
            {"Hansen": 0.19, "Sargan": 0.09, "AR(1)": 0.08, "AR(2)": 0.32},
            style=style,
            preset=preset,
            save=path,
        )
        figures[f"{style}_hansen_ar"] = path

        path = out / f"{style}_13_counterfactual.png"
        counterfactual_scenario_plot(
            scenario,
            time="year",
            y="pred",
            scenario="scenario",
            style=style,
            preset=preset,
            save=path,
        )
        figures[f"{style}_counterfactual"] = path

        path = out / f"{style}_14_surface_3d.png"
        surface_3d_plot(surface, x="techshare", y="polity", z="pred", style=style, preset=preset, save=path)
        figures[f"{style}_surface_3d"] = path

    gallery = export_postestimation_gallery(
        figures,
        output_html=out / "gallery.html",
        title="systemgmmkit post-estimation graphics gallery",
        description="Stata-style, journal-style, and dashboard-style post-estimation graphics.",
    )

    print(f"Wrote figures to: {out.resolve()}")
    print(f"Wrote gallery to: {gallery.resolve()}")


if __name__ == "__main__":
    main()

