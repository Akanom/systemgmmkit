"""Generic panel-data workflow helpers for FE, RE, IV/2SLS, and Difference/System GMM."""

from .diagnostics import DiagnosticCheck, DiagnosticReport, assess_diagnostics
from .fixed_effects import (
    FixedEffectsResult,
    FixedEffectsSpec,
    run_fixed_effects,
    run_fixed_effects_native,
)
from .native_gmm import NativeGMMResult, run_native_dynamic_panel_gmm
from .panel_iv import PanelIVResult, PanelIVSpec, run_panel_2sls
from .parity import stata_xtabond2_command, stata_xtreg_fe_command, write_stata_parity_do_file
from .presets import (
    build_difference_gmm_spec,
    build_dynamic_panel_gmm_spec,
    build_fixed_effects_spec,
    build_panel_model_suite,
    build_system_gmm_spec,
)
from .pydynpd_backend import PydynpdGMMResult, build_pydynpd_command, run_pydynpd
from .random_effects import RandomEffectsResult, RandomEffectsSpec, run_random_effects
from .reporting import model_card_markdown
from .spec import DynamicPanelSpec, GMMStyle, IVStyle
from .suite import PanelModelSuite, PanelModelSuiteResult, run_panel_model_suite
from .tables import combine_result_frames, export_regression_table, result_to_frame
from .validation import PanelValidationReport, validate_panel

__all__ = [
    "DiagnosticCheck",
    "DiagnosticReport",
    "DynamicPanelSpec",
    "FixedEffectsResult",
    "FixedEffectsSpec",
    "GMMStyle",
    "IVStyle",
    "NativeGMMResult",
    "PanelIVResult",
    "PanelIVSpec",
    "PanelModelSuite",
    "PanelModelSuiteResult",
    "PanelValidationReport",
    "PydynpdGMMResult",
    "RandomEffectsResult",
    "RandomEffectsSpec",
    "assess_diagnostics",
    "build_difference_gmm_spec",
    "build_dynamic_panel_gmm_spec",
    "build_fixed_effects_spec",
    "build_panel_model_suite",
    "build_pydynpd_command",
    "build_system_gmm_spec",
    "combine_result_frames",
    "export_regression_table",
    "model_card_markdown",
    "result_to_frame",
    "run_fixed_effects",
    "run_fixed_effects_native",
    "run_native_dynamic_panel_gmm",
    "run_panel_2sls",
    "run_panel_model_suite",
    "run_pydynpd",
    "run_random_effects",
    "stata_xtabond2_command",
    "stata_xtreg_fe_command",
    "validate_panel",
    "write_stata_parity_do_file",
    "DynamicPanelBackendError",
    "run_dynamic_panel_gmm",
    "run_system_gmm",
    "run_difference_gmm",
    "FirstDifferenceResult",
    "ParityReport",
    "ParityResult",
    "classify_parity_result",
    "first_difference",
    "LinearModelResult",
    "OLSSpec",
    "PooledOLSSpec",
    "run_ols",
    "run_pooled_ols",
    "confint",
    "fitted_values",
    "lincom",
    "marginal_effects",
    "predict",
    "residuals",
    "vcov",
    "wald_test",
    "PlotTheme",
    "available_styles",
    "coefficient_plot",
    "conditional_effects_plot",
    "counterfactual_scenario_plot",
    "dynamic_persistence_plot",
    "effect_surface_plot",
    "export_postestimation_gallery",
    "fixed_effects_plot",
    "hansen_ar_diagnostic_plot",
    "instrument_architecture_plot",
    "instrument_count_plot",
    "interaction_plot",
    "marginal_effects_plot",
    "margins_prediction_plot",
    "model_health_panel",
    "panel_spaghetti_plot",
    "parameter_impact_plot",
    "plot_all_diagnostics",
    "qq_residual_plot",
    "residual_histogram",
    "residuals_vs_fitted_plot",
    "sgm_plot_bundle",
    "surface_3d_plot",
    "HealthMetrics",
    "InstrumentArchitecture",
    "PersistenceAnalytics",
    "SGMVizAccessor",
    "dynamic_persistence_dashboard_v2",
    "effect_surface_dashboard_v2",
    "export_sgm_viz_v2_gallery",
    "health_dashboard",
    "instrument_architecture_dashboard_v2",
    "instrument_dashboard",
    "model_health_dashboard_v2",
    "persistence_dashboard",
    "publication_panel_v2",
    "sgm_viz",
    "ResultPlotAccessor",
    "attach_plot_accessor",
    "export_sgm_viz_report",
    "extract_health_metrics",
    "extract_instrument_architecture",
    "infer_persistence_phi",
    "install_result_plot_accessors",
    "model_comparison_dashboard_v2",
    "plot_accessor",
]

__version__ = "0.5.11"

import contextlib

from .dynamic_panel import (
    DynamicPanelBackendError,
    run_difference_gmm,
    run_dynamic_panel_gmm,
    run_system_gmm,
)

with contextlib.suppress(Exception):
    from .estimators.first_difference import FirstDifferenceResult, first_difference

with contextlib.suppress(Exception):
    from .reporting import ParityReport, ParityResult, classify_parity_result

from .estimators.first_difference import FirstDifferenceResult, first_difference

# Public OLS and post-estimation API
from .linear import LinearModelResult, OLSSpec, PooledOLSSpec, run_ols, run_pooled_ols
from .postestimation import (
    confint,
    fitted_values,
    lincom,
    marginal_effects,
    predict,
    residuals,
    vcov,
    wald_test,
)

# High-quality post-estimation graphics API
with contextlib.suppress(Exception):
    from .postestimation import (
        PlotTheme,
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


# SGM-Viz v2 flagship visualization API
with contextlib.suppress(Exception):
    from .postestimation import (
        HealthMetrics,
        InstrumentArchitecture,
        PersistenceAnalytics,
        SGMVizAccessor,
        dynamic_persistence_dashboard_v2,
        effect_surface_dashboard_v2,
        export_sgm_viz_v2_gallery,
        health_dashboard,
        instrument_architecture_dashboard_v2,
        instrument_dashboard,
        model_health_dashboard_v2,
        persistence_dashboard,
        publication_panel_v2,
        sgm_viz,
    )


# SGM-Viz result-object plotting integration
try:
    from .postestimation import (
        ResultPlotAccessor,
        attach_plot_accessor,
        export_sgm_viz_report,
        extract_health_metrics,
        extract_instrument_architecture,
        infer_persistence_phi,
        install_result_plot_accessors,
        model_comparison_dashboard_v2,
        plot_accessor,
    )

    install_result_plot_accessors()
except Exception:
    pass

