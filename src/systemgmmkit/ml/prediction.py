from __future__ import annotations

from typing import Any, Iterable

import numpy as np
import pandas as pd

from .adapter import adapt_result


_CONST_NAMES = ("const", "_cons", "_con", "intercept", "Intercept")


def _prepare_design(
    data: pd.DataFrame,
    params: pd.Series,
    *,
    add_constant: bool = True,
    strict: bool = True,
) -> pd.DataFrame:
    names = list(params.index)
    X = pd.DataFrame(index=data.index)

    for name in names:
        if name in data.columns:
            X[name] = pd.to_numeric(data[name], errors="raise")
        elif name in _CONST_NAMES:
            X[name] = 1.0
        elif add_constant and name.lower() in {c.lower() for c in _CONST_NAMES}:
            X[name] = 1.0
        elif strict:
            raise KeyError(
                f"Column '{name}' required for prediction was not found in data."
            )
        else:
            X[name] = 0.0

    return X.astype(float)


def predict(
    result: Any,
    data: pd.DataFrame,
    *,
    add_constant: bool = True,
    strict: bool = True,
) -> pd.Series:
    """
    Generic linear prediction: X @ beta.

    If the result object already has a native predict method, prefer that.
    Otherwise use the parameter vector and matching dataframe columns.
    """
    adapter = adapt_result(result)

    if adapter.has_native("predict"):
        try:
            pred = adapter.call_native("predict", data)
            return pd.Series(pred, index=data.index, name="prediction")
        except TypeError:
            pass

    params = adapter.params
    X = _prepare_design(
        data=data,
        params=params,
        add_constant=add_constant,
        strict=strict,
    )
    values = X.to_numpy() @ params.to_numpy()
    return pd.Series(values, index=data.index, name="prediction")


def fitted_values(
    result: Any,
    data: pd.DataFrame | None = None,
    *,
    add_constant: bool = True,
    strict: bool = True,
) -> pd.Series:
    """
    Return fitted values.

    Uses native fitted values where available. Otherwise requires data.
    """
    adapter = adapt_result(result)

    for name in ("fitted_values", "fittedvalues", "fitted", "yhat"):
        if hasattr(result, name):
            value = getattr(result, name)
            value = value() if callable(value) else value
            return pd.Series(value, name="fitted")

    if data is None:
        raise ValueError("data is required when fitted values are not stored on result.")

    out = predict(
        result,
        data,
        add_constant=add_constant,
        strict=strict,
    )
    out.name = "fitted"
    return out


def residuals(
    result: Any,
    data: pd.DataFrame | None = None,
    y: str | Iterable[float] | pd.Series | None = None,
    *,
    add_constant: bool = True,
    strict: bool = True,
) -> pd.Series:
    """
    Return residuals.

    Uses native residuals where available. Otherwise computes y - fitted.
    """
    for name in ("residuals", "resids", "resid"):
        if hasattr(result, name):
            value = getattr(result, name)
            value = value() if callable(value) else value
            return pd.Series(value, name="residual")

    if y is None or data is None:
        raise ValueError("Both data and y are required when residuals are not stored.")

    if isinstance(y, str):
        y_values = pd.to_numeric(data[y], errors="raise")
    else:
        y_values = pd.Series(y, index=data.index, dtype=float)

    fit = fitted_values(
        result,
        data,
        add_constant=add_constant,
        strict=strict,
    )
    out = y_values.astype(float) - fit.astype(float)
    out.name = "residual"
    return out
