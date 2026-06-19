from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from systemgmmkit.postestimation import (
    InstrumentArchitecture,
    attach_plot_accessor,
    export_sgm_viz_report,
    model_comparison_dashboard_v2,
    plot_accessor,
)


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

    estimator = "System GMM"
    nobs = 1248
    groups = 96
    instruments = 8
    collapsed = True
    transformation = "FOD"
    covariance_type = "Windmeijer two-step robust"

    hansen_p = 0.160
    sargan_p = 0.088
    ar1_p = 0.080
    ar2_p = 0.868


def main() -> None:
    out = Path("outputs/sgm_viz_result_integration")
    out.mkdir(parents=True, exist_ok=True)

    result = DemoResult()

    architecture = InstrumentArchitecture(
        estimator="System GMM",
        difference_equation=("L2.growth", "L3.growth", "L2.techshare"),
        level_equation=("D.growth",),
        standard_instruments=("polity", "fragility", "time effects"),
        lag_range=(2, 3),
        collapsed=True,
        transformation="FOD",
        total_instruments=8,
        groups=96,
    )

    # Explicit accessor pattern
    viz = plot_accessor(result)

    fig = viz.health(save=out / "01_health.png")
    plt.close(fig)

    fig = viz.persistence(save=out / "02_persistence.png")
    plt.close(fig)

    fig = viz.instruments(architecture=architecture, save=out / "03_instruments.png")
    plt.close(fig)

    fig = viz.publication_panel(architecture=architecture, save=out / "04_publication_panel.png")
    plt.close(fig)

    # Optional instance attachment pattern
    attach_plot_accessor(result)
    if hasattr(result, "plot"):
        fig = result.plot.publication_panel(
            architecture=architecture, save=out / "05_result_dot_plot_panel.png"
        )
        plt.close(fig)

    # One-command export pattern
    export_sgm_viz_report(
        result,
        out / "report",
        prefix="demo",
        architecture=architecture,
        include_gallery=True,
    )

    # Multi-model comparison pattern
    fig = model_comparison_dashboard_v2(
        [result, result],
        labels=["baseline", "robustness"],
        save=out / "06_model_comparison.png",
    )
    plt.close(fig)

    print(f"Wrote result integration outputs to: {out.resolve()}")


if __name__ == "__main__":
    main()
