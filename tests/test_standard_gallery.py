import numpy as np
import pandas as pd

from systemgmmkit.postestimation import (
    export_standard_postestimation_gallery,
    plot_accessor,
)


class DummyResult:
    params = pd.Series(
        {
            "L1.y": 0.618,
            "techshare": 0.160,
            "polity": 0.052,
            "fragility": -0.118,
            "techshare:polity": 0.041,
            "techshare:fragility": -0.029,
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
        }
    )

    rng = np.random.default_rng(123)
    fitted_values = np.linspace(-2, 2, 120)
    residuals = rng.normal(0, 0.8, 120)

    hansen_p = 0.160
    sargan_p = 0.088
    ar1_p = 0.080
    ar2_p = 0.868


def make_inputs():
    rng = np.random.default_rng(321)

    effects = pd.DataFrame(
        {
            "term": ["techshare", "polity", "fragility"],
            "effect": [0.18, 0.04, -0.09],
            "std_error": [0.04, 0.02, 0.03],
        }
    )

    grid = pd.DataFrame(
        {
            "x": np.tile(np.linspace(0, 1, 30), 3),
            "y": np.r_[
                np.linspace(-1.0, 0.7, 30),
                np.linspace(-0.4, 1.0, 30),
                np.linspace(0.2, 1.6, 30),
            ],
            "lo": np.r_[
                np.linspace(-1.25, 0.45, 30),
                np.linspace(-0.65, 0.75, 30),
                np.linspace(-0.05, 1.35, 30),
            ],
            "hi": np.r_[
                np.linspace(-0.75, 0.95, 30),
                np.linspace(-0.15, 1.25, 30),
                np.linspace(0.45, 1.85, 30),
            ],
            "group": ["Low"] * 30 + ["Mean"] * 30 + ["High"] * 30,
            "condition": ["Low"] * 30 + ["Mean"] * 30 + ["High"] * 30,
            "effect": np.r_[
                np.linspace(-0.4, -0.2, 30),
                np.linspace(0.0, 0.3, 30),
                np.linspace(0.4, 1.0, 30),
            ],
        }
    )

    panel = pd.DataFrame(
        {
            "entity": np.repeat(["Nigeria", "Ghana", "Kenya", "Ethiopia"], 12),
            "time": list(range(2000, 2012)) * 4,
            "growth": rng.normal(0.2, 0.8, 48).cumsum(),
        }
    )

    fixed = pd.DataFrame(
        {
            "entity": ["Nigeria", "Ghana", "Kenya", "Ethiopia"],
            "effect": [0.8, -0.35, 0.1, -0.15],
            "std_error": [0.22, 0.18, 0.13, 0.16],
        }
    )

    instruments = pd.DataFrame(
        {
            "lag": range(1, 8),
            "instruments": [12, 38, 66, 84, 77, 56, 39],
        }
    )

    counterfactual = pd.DataFrame(
        {
            "time": list(range(2000, 2010)) * 3,
            "y": np.r_[
                np.linspace(-1, 0.5, 10),
                np.linspace(-0.5, 1.2, 10),
                np.linspace(0, 1.8, 10),
            ],
            "scenario": ["Baseline"] * 10 + ["High techshare"] * 10 + ["High institutions"] * 10,
        }
    )

    surface_data = pd.DataFrame(
        {
            "x": np.repeat(np.linspace(0, 1, 14), 14),
            "z": np.tile(np.linspace(-2, 2, 14), 14),
        }
    )
    surface_data["y"] = (
        -0.4
        + 1.1 * surface_data["x"]
        + 0.25 * surface_data["z"]
        + 0.35 * surface_data["x"] * surface_data["z"]
    )

    return {
        "effects": effects,
        "margins": grid,
        "conditional": grid,
        "interaction": grid,
        "panel": panel,
        "fixed_effects": fixed,
        "instruments": instruments,
        "counterfactual": counterfactual,
        "surface": {"data": surface_data, "x": "x", "y": "z", "z": "y"},
    }


def test_standard_gallery_exports_all_core_plots(tmp_path):
    result = DummyResult()
    inputs = make_inputs()

    gallery = export_standard_postestimation_gallery(
        result,
        output_dir=tmp_path,
        prefix="dummy",
        outcome="growth",
        **inputs,
    )

    assert gallery.gallery is not None
    assert gallery.gallery.exists()
    assert len(gallery.figures) >= 14
    assert "coefficient_plot" in gallery.figures
    assert "hansen_ar_diagnostic_plot" in gallery.figures


def test_result_plot_standard_gallery_accessor(tmp_path):
    result = DummyResult()
    inputs = make_inputs()

    gallery = plot_accessor(result).standard_gallery(
        tmp_path,
        prefix="accessor",
        outcome="growth",
        **inputs,
    )

    assert gallery.gallery is not None
    assert gallery.gallery.exists()
    assert len(gallery.figures) >= 14
