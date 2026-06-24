from __future__ import annotations

import re
from typing import Any

import numpy as np
import pandas as pd

from .adapter import adapt_result

_CONST_NAMES = {"const", "_cons", "_con", "intercept", "Intercept"}


def _parse_lagged_y(term: str, y: str) -> int | None:
    """
    Detect common lagged dependent-variable coefficient names.

    Supported examples:
    - L1.y
    - L2.y
    - L.y
    - y_lag1
    - lag1_y
    - L1_y
    """
    if term == f"L.{y}":
        return 1

    m = re.match(r"^L(?P<lag>\d+)\.(?P<var>.+)$", term)
    if m and m.group("var") == y:
        return int(m.group("lag"))

    m = re.match(rf"^{re.escape(y)}_lag(?P<lag>\d+)$", term)
    if m:
        return int(m.group("lag"))

    m = re.match(rf"^lag(?P<lag>\d+)_{re.escape(y)}$", term)
    if m:
        return int(m.group("lag"))

    m = re.match(rf"^L(?P<lag>\d+)_{re.escape(y)}$", term)
    if m:
        return int(m.group("lag"))

    return None


def _advance_time(value: Any, step: int, time_step: Any | None = None) -> Any:
    if time_step is not None:
        if isinstance(value, pd.Timestamp):
            if isinstance(time_step, pd.DateOffset):
                return value + step * time_step
            return value + pd.to_timedelta(step * time_step)
        return value + step * time_step

    if isinstance(value, pd.Timestamp):
        return value + pd.DateOffset(periods=step)

    try:
        return value + step
    except TypeError:
        return step


def _latest_rows(history: pd.DataFrame, *, entity: str, time: str) -> dict[Any, pd.Series]:
    ordered = history.sort_values([entity, time])
    return {
        ent: group.iloc[-1].copy()
        for ent, group in ordered.groupby(entity, sort=False)
    }


def _initial_lag_buffer(
    history: pd.DataFrame,
    *,
    y: str,
    entity: str,
    time: str,
    max_lag: int,
) -> dict[Any, list[float]]:
    ordered = history.sort_values([entity, time])
    buffers: dict[Any, list[float]] = {}

    for ent, group in ordered.groupby(entity, sort=False):
        values = pd.to_numeric(group[y], errors="raise").astype(float).tolist()
        if len(values) < max_lag:
            raise ValueError(
                f"Entity {ent!r} has {len(values)} observations, but max lag "
                f"{max_lag} is required."
            )
        buffers[ent] = list(reversed(values[-max_lag:]))

    return buffers


def _future_rows_by_entity(
    future_exog: pd.DataFrame | None,
    *,
    entity: str,
    time: str,
) -> dict[Any, pd.DataFrame]:
    if future_exog is None:
        return {}

    if entity not in future_exog.columns:
        raise KeyError(f"future_exog is missing entity column '{entity}'.")

    if time in future_exog.columns:
        future_exog = future_exog.sort_values([entity, time])
    else:
        future_exog = future_exog.sort_values([entity])

    return {
        ent: group.reset_index(drop=True)
        for ent, group in future_exog.groupby(entity, sort=False)
    }


def forecast(
    result: Any,
    history: pd.DataFrame,
    *,
    y: str,
    entity: str,
    time: str,
    horizon: int = 1,
    future_exog: pd.DataFrame | None = None,
    time_step: Any | None = None,
    strict: bool = True,
) -> pd.DataFrame:
    """
    Recursive forecast for fitted econometric result objects.

    The function uses an already fitted model result and estimated parameters.
    It does not re-estimate and does not modify estimator internals.

    Parameters
    ----------
    result:
        Fitted result object exposing a parameter vector.
    history:
        Historical panel dataframe containing entity, time, y, and regressors.
    y:
        Dependent variable name.
    entity:
        Entity identifier column.
    time:
        Time identifier column.
    horizon:
        Number of periods to forecast.
    future_exog:
        Optional future exogenous dataframe. If omitted, the latest observed
        row for each entity is reused and exogenous variables are held constant.
    time_step:
        Optional increment used when future_exog is not supplied.
    strict:
        If True, missing regressors raise errors. If False, missing non-lag
        regressors are filled with zero.

    Returns
    -------
    pandas.DataFrame
        Forecast table with entity, time, horizon, and prediction columns.

    Notes
    -----
    Dynamic terms are detected from coefficient names such as `L1.y`, `L2.y`,
    `L.y`, `y_lag1`, `lag1_y`, and `L1_y`.
    """
    if horizon < 1:
        raise ValueError("horizon must be >= 1.")

    for col in (y, entity, time):
        if col not in history.columns:
            raise KeyError(f"history is missing required column '{col}'.")

    adapter = adapt_result(result)
    params = adapter.params.astype(float)

    lag_terms: dict[str, int] = {}
    for term in params.index:
        lag = _parse_lagged_y(str(term), y)
        if lag is not None:
            lag_terms[str(term)] = lag

    max_lag = max(lag_terms.values(), default=1)

    latest = _latest_rows(history, entity=entity, time=time)
    lag_buffer = _initial_lag_buffer(
        history,
        y=y,
        entity=entity,
        time=time,
        max_lag=max_lag,
    )
    future_groups = _future_rows_by_entity(
        future_exog,
        entity=entity,
        time=time,
    )

    rows: list[dict[str, Any]] = []

    for ent, last_row in latest.items():
        ent_future = future_groups.get(ent)

        for h in range(1, horizon + 1):
            if ent_future is not None and h <= len(ent_future):
                row = ent_future.iloc[h - 1].copy()
                forecast_time = row[time] if time in row.index else _advance_time(last_row[time], h, time_step)
            else:
                row = last_row.copy()
                row[entity] = ent
                forecast_time = _advance_time(last_row[time], h, time_step)
                row[time] = forecast_time

            design_values: list[float] = []

            for term in params.index:
                term_str = str(term)

                if term_str in _CONST_NAMES:
                    design_values.append(1.0)
                    continue

                lag = lag_terms.get(term_str)
                if lag is not None:
                    if lag > len(lag_buffer[ent]):
                        raise ValueError(
                            f"Entity {ent!r} does not have lag {lag} available."
                        )
                    design_values.append(float(lag_buffer[ent][lag - 1]))
                    continue

                if term_str in row.index:
                    design_values.append(float(row[term_str]))
                    continue

                if strict:
                    raise KeyError(
                        f"Column '{term_str}' required for forecasting was not found."
                    )

                design_values.append(0.0)

            prediction = float(np.dot(np.asarray(design_values), params.to_numpy()))

            rows.append(
                {
                    entity: ent,
                    time: forecast_time,
                    "horizon": h,
                    "prediction": prediction,
                }
            )

            lag_buffer[ent] = [prediction] + lag_buffer[ent][:-1]

    return pd.DataFrame(rows)
