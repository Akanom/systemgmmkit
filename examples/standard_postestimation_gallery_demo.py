from pathlib import Path

import numpy as np
import pandas as pd

from systemgmmkit.postestimation import export_standard_postestimation_gallery


class DemoResult:
    params = pd.Series(
        {
            "L1.growth": 0.618,
            "techshare": 0.160,
            "polity": 0.052,
            "fragility": -0.118,
            "techshare:polity": 0.041,
            "techshare:fragility": -0.029,
        }
    )

    std_errors = pd.Series(
        {
            "L1.growth": 0.065,
            "techshare": 0.050,
            "polity": 0.021,
            "fragility": 0.038,
            "techshare:polity": 0.014,
            "techshare:fragility": 0.013,
        }
    )

    rng = np.random.default_rng(42)
    fitted_values = np.linspace(-2, 2, 160)
    residuals = rng.normal(0, 0.8, 160)

    hansen_p = 0.160
    sargan_p = 0.088
    ar1_p = 0.080
    ar2_p = 0.868


def main() -> None:
    out = Path("outputs/standard_postestimation_gallery")

    rng = np.random.default_rng(7)
    result = DemoResult()

    effects = pd.DataFrame(
        {
            "term": ["techshare", "polity", "fragility"],
            "effect": [0.18, 0.04, -0.09],
            "std_error": [0.04, 0.02, 0.03],
        }
    )

    grid = pd.DataFrame(
        {
            "x": np.tile(np.linspace(0, 1, 50), 3),
            "y": np.r_[
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
            "group": ["Low polity"] * 50 + ["Mean polity"] * 50 + ["High polity"] * 50,
            "condition": ["Low polity"] * 50 + ["Mean polity"] * 50 + ["High polity"] * 50,
            "effect": np.r_[
                np.linspace(-0.4, -0.2, 50),
                np.linspace(0.0, 0.3, 50),
                np.linspace(0.4, 1.0, 50),
            ],
        }
    )

    countries = ["Nigeria", "Ghana", "Kenya", "Ethiopia", "Rwanda", "Tanzania"]
    panel = pd.DataFrame(
        {
            "entity": np.repeat(countries, 21),
            "time": list(range(2000, 2021)) * len(countries),
            "growth": rng.normal(0.15, 0.75, 21 * len(countries)).cumsum(),
        }
    )

    fixed_effects = pd.DataFrame(
        {
            "entity": ["Nigeria", "Ghana", "Kenya", "Ethiopia", "Rwanda", "Tanzania"],
            "effect": [0.80, -0.35, 0.10, -0.15, 0.35, 0.05],
            "std_error": [0.22, 0.18, 0.13, 0.16, 0.19, 0.12],
        }
    )

    instruments = pd.DataFrame(
        {
            "lag": range(1, 9),
            "instruments": [12, 45, 70, 82, 90, 76, 55, 40],
        }
    )

    counterfactual = pd.DataFrame(
        {
            "time": list(range(2000, 2021)) * 3,
            "y": np.r_[
                np.linspace(-1.2, 0.8, 21),
                np.linspace(-0.8, 1.5, 21),
                np.linspace(-0.4, 2.0, 21),
            ],
            "scenario": ["Baseline"] * 21 + ["High techshare"] * 21 + ["High institutions"] * 21,
        }
    )

    surface = pd.DataFrame(
        {
            "x": np.repeat(np.linspace(0, 1, 22), 22),
            "z": np.tile(np.linspace(-2, 2, 22), 22),
        }
    )
    surface["y"] = (
        -0.4
        + 1.1 * surface["x"]
        + 0.25 * surface["z"]
        + 0.35 * surface["x"] * surface["z"]
        - 0.25 * surface["x"] ** 2
    )

    gallery = export_standard_postestimation_gallery(
        result,
        output_dir=out,
        prefix="demo",
        effects=effects,
        margins=grid,
        conditional=grid,
        interaction=grid,
        panel=panel,
        fixed_effects=fixed_effects,
        instruments=instruments,
        counterfactual=counterfactual,
        surface={"data": surface, "x": "x", "y": "z", "z": "y"},
        entity="entity",
        time="time",
        outcome="growth",
        x="x",
        y="y",
        lower="lo",
        upper="hi",
        group="group",
        effect="effect",
        condition="condition",
        scenario="scenario",
        title="Standard post-estimation plot gallery",
        description="R/Stata/Java-style gallery of standard post-estimation graphics.",
    )

    print(f"Wrote standard gallery to: {gallery.gallery.resolve()}")
    print(f"Wrote {len(gallery.figures)} figures.")
    if gallery.skipped:
        print("Skipped:", gallery.skipped)


if __name__ == "__main__":
    main()
