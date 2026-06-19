import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from systemgmmkit.postestimation import (
    HealthMetrics,
    InstrumentArchitecture,
    PersistenceAnalytics,
    model_health_dashboard_v2,
    dynamic_persistence_dashboard_v2,
    instrument_architecture_dashboard_v2,
    effect_surface_dashboard_v2,
    publication_panel_v2,
    export_sgm_viz_v2_gallery,
    sgm_viz,
)


class DummyResult:
    params = pd.Series(
        {
            "L1.y": 0.618,
            "x": 1.2,
            "w": -0.4,
        }
    )
    std_errors = pd.Series(
        {
            "L1.y": 0.065,
            "x": 0.30,
            "w": 0.08,
        }
    )
    estimator = "System GMM"
    nobs = 1248
    groups = 96
    instruments = 8
    collapsed = True
    hansen_p = 0.160
    sargan_p = 0.088
    ar1_p = 0.080
    ar2_p = 0.868


def test_persistence_analytics():
    a = PersistenceAnalytics.from_phi(0.618)
    assert a.stable is True
    assert a.long_run_multiplier is not None
    assert a.persistence_class in {"High", "Moderate", "Low", "Very high"}


def test_sgm_viz_v2_figures_save(tmp_path):
    metrics = HealthMetrics(
        estimator="System GMM",
        nobs=1248,
        groups=96,
        instruments=8,
        hansen_p=0.160,
        sargan_p=0.088,
        ar1_p=0.080,
        ar2_p=0.868,
        collapsed=True,
    )

    arch = InstrumentArchitecture(
        estimator="System GMM",
        difference_equation=("L2.y", "L3.y"),
        level_equation=("D.y",),
        standard_instruments=("x", "w"),
        lag_range=(2, 3),
        collapsed=True,
        transformation="FOD",
        total_instruments=8,
        groups=96,
    )

    figs = {}
    paths = {}

    paths["health"] = tmp_path / "health.png"
    figs["health"] = model_health_dashboard_v2(metrics, save=paths["health"])

    paths["persistence"] = tmp_path / "persistence.svg"
    figs["persistence"] = dynamic_persistence_dashboard_v2(0.618, save=paths["persistence"])

    paths["instruments"] = tmp_path / "instruments.pdf"
    figs["instruments"] = instrument_architecture_dashboard_v2(arch, save=paths["instruments"])

    x = np.repeat(np.linspace(0, 1, 10), 10)
    y = np.tile(np.linspace(-2, 2, 10), 10)
    z = 0.5 * x + 0.2 * y + 0.3 * x * y
    paths["surface"] = tmp_path / "surface.png"
    figs["surface"] = effect_surface_dashboard_v2(x, y, z, x_label="TechShare", y_label="Polity", save=paths["surface"])

    paths["panel"] = tmp_path / "panel.png"
    figs["panel"] = publication_panel_v2(metrics=metrics, phi=0.618, instruments=arch, result=DummyResult(), save=paths["panel"])

    for fig in figs.values():
        assert fig is not None
        plt.close(fig)

    for path in paths.values():
        assert path.exists()

    gallery = export_sgm_viz_v2_gallery(paths, output_html=tmp_path / "gallery.html")
    assert gallery.exists()


def test_result_accessor(tmp_path):
    result = DummyResult()
    accessor = sgm_viz(result)

    fig = accessor.health(save=tmp_path / "accessor_health.png")
    assert fig is not None
    plt.close(fig)

    fig = accessor.persistence(save=tmp_path / "accessor_persistence.png")
    assert fig is not None
    plt.close(fig)

    fig = accessor.publication_panel(save=tmp_path / "accessor_panel.png")
    assert fig is not None
    plt.close(fig)

    assert (tmp_path / "accessor_panel.png").exists()
