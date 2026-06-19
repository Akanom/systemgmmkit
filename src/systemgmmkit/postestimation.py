from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats


def _get_params(result: Any) -> pd.Series:
    params = getattr(result, "params", None)

    if params is None:
        params = getattr(result, "coefficients", None)

    if params is None:
        raise AttributeError("Result object does not expose params/coefficients.")

    if isinstance(params, pd.Series):
        return params.astype(float)

    if isinstance(params, Mapping):
        return pd.Series(params, dtype=float)

    arr = np.asarray(params, dtype=float).reshape(-1)
    names = getattr(result, "param_names", None)

    if names is None:
        names = [f"b{i}" for i in range(len(arr))]

    return pd.Series(arr, index=list(names), dtype=float)


def _get_covariance(result: Any, params: pd.Series | None = None) -> pd.DataFrame:
    if params is None:
        params = _get_params(result)

    cov = None

    for name in ("covariance", "cov", "vcov_matrix"):
        if hasattr(result, name):
            value = getattr(result, name)
            cov = value() if callable(value) and name == "vcov_matrix" else value
            if cov is not None:
                break

    if cov is None and hasattr(result, "vcov"):
        value = result.vcov
        cov = value() if callable(value) else value

    if cov is None:
        raise AttributeError("Result object does not expose a covariance/vcov matrix.")

    if isinstance(cov, pd.DataFrame):
        return cov.loc[params.index, params.index].astype(float)

    arr = np.asarray(cov, dtype=float)
    return pd.DataFrame(arr, index=params.index, columns=params.index)


def _get_df_resid(result: Any) -> int:
    df_inference = getattr(result, "df_inference", None)
    if df_inference is not None:
        return max(int(df_inference), 1)

    df = getattr(result, "df_resid", None)

    if df is None:
        nobs = getattr(result, "nobs", None)
        params = _get_params(result)

        if nobs is None:
            return max(len(params) - 1, 1)

        return max(int(nobs) - len(params), 1)

    return max(int(df), 1)


def vcov(result: Any) -> pd.DataFrame:
    params = _get_params(result)
    return _get_covariance(result, params=params).copy()


def confint(result: Any, alpha: float = 0.05) -> pd.DataFrame:
    params = _get_params(result)
    cov = _get_covariance(result, params=params)
    df_resid = _get_df_resid(result)

    se = pd.Series(
        np.sqrt(np.maximum(np.diag(cov.to_numpy()), 0.0)),
        index=params.index,
    )

    critical = stats.t.ppf(1.0 - alpha / 2.0, df_resid)

    return pd.DataFrame(
        {
            "lower": params - critical * se,
            "upper": params + critical * se,
        }
    )


def predict(result: Any, data: pd.DataFrame | None = None) -> pd.Series:
    method = getattr(result, "predict", None)

    if callable(method):
        return method(data)

    if data is None:
        return fitted_values(result)

    raise AttributeError("Result object does not expose predict(data).")


def fitted_values(result: Any) -> pd.Series:
    for name in ("fitted_values", "fitted", "fitted_values_series"):
        if hasattr(result, name):
            value = getattr(result, name)
            out = value() if callable(value) else value

            if isinstance(out, pd.Series):
                return out.copy()

            return pd.Series(out, name="fitted")

    raise AttributeError("Result object does not expose fitted values.")


def residuals(result: Any) -> pd.Series:
    for name in ("residuals", "resid", "residual_values"):
        if hasattr(result, name):
            value = getattr(result, name)
            out = value() if callable(value) else value

            if isinstance(out, pd.Series):
                return out.copy()

            return pd.Series(out, name="residual")

    raise AttributeError("Result object does not expose residuals.")


def _weights_to_series(
    weights: Mapping[str, float] | Sequence[float],
    params: pd.Series,
) -> pd.Series:
    if isinstance(weights, Mapping):
        w = pd.Series(0.0, index=params.index)

        unknown = [name for name in weights if name not in params.index]
        if unknown:
            raise KeyError(f"Unknown coefficient(s) in linear combination: {unknown}")

        for name, value in weights.items():
            w.loc[name] = float(value)

        return w

    arr = np.asarray(weights, dtype=float).reshape(-1)

    if len(arr) != len(params):
        raise ValueError(
            f"Linear-combination vector length {len(arr)} does not match "
            f"number of parameters {len(params)}."
        )

    return pd.Series(arr, index=params.index)


def lincom(
    result: Any,
    weights: Mapping[str, float] | Sequence[float],
    value: float = 0.0,
    alpha: float = 0.05,
) -> dict[str, float]:
    params = _get_params(result)
    cov = _get_covariance(result, params=params)
    df_resid = _get_df_resid(result)
    w = _weights_to_series(weights, params)

    estimate = float(w.to_numpy() @ params.to_numpy())
    variance = float(w.to_numpy() @ cov.to_numpy() @ w.to_numpy())
    std_error = float(np.sqrt(max(variance, 0.0)))

    statistic = float((estimate - value) / std_error) if std_error > 0 else np.nan
    p_value = (
        float(2.0 * stats.t.sf(abs(statistic), df_resid)) if np.isfinite(statistic) else np.nan
    )
    critical = float(stats.t.ppf(1.0 - alpha / 2.0, df_resid))

    return {
        "estimate": estimate,
        "null_value": float(value),
        "std_error": std_error,
        "statistic": statistic,
        "p_value": p_value,
        "ci_lower": estimate - critical * std_error,
        "ci_upper": estimate + critical * std_error,
        "df_resid": float(df_resid),
    }


def wald_test(
    result: Any,
    R: Sequence[Sequence[float]],
    q: Sequence[float] | None = None,
    use_f: bool = False,
) -> dict[str, float]:
    params = _get_params(result)
    cov = _get_covariance(result, params=params)

    R_arr = np.asarray(R, dtype=float)

    if R_arr.ndim == 1:
        R_arr = R_arr.reshape(1, -1)

    if R_arr.shape[1] != len(params):
        raise ValueError(
            f"Restriction matrix has {R_arr.shape[1]} columns but result has "
            f"{len(params)} parameters."
        )

    if q is None:
        q_arr = np.zeros(R_arr.shape[0], dtype=float)
    else:
        q_arr = np.asarray(q, dtype=float).reshape(-1)

    if len(q_arr) != R_arr.shape[0]:
        raise ValueError("Restriction value vector q must match number of restrictions.")

    diff = R_arr @ params.to_numpy(dtype=float) - q_arr
    middle = R_arr @ cov.to_numpy(dtype=float) @ R_arr.T

    chi2_statistic = float(diff.T @ np.linalg.pinv(middle) @ diff)
    df_constraints = int(R_arr.shape[0])

    if use_f:
        df_resid = _get_df_resid(result)
        f_statistic = chi2_statistic / df_constraints
        p_value = float(stats.f.sf(f_statistic, df_constraints, df_resid))
        return {
            "statistic": f_statistic,
            "df_constraints": float(df_constraints),
            "df_resid": float(df_resid),
            "p_value": p_value,
            "distribution": "F",
            "chi2_statistic": chi2_statistic,
        }

    p_value = float(stats.chi2.sf(chi2_statistic, df_constraints))

    return {
        "statistic": chi2_statistic,
        "df_constraints": float(df_constraints),
        "p_value": p_value,
        "distribution": "chi2",
    }


def marginal_effects(
    result: Any,
    variables: Sequence[str] | None = None,
    alpha: float = 0.05,
) -> pd.DataFrame:
    params = _get_params(result)
    cov = _get_covariance(result, params=params)
    ci = confint(result, alpha=alpha)

    if variables is None:
        variables = [name for name in params.index if name not in {"_con", "const", "intercept"}]

    rows: list[dict[str, float | str]] = []

    for var in variables:
        if var not in params.index:
            raise KeyError(f"Unknown variable for marginal effect: {var}")

        se = float(np.sqrt(max(float(cov.loc[var, var]), 0.0)))

        rows.append(
            {
                "variable": var,
                "dy_dx": float(params.loc[var]),
                "std_error": se,
                "ci_lower": float(ci.loc[var, "lower"]),
                "ci_upper": float(ci.loc[var, "upper"]),
            }
        )

    return pd.DataFrame(rows)
