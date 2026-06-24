from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

_PARAM_NAMES = ("params", "coef", "coefficients", "beta", "parameter")
_COV_NAMES = ("cov", "covariance", "cov_params", "vcov")
_NOBS_NAMES = ("nobs", "n_obs", "n")


def _as_series(obj: Any, *, name: str = "param") -> pd.Series:
    if obj is None:
        raise ValueError("Cannot convert None to Series.")

    if isinstance(obj, pd.Series):
        return obj.astype(float)

    if isinstance(obj, Mapping):
        return pd.Series(obj, dtype=float, name=name)

    arr = np.asarray(obj, dtype=float).reshape(-1)
    return pd.Series(arr, name=name)


def _maybe_call(value: Any) -> Any:
    return value() if callable(value) else value


def _first_attr(obj: Any, names: tuple[str, ...]) -> Any:
    for name in names:
        if hasattr(obj, name):
            return _maybe_call(getattr(obj, name))
    return None


@dataclass(frozen=True)
class ResultAdapter:
    """
    Generic duck-typed adapter for econometric result objects.

    It expects, at minimum, coefficient parameters. It works with:
    - systemgmmkit-style result objects
    - statsmodels-like result objects
    - linearmodels-like result objects
    - dictionaries
    - simple custom result containers
    """

    result: Any

    @property
    def params(self) -> pd.Series:
        if isinstance(self.result, Mapping):
            for key in _PARAM_NAMES:
                if key in self.result:
                    return _as_series(self.result[key])
        value = _first_attr(self.result, _PARAM_NAMES)
        if value is None:
            raise AttributeError(
                "Could not find model parameters. Expected one of: "
                f"{', '.join(_PARAM_NAMES)}"
            )
        return _as_series(value)

    @property
    def cov(self) -> pd.DataFrame | None:
        value = None
        if isinstance(self.result, Mapping):
            for key in _COV_NAMES:
                if key in self.result:
                    value = self.result[key]
                    break
        else:
            value = _first_attr(self.result, _COV_NAMES)

        if value is None:
            return None

        if isinstance(value, pd.DataFrame):
            return value.astype(float)

        arr = np.asarray(value, dtype=float)
        names = list(self.params.index)
        return pd.DataFrame(arr, index=names, columns=names)

    @property
    def nobs(self) -> int | None:
        if isinstance(self.result, Mapping):
            for key in _NOBS_NAMES:
                if key in self.result:
                    return int(self.result[key])
        value = _first_attr(self.result, _NOBS_NAMES)
        return None if value is None else int(value)

    @property
    def diagnostics(self) -> dict[str, Any]:
        if isinstance(self.result, Mapping):
            diag = self.result.get("diagnostics", {})
            return dict(diag) if isinstance(diag, Mapping) else {}
        diag = getattr(self.result, "diagnostics", {})
        return dict(diag) if isinstance(diag, Mapping) else {}

    def has_native(self, method_name: str) -> bool:
        return hasattr(self.result, method_name) and callable(getattr(self.result, method_name))

    def call_native(self, method_name: str, *args: Any, **kwargs: Any) -> Any:
        if not self.has_native(method_name):
            raise AttributeError(f"Result object has no native {method_name} method.")
        return getattr(self.result, method_name)(*args, **kwargs)


def adapt_result(result: Any) -> ResultAdapter:
    return ResultAdapter(result=result)
