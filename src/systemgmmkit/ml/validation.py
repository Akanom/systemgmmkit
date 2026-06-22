from __future__ import annotations

from typing import Any, Callable

import pandas as pd

from .metrics import regression_metrics
from .prediction import predict
from .split import PanelTimeSeriesSplit


def cross_validate_panel(
    *,
    estimator: Callable[..., Any],
    data: pd.DataFrame,
    y: str,
    time: str,
    cv: PanelTimeSeriesSplit | None = None,
    fit_kwargs: dict[str, Any] | None = None,
    predict_kwargs: dict[str, Any] | None = None,
) -> pd.DataFrame:
    """
    Panel-aware cross-validation.

    estimator must be a callable accepting data=... or a positional dataframe.
    It should return a result object compatible with ml.predict().
    """
    if y not in data.columns:
        raise KeyError(f"dependent variable '{y}' not found.")

    cv = cv or PanelTimeSeriesSplit()
    fit_kwargs = dict(fit_kwargs or {})
    predict_kwargs = dict(predict_kwargs or {})

    rows: list[dict[str, float]] = []

    for fold, (train_idx, test_idx) in enumerate(cv.split(data, time=time), start=1):
        train = data.loc[train_idx].copy()
        test = data.loc[test_idx].copy()

        try:
            result = estimator(data=train, **fit_kwargs)
        except TypeError:
            result = estimator(train, **fit_kwargs)

        y_pred = predict(result, test, **predict_kwargs)
        metrics = regression_metrics(test[y], y_pred)

        rows.append(
            {
                "fold": float(fold),
                "train_n": float(len(train)),
                "test_n": float(len(test)),
                **metrics,
            }
        )

    return pd.DataFrame(rows)
