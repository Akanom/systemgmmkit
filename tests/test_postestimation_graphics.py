import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from systemgmmkit.postestimation import (
    available_styles,
    coefficient_plot,
    conditional_effects_plot,
    counterfactual_scenario_plot,
    dynamic_persistence_plot,
    effect_surface_plot,
    export_postestimation_gallery,
    fixed_effects_plot,
    hansen_ar_diagnostic_plot,
    instrument_architecture_plot,
    instrument_count_plot,
    interaction_plot,
    marginal_effects_plot,
    margins_prediction_plot,
    model_health_panel,
    panel_spaghetti_plot,
    parameter_impact_plot,
    plot_all_diagnostics,
    qq_residual_plot,
    residual_histogram,
    residuals_vs_fitted_plot,
    sgm_plot_bundle,
    surface_3d_plot,
)


class DummyResult:
    params = pd.Series(
        {
            "L1.y": 0.6177,
            "techshare": 0.161,
            "polity": 0.052,
            "fragility": -0.118,
            "techshare:polity": 0.041,
            "techshare:fragility": -0.029,
            "_con": 0.078,
        }
    )

    std_errors = pd.Series(
        {
            "L1.y": 0.065,
            "techshare": 0.050,
            "polity": 0.021,
            "fragility": 0.038,
            "techshare:polity": 0.014,
            "techshare:fragility": 0.013,
            "_con": 0.018,
        }
    )

    rng = np.random.default_rng(123)
    fitted_values = np.linspace(-2.0, 2.0, 120)
    residuals = rng.normal(0, 0.8, 120)

    hansen_p = 0.160
    sargan_p = 0.088
    ar1_p = 0.080
    ar2_p = 0.868


def test_available_styles():
    assert available_styles() == ["sgm", "stata", "journal", "dashboard"]


def test_high_quality_postestimation_plots_smoke(tmp_path):
    result = DummyResult()

    effects = pd.DataFrame(
        {
            "term": ["techshare", "polity", "fragility"],
            "effect": [0.18, 0.04, -0.08],
            "std_error": [0.04, 0.02, 0.03],
        }
    )

    grid = pd.DataFrame(
        {
            "techshare": np.tile(np.linspace(0, 1, 25), 3),
            "pred": np.r_[
                np.linspace(-1.0, 0.6, 25),
                np.linspace(-0.4, 1.0, 25),
                np.linspace(0.2, 1.5, 25),
            ],
            "lo": np.r_[
                np.linspace(-1.2, 0.4, 25),
                np.linspace(-0.6, 0.8, 25),
                np.linspace(0.0, 1.3, 25),
            ],
            "hi": np.r_[
                np.linspace(-0.8, 0.8, 25),
                np.linspace(-0.2, 1.2, 25),
                np.linspace(0.4, 1.7, 25),
            ],
            "condition": ["Low polity"] * 25 + ["Mean polity"] * 25 + ["High polity"] * 25,
        }
    )

    fe = pd.DataFrame(
        {
            "entity": ["Nigeria", "Ghana", "Kenya", "Ethiopia", "Rwanda", "Tanzania"],
            "effect": [0.8, -0.35, 0.1, -0.15, 0.35, 0.05],
            "std_error": [0.22, 0.18, 0.13, 0.16, 0.19, 0.12],
        }
    )

    rng = np.random.default_rng(321)
    panel = pd.DataFrame(
        {
            "country": np.repeat(["Nigeria", "Ghana", "Kenya", "Ethiopia"], 12),
            "year": list(range(2000, 2012)) * 4,
            "growth": rng.normal(0.2, 0.8, 48).cumsum(),
        }
    )

    instr = pd.DataFrame(
        {
            "lag": range(1, 8),
            "instruments": [12, 38, 66, 84, 77, 56, 39],
        }
    )

    scen = pd.DataFrame(
        {
            "year": list(range(2000, 2010)) * 3,
            "pred": np.r_[
                np.linspace(-1, 0.5, 10), np.linspace(-0.5, 1.2, 10), np.linspace(0, 1.8, 10)
            ],
            "scenario": ["Baseline"] * 10 + ["High techshare"] * 10 + ["High institutions"] * 10,
        }
    )

    surface = pd.DataFrame(
        {
            "techshare": np.repeat(np.linspace(0, 1, 10), 10),
            "polity": np.tile(np.linspace(-2, 2, 10), 10),
        }
    )
    surface["pred"] = (
        -0.4
        + surface["techshare"]
        + 0.25 * surface["polity"]
        + 0.35 * surface["techshare"] * surface["polity"]
    )

    for style in ["sgm", "stata", "journal", "dashboard"]:
        coefficient_plot(result, style=style, save=tmp_path / f"{style}_coef.png")
        parameter_impact_plot(result, style=style, save=tmp_path / f"{style}_parameter_impact.png")
        marginal_effects_plot(effects, style=style, save=tmp_path / f"{style}_me.png")
        margins_prediction_plot(
            grid, x="techshare", y="pred", lower="lo", upper="hi", group="condition", style=style
        )
        interaction_plot(grid, x="techshare", y="pred", moderator="condition", style=style)
        conditional_effects_plot(
            grid,
            x="techshare",
            effect="pred",
            condition="condition",
            lower="lo",
            upper="hi",
            style=style,
        )
        residuals_vs_fitted_plot(result, style=style)
        qq_residual_plot(result.residuals, style=style)
        residual_histogram(result.residuals, style=style)
        fixed_effects_plot(fe, style=style)
        panel_spaghetti_plot(
            panel,
            entity="country",
            time="year",
            y="growth",
            highlight=["Nigeria", "Ghana"],
            style=style,
        )
        instrument_count_plot(instr, style=style)
        instrument_architecture_plot(instr, style=style)
        hansen_ar_diagnostic_plot(
            {"Hansen": 0.16, "Sargan": 0.088, "AR(1)": 0.08, "AR(2)": 0.868}, style=style
        )
        model_health_panel(
            {"Hansen": 0.16, "Sargan": 0.088, "AR(1)": 0.08, "AR(2)": 0.868}, style=style
        )
        counterfactual_scenario_plot(scen, time="year", y="pred", scenario="scenario", style=style)
        surface_3d_plot(surface, x="techshare", y="polity", z="pred", style=style)
        effect_surface_plot(surface, x="techshare", y="polity", z="pred", style=style)
        dynamic_persistence_plot(0.62, style=style)
        plt.close("all")

    saved = plot_all_diagnostics(result, output_dir=tmp_path, style="sgm", prefix="dummy")
    plt.close("all")
    assert "coefplot" in saved
    assert "hansen_ar" in saved

    bundle = sgm_plot_bundle(result, output_dir=tmp_path / "bundle", prefix="sgm")
    plt.close("all")
    assert "coefplot" in bundle

    gallery = export_postestimation_gallery(saved, output_html=tmp_path / "gallery.html")
    plt.close("all")
    assert gallery.exists()
    assert (tmp_path / "journal_coef.png").exists()
    assert (tmp_path / "journal_me.png").exists()
