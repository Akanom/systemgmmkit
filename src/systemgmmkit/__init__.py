"""Generic panel-data workflow helpers for FE and Difference/System GMM."""

from .diagnostics import DiagnosticCheck, DiagnosticReport, assess_diagnostics
from .fixed_effects import (
    FixedEffectsResult,
    FixedEffectsSpec,
    run_fixed_effects,
    run_fixed_effects_native,
)
from .presets import (
    build_difference_gmm_spec,
    build_dynamic_panel_gmm_spec,
    build_fixed_effects_spec,
    build_panel_model_suite,
    build_system_gmm_spec,
)
from .pydynpd_backend import build_pydynpd_command, run_pydynpd
from .reporting import model_card_markdown
from .spec import DynamicPanelSpec, GMMStyle, IVStyle
from .suite import PanelModelSuite, PanelModelSuiteResult, run_panel_model_suite
from .validation import PanelValidationReport, validate_panel

__all__ = [
    "DiagnosticCheck",
    "DiagnosticReport",
    "DynamicPanelSpec",
    "FixedEffectsResult",
    "FixedEffectsSpec",
    "GMMStyle",
    "IVStyle",
    "PanelModelSuite",
    "PanelModelSuiteResult",
    "PanelValidationReport",
    "assess_diagnostics",
    "build_difference_gmm_spec",
    "build_dynamic_panel_gmm_spec",
    "build_fixed_effects_spec",
    "build_panel_model_suite",
    "build_pydynpd_command",
    "build_system_gmm_spec",
    "model_card_markdown",
    "run_fixed_effects",
    "run_fixed_effects_native",
    "run_panel_model_suite",
    "run_pydynpd",
    "validate_panel",
]

__version__ = "0.3.0"
