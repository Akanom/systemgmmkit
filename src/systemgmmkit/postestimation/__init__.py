"""
High-quality post-estimation graphics for systemgmmkit.

Styles:
- stata: econometrician-friendly, Stata-inspired
- journal: publication-grade academic graphics
- dashboard: executive / PowerBI / Tableau-style graphics
"""

from .plots import (
    PlotTheme,
    available_styles,
    coefficient_plot,
    marginal_effects_plot,
    margins_prediction_plot,
    interaction_plot,
    conditional_effects_plot,
    residuals_vs_fitted_plot,
    qq_residual_plot,
    residual_histogram,
    fixed_effects_plot,
    panel_spaghetti_plot,
    instrument_count_plot,
    hansen_ar_diagnostic_plot,
    counterfactual_scenario_plot,
    surface_3d_plot,
    plot_all_diagnostics,
    export_postestimation_gallery,
)

__all__ = [
    "PlotTheme",
    "available_styles",
    "coefficient_plot",
    "marginal_effects_plot",
    "margins_prediction_plot",
    "interaction_plot",
    "conditional_effects_plot",
    "residuals_vs_fitted_plot",
    "qq_residual_plot",
    "residual_histogram",
    "fixed_effects_plot",
    "panel_spaghetti_plot",
    "instrument_count_plot",
    "hansen_ar_diagnostic_plot",
    "counterfactual_scenario_plot",
    "surface_3d_plot",
    "plot_all_diagnostics",
    "export_postestimation_gallery",
]

# Backward-compatible inference helpers
def confint(result, level=0.95):
    from .plots import _ci
    return _ci(result, level=level)

# -------------------------------------------------------------------
# Backward-compatible post-estimation API
# -------------------------------------------------------------------

def _get_result_attr(result, names, default=None):
    for name in names:
        if isinstance(result, dict) and name in result:
            return result[name]
        if hasattr(result, name):
            return getattr(result, name)
    return default


def confint(result, level=0.95):
    from .plots import _ci
    return _ci(result, level=level)


def vcov(result):
    value = _get_result_attr(result, ["cov", "covariance", "vcov", "cov_params"])
    if callable(value):
        return value()
    if value is None:
        raise AttributeError("Result object does not expose a covariance matrix.")
    return value


def fitted_values(result):
    value = _get_result_attr(result, ["fitted_values", "fittedvalues", "fitted"])
    if value is None:
        raise AttributeError("Result object does not expose fitted values.")
    return value


def residuals(result):
    value = _get_result_attr(result, ["residuals", "resid", "errors"])
    if value is None:
        raise AttributeError("Result object does not expose residuals.")
    return value


def predict(result, data=None, **kwargs):
    fn = _get_result_attr(result, ["predict"])
    if callable(fn):
        if data is None:
            return fn(**kwargs)
        return fn(data, **kwargs)

    fitted = _get_result_attr(result, ["fitted_values", "fittedvalues", "fitted"])
    if data is None and fitted is not None:
        return fitted

    raise AttributeError("Result object does not expose predict().")


def lincom(result, expression, **kwargs):
    fn = _get_result_attr(result, ["lincom"])
    if callable(fn):
        return fn(expression, **kwargs)
    raise NotImplementedError("lincom is not available for this result object.")


def wald_test(result, constraints=None, **kwargs):
    fn = _get_result_attr(result, ["wald_test", "wald"])
    if callable(fn):
        if constraints is None:
            return fn(**kwargs)
        return fn(constraints, **kwargs)
    raise NotImplementedError("wald_test is not available for this result object.")


def marginal_effects(result, *args, **kwargs):
    fn = _get_result_attr(result, ["marginal_effects", "get_margeff"])
    if callable(fn):
        return fn(*args, **kwargs)
    raise NotImplementedError("marginal_effects is not available for this result object.")
