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
    "run_difference_gmm",    "FirstDifferenceResult",
    "ParityReport",
    "ParityResult",
    "classify_parity_result",
    "first_difference",
]

__version__ = "0.5.9"

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




