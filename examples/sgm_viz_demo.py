from systemgmmkit.postestimation import (
    HealthMetrics,
    dynamic_persistence_dashboard,
    instrument_architecture_dashboard,
    model_health_dashboard,
    publication_panel,
)

m = HealthMetrics(
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

model_health_dashboard(
    m,
    save="outputs/sgm_health.png",
)

dynamic_persistence_dashboard(
    0.618,
    save="outputs/sgm_persistence.png",
)

instrument_architecture_dashboard(
    [1, 2, 3, 4, 5, 6],
    [8, 12, 16, 18, 20, 21],
    save="outputs/sgm_instruments.png",
)

publication_panel(
    m,
    0.618,
    [1, 2, 3, 4, 5, 6],
    [8, 12, 16, 18, 20, 21],
    save="outputs/sgm_publication_panel.png",
)

print("SGM-Viz demo complete")
