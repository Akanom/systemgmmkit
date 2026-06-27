from __future__ import annotations

import math
import re
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
    "estat_vce",
    "confint",
    "lincom",
    "wald_test",
    "marginal_effects",
    "margins",
    "predict_stata",
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


def _alpha_from_level(alpha: float = 0.05, level: float | None = None) -> float:
    if level is None:
        return float(alpha)

    value = float(level)
    if value > 1.0:
        value = value / 100.0

    if value <= 0.0 or value >= 1.0:
        raise ValueError("level must be between 0 and 1, or between 0 and 100.")

    return float(1.0 - value)


def _normal_pvalue(z: float) -> float:
    z = float(z)
    if not math.isfinite(z):
        return float("nan")
    return float(2.0 * (1.0 - 0.5 * (1.0 + math.erf(abs(z) / math.sqrt(2.0)))))


def _inference_df(result: Any) -> float | None:
    for name in ("df_inference", "df_resid"):
        value = _value_attr(result, [name])
        if value is None:
            continue
        try:
            out = float(value)
        except (TypeError, ValueError):
            continue
        if math.isfinite(out) and out > 0:
            return out
    return None


def _critical_value(alpha: float, df: float | None) -> float:
    try:
        from scipy import stats

        if df is not None:
            return float(stats.t.ppf(1.0 - alpha / 2.0, df))
        return float(stats.norm.ppf(1.0 - alpha / 2.0))
    except Exception:
        return _normal_crit(alpha)


def _two_sided_pvalue(statistic: float, df: float | None) -> float:
    try:
        from scipy import stats

        if df is not None:
            return float(2.0 * stats.t.sf(abs(statistic), df))
    except Exception:
        pass
    return _normal_pvalue(statistic)


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


def predict_stata(
    result: Any,
    data: Any | None = None,
    *,
    option: str = "xb",
    y: str | Sequence[float] | pd.Series | None = None,
    **kwargs: Any,
) -> Any:
    """Stata-style post-estimation prediction wrapper.

    Supported options are ``xb``/``fitted`` for linear predictions and
    ``residuals``/``resid`` for residuals. The helper composes existing
    post-estimation functions and does not modify fitted result objects.
    """

    option_value = str(option).strip().lower()

    if option_value in {"xb", "x", "linear", "prediction", "predictions"}:
        return predict(result, data, **kwargs)

    if option_value in {"fitted", "fitted_values", "fit", "yhat"}:
        if data is None:
            return fitted_values(result, **kwargs)
        return predict(result, data, **kwargs)

    if option_value in {"residual", "residuals", "resid", "e"}:
        out = residuals(result)
        if data is not None and y is not None:
            if isinstance(y, str):
                y_values = pd.to_numeric(data[y], errors="raise")
            else:
                y_values = pd.Series(y, index=getattr(data, "index", None), dtype=float)
            fit = predict(result, data, **kwargs)
            out = y_values.astype(float) - pd.Series(fit, index=y_values.index).astype(float)
            out.name = "residual"
        return out

    raise ValueError("option must be one of: xb, fitted, residuals, resid.")


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


def estat_vce(result: Any) -> pd.DataFrame:
    """Stata-style alias for the variance-covariance matrix."""

    return vcov(result)


def confint(
    result: Any,
    alpha: float = 0.05,
    *,
    level: float | None = None,
) -> pd.DataFrame:
    alpha = _alpha_from_level(alpha, level)
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


def _is_number(value: str) -> bool:
    try:
        float(value)
    except ValueError:
        return False
    return True


def _split_linear_terms(expression: str) -> list[tuple[float, str]]:
    text = expression.strip()
    if not text:
        raise ValueError("Linear expression cannot be empty.")

    terms: list[tuple[float, str]] = []
    for match in re.finditer(r"([+-]?)\s*([^+-]+)", text):
        sign_text, raw_term = match.groups()
        sign = -1.0 if sign_text == "-" else 1.0
        term = raw_term.strip()

        if not term:
            continue

        if "*" in term:
            left, right = [part.strip() for part in term.split("*", 1)]
            if _is_number(left):
                coefficient = float(left)
                name = right
            elif _is_number(right):
                coefficient = float(right)
                name = left
            else:
                raise ValueError(f"Could not parse linear term {term!r}.")
        else:
            parts = term.split()
            if len(parts) == 1:
                coefficient = 1.0
                name = parts[0]
            elif len(parts) == 2 and _is_number(parts[0]):
                coefficient = float(parts[0])
                name = parts[1]
            else:
                raise ValueError(f"Could not parse linear term {term!r}.")

        if not name:
            raise ValueError(f"Could not parse coefficient name from {term!r}.")

        terms.append((sign * coefficient, name))

    if not terms:
        raise ValueError("Linear expression did not contain any coefficient names.")

    return terms


def _linear_expression_to_weights(expression: str, params: pd.Series) -> tuple[pd.Series, float | None]:
    lhs, sep, rhs = expression.partition("=")
    w = pd.Series(0.0, index=params.index, dtype=float)

    for coefficient, name in _split_linear_terms(lhs):
        if name not in w.index:
            raise KeyError(f"Unknown coefficient in linear expression: {name!r}")
        w.loc[name] += float(coefficient)

    value = None
    if sep:
        rhs_text = rhs.strip()
        if not _is_number(rhs_text):
            raise ValueError(
                "Right-hand side of a linear constraint must be a numeric value."
            )
        value = float(rhs_text)

    return w, value


def _weights_from_expression(
    expression: Mapping[str, float] | Sequence[float] | str,
    params: pd.Series,
) -> tuple[pd.Series, float | None]:
    if isinstance(expression, str):
        return _linear_expression_to_weights(expression, params)

    if isinstance(expression, Mapping):
        w = pd.Series(0.0, index=params.index, dtype=float)
        for name, weight in expression.items():
            if name not in w.index:
                raise KeyError(f"Unknown coefficient in lincom expression: {name!r}")
            w.loc[name] = float(weight)
        return w, None

    arr = np.asarray(expression, dtype=float).reshape(-1)
    if arr.size != params.size:
        raise ValueError(
            f"Linear-combination vector has length {arr.size}, "
            f"but result has {params.size} parameters."
        )
    return pd.Series(arr, index=params.index, dtype=float), None


def _split_constraints(text: str) -> list[str]:
    text = text.strip()
    if text.lower().startswith("test "):
        text = text[5:].strip()
    if text.startswith("(") and text.endswith(")"):
        text = re.sub(r"\)\s*\(", ";\n", text[1:-1])
    parts = [
        part.strip()
        for part in re.split(r"[;\n,]+", text)
        if part.strip()
    ]
    if not parts:
        raise ValueError("Constraint expression cannot be empty.")
    return parts


def _constraints_to_matrices(
    constraints: Sequence[str] | str,
    params: pd.Series,
) -> tuple[np.ndarray, np.ndarray]:
    expressions = _split_constraints(constraints) if isinstance(constraints, str) else list(constraints)

    rows: list[np.ndarray] = []
    values: list[float] = []

    for expression in expressions:
        if expression in params.index:
            w = pd.Series(0.0, index=params.index, dtype=float)
            w.loc[expression] = 1.0
            value = 0.0
        else:
            w, parsed_value = _linear_expression_to_weights(str(expression), params)
            value = 0.0 if parsed_value is None else parsed_value

        rows.append(w.to_numpy(dtype=float))
        values.append(float(value))

    return np.vstack(rows), np.asarray(values, dtype=float)


def lincom(
    result: Any,
    expression: Mapping[str, float] | Sequence[float] | str | None = None,
    *,
    weights: Mapping[str, float] | Sequence[float] | str | None = None,
    value: float = 0.0,
    alpha: float = 0.05,
    level: float | None = None,
    **kwargs: Any,
) -> dict[str, float]:
    alpha = _alpha_from_level(alpha, level)

    if expression is None:
        expression = weights

    if expression is None:
        raise TypeError("lincom() requires an expression or weights argument.")

    params = _params_series(result)
    V = _vcov_frame(result, params)
    w, parsed_value = _weights_from_expression(expression, params)
    if parsed_value is not None:
        value = parsed_value

    estimate = float(w.to_numpy() @ params.to_numpy())
    variance = float(w.to_numpy() @ V.loc[params.index, params.index].to_numpy() @ w.to_numpy())
    std_error = math.sqrt(max(variance, 0.0))

    statistic = float((estimate - float(value)) / std_error) if std_error > 0 else float("nan")
    df = _inference_df(result)
    p_value = _two_sided_pvalue(statistic, df)
    crit = _critical_value(alpha, df)
    distribution = "t" if df is not None else "z"

    return {
        "estimate": estimate,
        "std_error": std_error,
        "statistic": statistic,
        "z": statistic if distribution == "z" else float("nan"),
        "t": statistic,
        "p_value": p_value,
        "ci_low": float(estimate - crit * std_error),
        "ci_high": float(estimate + crit * std_error),
        "value": float(value),
        "alpha": float(alpha),
        "df": float(df) if df is not None else float("nan"),
        "df_resid": float(df) if df is not None else float("nan"),
        "distribution": distribution,
    }


def wald_test(
    result: Any,
    R: Sequence[Sequence[float]] | Sequence[float] | Sequence[str] | str | None = None,
    q: Sequence[float] | float | None = None,
    *,
    variables: Sequence[str] | None = None,
    constraints: Sequence[Sequence[float]] | Sequence[float] | Sequence[str] | str | None = None,
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

    parsed_q: np.ndarray | None = None
    if variables is None and isinstance(R, str):
        Rmat, parsed_q = _constraints_to_matrices(R, params)
        R = None

    elif (
        variables is None
        and isinstance(R, Sequence)
        and not isinstance(R, np.ndarray)
        and all(isinstance(item, str) for item in R)
    ):
        string_items = list(R)  # type: ignore[arg-type]
        if all(item in params.index for item in string_items):
            variables = string_items
            R = None
        else:
            Rmat, parsed_q = _constraints_to_matrices(string_items, params)
            R = None

    if variables is not None:
        variables = list(variables)

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

    elif parsed_q is not None:
        pass

    else:
        raise TypeError("wald_test() requires R, constraints, or variables.")

    if parsed_q is not None and q is None:
        qvec = parsed_q
    elif q is None:
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
    df_inference = _inference_df(result)

    if stats is not None and df_inference is not None:
        f_statistic = statistic / df_constraints
        p_value = float(stats.f.sf(f_statistic, df_constraints, df_inference))
        display_statistic = float(f_statistic)
        distribution = "F"
    else:
        f_statistic = float("nan")
        p_value = float(stats.chi2.sf(statistic, df_constraints)) if stats is not None else float("nan")
        display_statistic = statistic
        distribution = "chi2"

    return {
        "statistic": display_statistic,
        "chi2": statistic,
        "f": f_statistic,
        "F": f_statistic,
        "df": df_constraints,
        "df_constraints": df_constraints,
        "df_denom": float(df_inference) if df_inference is not None else float("nan"),
        "df_resid": float(df_inference) if df_inference is not None else float("nan"),
        "p_value": p_value,
        "alpha": float(alpha),
        "distribution": distribution,
    }


def marginal_effects(
    result: Any,
    variables: Sequence[str] | None = None,
    alpha: float = 0.05,
    *,
    level: float | None = None,
    **kwargs: Any,
) -> pd.DataFrame:
    alpha = _alpha_from_level(alpha, level)
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
                "dy_dx": effect,
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


def margins(
    result: Any,
    dydx: Sequence[str] | str | None = None,
    *,
    variables: Sequence[str] | None = None,
    alpha: float = 0.05,
    level: float | None = None,
    **kwargs: Any,
) -> pd.DataFrame:
    """Stata-style alias for linear marginal effects.

    For linear models, ``margins, dydx(x z)`` is equivalent to returning the
    relevant slope coefficients with standard errors and confidence intervals.
    """

    if variables is None and dydx is not None:
        variables = [dydx] if isinstance(dydx, str) else list(dydx)

    return marginal_effects(
        result,
        variables=variables,
        alpha=alpha,
        level=level,
        **kwargs,
    )
