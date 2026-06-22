from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Iterable

import pandas as pd

from .adapter import adapt_result
from .metrics import regression_metrics
from .prediction import predict


def _normalise_models(
    models: Mapping[str, Any] | Iterable[tuple[str, Any]],
) -> list[tuple[str, Any]]:
    if isinstance(models, Mapping):
        return list(models.items())

    out = list(models)
    for item in out:
        if not isinstance(item, tuple) or len(item) != 2:
            raise TypeError(
                "models must be a mapping like {'OLS': result} or an iterable "
                "of (name, result) tuples."
            )
    return out


def _safe_diagnostics(result: Any) -> dict[str, Any]:
    adapter = adapt_result(result)

    try:
        diagnostics = adapter.diagnostics
    except Exception:
        diagnostics = {}

    if not isinstance(diagnostics, Mapping):
        return {}

    out: dict[str, Any] = {}
    for key, value in diagnostics.items():
        if isinstance(value, (int, float, str, bool)) or value is None:
            out[str(key)] = value
    return out


def compare_models(
    models: Mapping[str, Any] | Iterable[tuple[str, Any]],
    data: pd.DataFrame,
    *,
    y: str,
    sort_by: str | None = "rmse",
    ascending: bool = True,
    include_diagnostics: bool = True,
    predict_kwargs: dict[str, Any] | None = None,
    raise_on_error: bool = False,
) -> pd.DataFrame:
    """
    Compare fitted econometric model results using ML-style prediction metrics.

    Parameters
    ----------
    models:
        Mapping or iterable of ``(model_name, result_object)`` pairs.
    data:
        Evaluation dataframe.
    y:
        Dependent variable column in ``data``.
    sort_by:
        Column used to sort the comparison table. Defaults to RMSE.
        Set to None to preserve input order.
    ascending:
        Sort direction.
    include_diagnostics:
        If True, include scalar diagnostics exposed by result objects.
    predict_kwargs:
        Extra keyword arguments passed to ``systemgmmkit.ml.predict``.
    raise_on_error:
        If True, raise errors immediately. If False, keep failed models in the
        table with an ``error`` column.

    Returns
    -------
    pandas.DataFrame
        One row per model with prediction metrics and optional diagnostics.

    Notes
    -----
    This function does not re-estimate models. It compares already fitted
    accepted estimators through the additive ML workflow layer.
    """
    if y not in data.columns:
        raise KeyError(f"dependent variable '{y}' not found in data.")

    predict_kwargs = dict(predict_kwargs or {})
    rows: list[dict[str, Any]] = []

    for name, result in _normalise_models(models):
        row: dict[str, Any] = {
            "model": str(name),
            "error": "",
        }

        try:
            y_pred = predict(result, data, **predict_kwargs)
            metrics = regression_metrics(data[y], y_pred)
            row.update(metrics)

            if include_diagnostics:
                diagnostics = _safe_diagnostics(result)
                for key, value in diagnostics.items():
                    row[f"diag_{key}"] = value

        except Exception as exc:
            if raise_on_error:
                raise
            row["error"] = f"{type(exc).__name__}: {exc}"

        rows.append(row)

    table = pd.DataFrame(rows)

    if sort_by is not None and sort_by in table.columns:
        usable = table["error"].fillna("").eq("")
        ok = table.loc[usable].sort_values(sort_by, ascending=ascending)
        bad = table.loc[~usable]
        table = pd.concat([ok, bad], ignore_index=True)

    preferred = [
        "model",
        "n",
        "mae",
        "mse",
        "rmse",
        "mape",
        "smape",
        "r2",
        "error",
    ]

    diag_cols = [c for c in table.columns if c.startswith("diag_")]
    remaining = [
        c for c in table.columns
        if c not in preferred and c not in diag_cols
    ]

    ordered = [
        c for c in preferred if c in table.columns
    ] + diag_cols + remaining

    return table.loc[:, ordered]
