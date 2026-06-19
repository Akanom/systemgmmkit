from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np
import pandas as pd

from .plots import (
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
from .result_plot import (
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
from .sgm_viz import (
    dynamic_persistence_dashboard,
    effect_surface_dashboard,
    instrument_architecture_dashboard,
    model_health_dashboard,
    publication_panel,
)
from .sgm_viz_v2 import (
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
from .standard_gallery import (
    StandardGalleryResult,
    export_standard_postestimation_gallery,
)

__all__ = [
    "PlotTheme",
    "available_styles",
    "coefficient_plot",
    "parameter_impact_plot",
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
    "instrument_architecture_plot",
    "hansen_ar_diagnostic_plot",
    "model_health_panel",
    "counterfactual_scenario_plot",
    "surface_3d_plot",
    "effect_surface_plot",
    "dynamic_persistence_plot",
    "plot_all_diagnostics",
    "sgm_plot_bundle",
    "export_postestimation_gallery",
    "predict",
    "fitted_values",
    "residuals",
    "vcov",
    "confint",
    "lincom",
    "wald_test",
    "marginal_effects",
    "HealthMetrics",
    "InstrumentArchitecture",
    "PersistenceAnalytics",
    "SGMVizAccessor",
    "sgm_viz",
    "model_health_dashboard",
    "dynamic_persistence_dashboard",
    "instrument_architecture_dashboard",
    "effect_surface_dashboard",
    "publication_panel",
    "model_health_dashboard_v2",
    "dynamic_persistence_dashboard_v2",
    "instrument_architecture_dashboard_v2",
    "effect_surface_dashboard_v2",
    "publication_panel_v2",
    "export_sgm_viz_v2_gallery",
    "health_dashboard",
    "persistence_dashboard",
    "instrument_dashboard",
    "ResultPlotAccessor",
    "extract_health_metrics",
    "extract_instrument_architecture",
    "infer_persistence_phi",
    "plot_accessor",
    "attach_plot_accessor",
    "install_result_plot_accessors",
    "export_sgm_viz_report",
    "model_comparison_dashboard_v2",
    "StandardGalleryResult",
    "export_standard_postestimation_gallery",
]


def _attr(obj: Any, names: Sequence[str], default: Any = None) -> Any:
    for name in names:
        if hasattr(obj, name):
            return getattr(obj, name)
    return default


def _value_attr(obj: Any, names: Sequence[str], default: Any = None) -> Any:
    value = _attr(obj, names, default)
    return default if callable(value) else value


def _params_series(result: Any) -> pd.Series:
    params = _attr(result, ["params", "coefficients", "coef", "beta"])

    if params is None:
        raise AttributeError("Result object does not expose params/coefficients.")

    if isinstance(params, pd.Series):
        return params.astype(float)

    if isinstance(params, Mapping):
        return pd.Series(dict(params), dtype=float)

    arr = np.asarray(params, dtype=float).reshape(-1)
    names = _attr(result, ["param_names", "terms", "names"])

    if names is None:
        names = [f"b{i}" for i in range(arr.size)]

    return pd.Series(arr, index=list(names), dtype=float)


def _std_errors_series(result: Any, params: pd.Series) -> pd.Series:
    se = _attr(result, ["std_errors", "standard_errors", "bse", "se"])

    if se is not None:
        if isinstance(se, pd.Series):
            return se.reindex(params.index).astype(float)

        if isinstance(se, Mapping):
            return pd.Series(dict(se), dtype=float).reindex(params.index)

        arr = np.asarray(se, dtype=float).reshape(-1)
        if arr.size == params.size:
            return pd.Series(arr, index=params.index, dtype=float)

    V = _vcov_frame(result, params, allow_se_fallback=False)
    return pd.Series(np.sqrt(np.maximum(np.diag(V.to_numpy()), 0.0)), index=params.index)


def _vcov_frame(
    result: Any,
    params: pd.Series | None = None,
    *,
    allow_se_fallback: bool = True,
) -> pd.DataFrame:
    if params is None:
        params = _params_series(result)

    V = _value_attr(
        result,
        [
            "covariance",
            "cov",
            "cov_matrix",
            "variance_covariance",
            "V",
        ],
    )

    if V is None:
        cov_params = _attr(result, ["cov_params"])
        if callable(cov_params):
            V = cov_params()

    if V is None and allow_se_fallback:
        se = _std_errors_series(result, params)
        return pd.DataFrame(
            np.diag(np.square(se.to_numpy())),
            index=params.index,
            columns=params.index,
        )

    if V is None:
        raise AttributeError("Result object does not expose a variance-covariance matrix.")

    if isinstance(V, pd.DataFrame):
        return V.reindex(index=params.index, columns=params.index).astype(float)

    arr = np.asarray(V, dtype=float)

    if arr.ndim != 2 or arr.shape[0] != arr.shape[1]:
        raise ValueError("Variance-covariance matrix must be square.")

    if arr.shape[0] != params.size:
        raise ValueError(
            f"Variance-covariance matrix has shape {arr.shape}, "
            f"but result has {params.size} parameters."
        )

    return pd.DataFrame(arr, index=params.index, columns=params.index)


def _normal_crit(alpha: float = 0.05) -> float:
    try:
        from scipy import stats

        return float(stats.norm.ppf(1.0 - alpha / 2.0))
    except Exception:
        return 1.959963984540054


def _normal_pvalue(z: float) -> float:
    z = float(z)
    if not math.isfinite(z):
        return float("nan")
    return float(2.0 * (1.0 - 0.5 * (1.0 + math.erf(abs(z) / math.sqrt(2.0)))))


def predict(result: Any, data: Any | None = None, **kwargs: Any) -> Any:
    fn = _attr(result, ["predict"])

    if callable(fn):
        if data is None:
            return fn(**kwargs)
        return fn(data, **kwargs)

    fit = fitted_values(result)
    if data is not None:
        raise NotImplementedError("This result object does not support out-of-sample prediction.")
    return fit


def fitted_values(result: Any, **kwargs: Any) -> Any:
    value = _value_attr(
        result,
        [
            "fitted",
            "fittedvalues",
            "yhat",
            "predicted",
            "predictions",
        ],
    )

    if value is not None:
        return value

    return predict(result, **kwargs)


def residuals(result: Any) -> Any:
    value = _value_attr(
        result,
        [
            "resid",
            "residual",
            "residual_values",
            "errors",
            "uhat",
        ],
    )

    if value is not None:
        return value

    data = _value_attr(result, ["data", "df", "model_data"])
    spec = _value_attr(result, ["spec"])
    dep = _value_attr(spec, ["dependent", "depvar", "y"]) if spec is not None else None

    if data is not None and dep is not None and dep in data:
        return data[dep] - fitted_values(result)

    # Last fallback: only call a residuals method if no non-callable residual
    # storage exists. This preserves compatibility with result objects that
    # implement their own residual computation.
    fn = _attr(result, ["residuals"])
    if callable(fn):
        return fn()

    raise AttributeError("Result object does not expose residuals.")


def vcov(result: Any) -> pd.DataFrame:
    return _vcov_frame(result)


def confint(result: Any, alpha: float = 0.05) -> pd.DataFrame:
    params = _params_series(result)
    se = _std_errors_series(result, params)
    crit = _normal_crit(alpha)

    out = pd.DataFrame(
        {
            "lower": params - crit * se,
            "upper": params + crit * se,
        }
    )
    out.index.name = "term"
    return out


def lincom(
    result: Any,
    expression: Mapping[str, float] | Sequence[float] | None = None,
    *,
    weights: Mapping[str, float] | Sequence[float] | None = None,
    value: float = 0.0,
    alpha: float = 0.05,
    **kwargs: Any,
) -> dict[str, float]:
    if expression is None:
        expression = weights

    if expression is None:
        raise TypeError("lincom() requires an expression or weights argument.")

    params = _params_series(result)
    V = _vcov_frame(result, params)

    if isinstance(expression, Mapping):
        w = pd.Series(0.0, index=params.index, dtype=float)
        for name, weight in expression.items():
            if name not in w.index:
                raise KeyError(f"Unknown coefficient in lincom expression: {name!r}")
            w.loc[name] = float(weight)
    else:
        arr = np.asarray(expression, dtype=float).reshape(-1)
        if arr.size != params.size:
            raise ValueError(
                f"Linear-combination vector has length {arr.size}, "
                f"but result has {params.size} parameters."
            )
        w = pd.Series(arr, index=params.index, dtype=float)

    estimate = float(w.to_numpy() @ params.to_numpy())
    variance = float(w.to_numpy() @ V.loc[params.index, params.index].to_numpy() @ w.to_numpy())
    std_error = math.sqrt(max(variance, 0.0))

    statistic = float((estimate - float(value)) / std_error) if std_error > 0 else float("nan")
    p_value = _normal_pvalue(statistic)
    crit = _normal_crit(alpha)

    return {
        "estimate": estimate,
        "std_error": std_error,
        "statistic": statistic,
        "z": statistic,
        "t": statistic,
        "p_value": p_value,
        "ci_low": float(estimate - crit * std_error),
        "ci_high": float(estimate + crit * std_error),
        "value": float(value),
        "alpha": float(alpha),
    }


def wald_test(
    result: Any,
    R: Sequence[Sequence[float]] | Sequence[float] | Sequence[str] | None = None,
    q: Sequence[float] | float | None = None,
    *,
    variables: Sequence[str] | None = None,
    constraints: Sequence[Sequence[float]] | Sequence[float] | Sequence[str] | None = None,
    alpha: float = 0.05,
    **kwargs: Any,
) -> dict[str, float]:
    try:
        from scipy import stats
    except Exception:
        stats = None

    params = _params_series(result)
    V = _vcov_frame(result, params)

    if R is None and constraints is not None:
        R = constraints

    if (
        variables is None
        and isinstance(R, Sequence)
        and not isinstance(R, np.ndarray)
        and all(isinstance(item, str) for item in R)
    ):
        variables = list(R)  # type: ignore[arg-type]
        R = None

    if variables is not None:
        rows = []
        param_names = list(params.index)
        for name in variables:
            if name not in params.index:
                raise KeyError(f"Unknown coefficient in Wald test: {name!r}")
            row = np.zeros(params.size)
            row[param_names.index(name)] = 1.0
            rows.append(row)
        Rmat = np.vstack(rows)

    elif R is not None:
        Rmat = np.asarray(R, dtype=float)
        if Rmat.ndim == 1:
            Rmat = Rmat.reshape(1, -1)
        if Rmat.shape[1] != params.size:
            raise ValueError(
                f"Restriction matrix has {Rmat.shape[1]} columns, "
                f"but result has {params.size} parameters."
            )

    else:
        raise TypeError("wald_test() requires R, constraints, or variables.")

    if q is None:
        qvec = np.zeros(Rmat.shape[0])
    else:
        qvec = np.asarray(q, dtype=float).reshape(-1)
        if qvec.size == 1 and Rmat.shape[0] > 1:
            qvec = np.repeat(qvec, Rmat.shape[0])
        if qvec.size != Rmat.shape[0]:
            raise ValueError("q must have one value per restriction.")

    beta = params.to_numpy()
    Vmat = V.loc[params.index, params.index].to_numpy()

    diff = Rmat @ beta - qvec
    middle = Rmat @ Vmat @ Rmat.T
    inv_middle = np.linalg.pinv(middle)

    statistic = float(diff.T @ inv_middle @ diff)
    df_constraints = float(Rmat.shape[0])
    p_value = float(stats.chi2.sf(statistic, df_constraints)) if stats is not None else float("nan")

    return {
        "statistic": statistic,
        "chi2": statistic,
        "df": df_constraints,
        "df_constraints": df_constraints,
        "p_value": p_value,
        "alpha": float(alpha),
    }


def marginal_effects(
    result: Any,
    variables: Sequence[str] | None = None,
    alpha: float = 0.05,
    **kwargs: Any,
) -> pd.DataFrame:
    params = _params_series(result)
    se = _std_errors_series(result, params)

    if variables is None:
        variables = [
            str(name)
            for name in params.index
            if str(name).lower() not in {"const", "_con", "_cons", "intercept"}
        ]

    crit = _normal_crit(alpha)
    rows = []

    for name in variables:
        if name not in params.index:
            raise KeyError(f"Unknown coefficient in marginal_effects: {name!r}")

        effect = float(params.loc[name])
        std_error = float(se.loc[name])
        statistic = effect / std_error if std_error > 0 else float("nan")

        rows.append(
            {
                "variable": name,
                "term": name,
                "effect": effect,
                "estimate": effect,
                "std_error": std_error,
                "statistic": statistic,
                "z": statistic,
                "p_value": _normal_pvalue(statistic),
                "ci_low": float(effect - crit * std_error),
                "ci_high": float(effect + crit * std_error),
            }
        )

    out = pd.DataFrame(rows)
    if not out.empty:
        out.index = out["term"]
        out.index.name = "term"

    return out
