from __future__ import annotations

from typing import Any, Callable, Iterable

import pandas as pd

from .forecast import forecast
from .metrics import regression_metrics


def _call_result_factory(
    result_factory: Callable[..., Any],
    train: pd.DataFrame,
    fit_kwargs: dict[str, Any],
) -> Any:
    try:
        return result_factory(data=train, **fit_kwargs)
    except TypeError:
        return result_factory(train, **fit_kwargs)


def _resolve_cutoffs(
    periods: list[Any],
    *,
    horizon: int,
    min_train_periods: int | None,
    cutoffs: Iterable[Any] | None,
    max_cutoffs: int | None,
) -> list[Any]:
    if horizon < 1:
        raise ValueError("horizon must be >= 1.")

    if len(periods) <= horizon:
        raise ValueError("Not enough time periods for requested forecast horizon.")

    if cutoffs is not None:
        resolved = list(cutoffs)
        valid = set(periods[:-horizon])
        invalid = [c for c in resolved if c not in valid]
        if invalid:
            raise ValueError(
                "Some cutoffs are invalid because they are not observed periods "
                f"or leave no future horizon: {invalid}"
            )
        return resolved

    if min_train_periods is None:
        min_train_periods = max(1, len(periods) // 2)

    if min_train_periods < 1:
        raise ValueError("min_train_periods must be >= 1.")

    if min_train_periods + horizon > len(periods):
        raise ValueError(
            "min_train_periods plus horizon leaves no valid backtest cutoff."
        )

    resolved = periods[min_train_periods - 1 : len(periods) - horizon]

    if max_cutoffs is not None:
        if max_cutoffs < 1:
            raise ValueError("max_cutoffs must be >= 1 when supplied.")
        resolved = resolved[-max_cutoffs:]

    return resolved


def backtest_forecast(
    *,
    result_factory: Callable[..., Any],
    data: pd.DataFrame,
    y: str,
    entity: str,
    time: str,
    horizon: int = 1,
    min_train_periods: int | None = None,
    cutoffs: Iterable[Any] | None = None,
    max_cutoffs: int | None = None,
    fit_kwargs: dict[str, Any] | None = None,
    forecast_kwargs: dict[str, Any] | None = None,
    strict: bool = True,
) -> pd.DataFrame:
    """
    Expanding-window forecast backtesting for panel econometric models.

    The function repeatedly:
    1. keeps observations up to a cutoff as training history
    2. obtains a fitted result from ``result_factory``
    3. forecasts the next ``horizon`` periods
    4. compares forecasts with observed outcomes

    Parameters
    ----------
    result_factory:
        Callable returning a fitted result object. It should accept either
        ``data=train`` or ``train`` as its first argument.
    data:
        Panel dataframe containing entity, time, y, and regressors.
    y:
        Dependent variable column.
    entity:
        Entity identifier column.
    time:
        Time identifier column.
    horizon:
        Number of future periods to forecast at each cutoff.
    min_train_periods:
        Minimum number of unique time periods used before the first cutoff.
    cutoffs:
        Optional explicit cutoff periods.
    max_cutoffs:
        Optional maximum number of most recent cutoffs to evaluate.
    fit_kwargs:
        Extra arguments passed to ``result_factory``.
    forecast_kwargs:
        Extra arguments passed to ``forecast``.
    strict:
        Passed to ``forecast``. If True, missing required regressors raise.

    Returns
    -------
    pandas.DataFrame
        One row per cutoff and forecast horizon with regression metrics.

    Notes
    -----
    This function does not implement a new estimator. It backtests existing
    accepted estimators through the additive ML workflow layer.
    """
    for col in (y, entity, time):
        if col not in data.columns:
            raise KeyError(f"data is missing required column '{col}'.")

    fit_kwargs = dict(fit_kwargs or {})
    forecast_kwargs = dict(forecast_kwargs or {})

    ordered = data.sort_values([entity, time]).copy()
    periods = sorted(ordered[time].dropna().unique().tolist())

    resolved_cutoffs = _resolve_cutoffs(
        periods,
        horizon=horizon,
        min_train_periods=min_train_periods,
        cutoffs=cutoffs,
        max_cutoffs=max_cutoffs,
    )

    rows: list[dict[str, Any]] = []

    for cutoff in resolved_cutoffs:
        cutoff_pos = periods.index(cutoff)
        future_periods = periods[cutoff_pos + 1 : cutoff_pos + 1 + horizon]

        train = ordered.loc[ordered[time].isin(periods[: cutoff_pos + 1])].copy()
        actual_future = ordered.loc[ordered[time].isin(future_periods)].copy()

        future_exog = actual_future.drop(columns=[y], errors="ignore").copy()

        result = _call_result_factory(result_factory, train, fit_kwargs)

        fc = forecast(
            result,
            train,
            y=y,
            entity=entity,
            time=time,
            horizon=horizon,
            future_exog=future_exog,
            strict=strict,
            **forecast_kwargs,
        )

        actual = actual_future[[entity, time, y]].copy()

        merged = fc.merge(
            actual,
            on=[entity, time],
            how="inner",
            validate="one_to_one",
        )

        for h in range(1, horizon + 1):
            hdata = merged.loc[merged["horizon"] == h].copy()

            row: dict[str, Any] = {
                "cutoff": cutoff,
                "horizon": h,
                "train_n": float(len(train)),
                "test_n": float(len(hdata)),
            }

            if hdata.empty:
                row["error"] = "No matched observations for cutoff/horizon."
            else:
                row.update(regression_metrics(hdata[y], hdata["prediction"]))
                row["error"] = ""

            rows.append(row)

    return pd.DataFrame(rows)
