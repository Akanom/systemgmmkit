from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from systemgmmkit.postestimation import (
    HealthMetrics,
    InstrumentArchitecture,
    dynamic_persistence_dashboard_v2,
    effect_surface_dashboard_v2,
    export_sgm_viz_v2_gallery,
    instrument_architecture_dashboard_v2,
    model_health_dashboard_v2,
    publication_panel_v2,
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


def main() -> None:
    out = Path("outputs/sgm_viz_v2")
    out.mkdir(parents=True, exist_ok=True)

    figures = {}

    metrics = HealthMetrics(
        estimator="System GMM",
        nobs=1248,
        groups=96,
        instruments=8,
        parameters=4,
        collapsed=True,
        transformation="FOD",
        covariance_type="Windmeijer two-step robust",
        hansen_p=0.160,
        sargan_p=0.088,
        ar1_stat=-1.752,
        ar1_p=0.080,
        ar2_stat=-0.167,
        ar2_p=0.868,
    )

    architecture = InstrumentArchitecture(
        estimator="System GMM",
        difference_equation=("L2.y", "L3.y", "L2.x"),
        level_equation=("D.y",),
        standard_instruments=("w", "time effects"),
        lag_range=(2, 3),
        collapsed=True,
        transformation="FOD",
        total_instruments=8,
        groups=96,
    )

    def save(name, fig):
        path = out / f"{name}.png"
        fig.savefig(path, dpi=300, bbox_inches="tight")
        plt.close(fig)
        figures[name] = path

    save("01_model_health_dashboard", model_health_dashboard_v2(metrics))
    save("02_dynamic_persistence_dashboard", dynamic_persistence_dashboard_v2(0.618))
    save("03_instrument_architecture_dashboard", instrument_architecture_dashboard_v2(architecture))

    x = np.repeat(np.linspace(0, 1, 24), 24)
    y = np.tile(np.linspace(-2, 2, 24), 24)
    z = -0.4 + 1.1 * x + 0.25 * y + 0.35 * x * y - 0.25 * x**2

    save(
        "04_effect_surface_dashboard",
        effect_surface_dashboard_v2(
            x,
            y,
            z,
            x_label="Technical aid share",
            y_label="Institutional quality",
            z_label="Predicted growth",
        ),
    )

    save(
        "05_publication_panel",
        publication_panel_v2(
            metrics=metrics,
            phi=0.618,
            instruments=architecture,
            result=DemoResult(),
        ),
    )

    gallery = export_sgm_viz_v2_gallery(
        figures,
        output_html=out / "gallery.html",
        title="SGM-Viz v2 demo gallery",
        description="Definition-of-Done dynamic panel graphics: health, persistence, instruments, effect surface, and publication panel.",
    )

    print(f"Wrote figures to: {out.resolve()}")
    print(f"Wrote gallery to: {gallery.resolve()}")


if __name__ == "__main__":
    main()
