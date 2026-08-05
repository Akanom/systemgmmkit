"""Generic panel-data workflow helpers for FE, RE, IV/2SLS, and Difference/System GMM."""

from contextlib import suppress as _suppress

from . import postestimation as _postestimation
from .diagnostics import DiagnosticCheck, DiagnosticReport, assess_diagnostics
from .dynamic_panel import (
    DynamicPanelBackendError,
    run_difference_gmm,
    run_dynamic_panel_gmm,
    run_system_gmm,
)
from .easy import DynamicGMMWorkflowResult, difference_gmm, system_gmm
from .estimators.first_difference import FirstDifferenceResult, first_difference
from .fixed_effects import (
    FixedEffectsResult,
    FixedEffectsSpec,
    run_fixed_effects,
    run_fixed_effects_native,
)
from .integrations import add_to_outputhub, outputhub_diagnostics_frame, to_outputhub_model
from .linear import LinearModelResult, OLSSpec, PooledOLSSpec, run_ols, run_pooled_ols
from .ml import (
    ForecastSummary,
    MLWorkflowSummary,
    PostEstimationSummary,
    auto_dynamic_gmm,
    quick_forecast,
    quick_ml,
    quick_postestimation,
)
from .native_gmm import NativeGMMResult, run_native_dynamic_panel_gmm
from .panel_iv import PanelIVResult, PanelIVSpec, run_panel_2sls
from .parity import stata_xtabond2_command, stata_xtreg_fe_command, write_stata_parity_do_file
from .postestimation import (
    confint,
    estat_vce,
    fitted_values,
    lincom,
    marginal_effects,
    margins,
    predict,
    predict_stata,
    residuals,
    vcov,
    wald_test,
)
from .presets import (
    build_difference_gmm_spec,
    build_dynamic_panel_gmm_spec,
    build_fixed_effects_spec,
    build_panel_model_suite,
    build_system_gmm_spec,
)
from .pydynpd_backend import PydynpdGMMResult, build_pydynpd_command, run_pydynpd
from .random_effects import RandomEffectsResult, RandomEffectsSpec, run_random_effects
from .reporting import (
    ParityReport,
    ParityResult,
    classify_parity_result,
    model_card_markdown,
)
from .spec import DynamicPanelSpec, GMMStyle, IVStyle
from .suite import PanelModelSuite, PanelModelSuiteResult, run_panel_model_suite
from .tables import (
    combine_result_frames,
    export_regression_table,
    format_inference_frame,
    result_to_frame,
)
from .validation import PanelValidationReport, validate_panel

# Keep wildcard imports dependency-free and focused on the documented estimator,
# workflow, diagnostics, reporting, and post-estimation surface. Plotting remains
# available through ``systemgmmkit.postestimation`` and through the legacy lazy
# root aliases handled by ``__getattr__`` below.
__all__ = [
    "DiagnosticCheck",
    "DiagnosticReport",
    "DynamicGMMWorkflowResult",
    "DynamicPanelBackendError",
    "DynamicPanelSpec",
    "FirstDifferenceResult",
    "FixedEffectsResult",
    "FixedEffectsSpec",
    "ForecastSummary",
    "GMMStyle",
    "IVStyle",
    "LinearModelResult",
    "MLWorkflowSummary",
    "NativeGMMResult",
    "OLSSpec",
    "PanelIVResult",
    "PanelIVSpec",
    "PanelModelSuite",
    "PanelModelSuiteResult",
    "PanelValidationReport",
    "ParityReport",
    "ParityResult",
    "PostEstimationSummary",
    "PooledOLSSpec",
    "PydynpdGMMResult",
    "RandomEffectsResult",
    "RandomEffectsSpec",
    "add_to_outputhub",
    "assess_diagnostics",
    "auto_dynamic_gmm",
    "build_difference_gmm_spec",
    "build_dynamic_panel_gmm_spec",
    "build_fixed_effects_spec",
    "build_panel_model_suite",
    "build_pydynpd_command",
    "build_system_gmm_spec",
    "classify_parity_result",
    "combine_result_frames",
    "confint",
    "difference_gmm",
    "estat_vce",
    "export_regression_table",
    "first_difference",
    "fitted_values",
    "format_inference_frame",
    "lincom",
    "marginal_effects",
    "margins",
    "model_card_markdown",
    "outputhub_diagnostics_frame",
    "predict",
    "predict_stata",
    "quick_forecast",
    "quick_ml",
    "quick_postestimation",
    "residuals",
    "result_to_frame",
    "run_difference_gmm",
    "run_dynamic_panel_gmm",
    "run_fixed_effects",
    "run_fixed_effects_native",
    "run_native_dynamic_panel_gmm",
    "run_ols",
    "run_panel_2sls",
    "run_panel_model_suite",
    "run_pooled_ols",
    "run_pydynpd",
    "run_random_effects",
    "run_system_gmm",
    "stata_xtabond2_command",
    "stata_xtreg_fe_command",
    "system_gmm",
    "to_outputhub_model",
    "validate_panel",
    "vcov",
    "wald_test",
    "write_stata_parity_do_file",
]

__version__ = "0.5.14"

_OPTIONAL_PLOT_EXPORTS = frozenset(
    export for exports in _postestimation._PLOT_MODULE_EXPORTS.values() for export in exports
)


def __getattr__(name: str):
    """Resolve compatibility plotting aliases without eagerly binding them."""

    if name in _OPTIONAL_PLOT_EXPORTS:
        return getattr(_postestimation, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


# Preserve the documented ``result.plot`` convenience while keeping optional
# plotting symbols out of the root module globals. A missing plots extra remains
# non-fatal for the core package import.
with _suppress(ImportError):
    _postestimation.install_result_plot_accessors()
