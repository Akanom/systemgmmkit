import matplotlib.pyplot as plt
import pandas as pd

from systemgmmkit.postestimation import (
    HealthMetrics,
    InstrumentArchitecture,
    ResultPlotAccessor,
    attach_plot_accessor,
    export_sgm_viz_report,
    extract_health_metrics,
    extract_instrument_architecture,
    infer_persistence_phi,
    model_comparison_dashboard_v2,
    plot_accessor,
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
    transformation = "FOD"
    covariance_type = "Windmeijer"

    hansen_p = 0.160
    sargan_p = 0.088
    ar1_p = 0.080
    ar2_p = 0.868


def test_metric_and_architecture_extraction():
    result = DummyResult()

    metrics = extract_health_metrics(result)
    assert isinstance(metrics, HealthMetrics)
    assert metrics.nobs == 1248
    assert metrics.instrument_group_ratio == 8 / 96

    arch = extract_instrument_architecture(result)
    assert isinstance(arch, InstrumentArchitecture)
    assert arch.total_instruments == 8

    assert infer_persistence_phi(result) == 0.618


def test_plot_accessor_methods(tmp_path):
    result = DummyResult()
    accessor = plot_accessor(result)

    assert isinstance(accessor, ResultPlotAccessor)

    fig = accessor.health(save=tmp_path / "health.png")
    assert fig is not None
    plt.close(fig)

    fig = accessor.persistence(save=tmp_path / "persistence.png")
    assert fig is not None
    plt.close(fig)

    fig = accessor.instruments(save=tmp_path / "instruments.png")
    assert fig is not None
    plt.close(fig)

    fig = accessor.publication_panel(save=tmp_path / "panel.png")
    assert fig is not None
    plt.close(fig)

    assert (tmp_path / "panel.png").exists()


def test_attach_plot_accessor_and_export_report(tmp_path):
    result = attach_plot_accessor(DummyResult())

    if hasattr(result, "plot"):
        fig = result.plot.health(save=tmp_path / "attached_health.png")
        assert fig is not None
        plt.close(fig)

    paths = export_sgm_viz_report(
        result,
        tmp_path / "report",
        prefix="dummy",
        include_gallery=True,
    )

    assert "health_dashboard" in paths
    assert "publication_panel" in paths
    assert "manifest" in paths
    assert "gallery" in paths
    assert paths["gallery"].exists()


def test_model_comparison_dashboard(tmp_path):
    results = [DummyResult(), DummyResult()]
    fig = model_comparison_dashboard_v2(
        results,
        labels=["baseline", "robustness"],
        save=tmp_path / "comparison.png",
    )
    assert fig is not None
    plt.close(fig)
    assert (tmp_path / "comparison.png").exists()
