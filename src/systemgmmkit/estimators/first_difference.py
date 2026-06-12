from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class FirstDifferenceResult:
    params: dict[str, float]
    residuals: pd.Series
    fitted_values: pd.Series
    nobs: int
    entity: str
    time: str
    y: str
    x: list[str]
    method: str = "first_difference_ols"


def first_difference(
    data: pd.DataFrame,
    y: str,
    x: Iterable[str],
    entity: str,
    time: str,
    drop_missing: bool = True,
) -> FirstDifferenceResult:
    """
    First-difference panel estimator.

    Estimates:

        Δy_it = Δx_it β + Δu_it

    No intercept is included, which is the standard first-difference
    transformation because entity fixed effects difference out.
    """
    x = list(x)
    required = [entity, time, y, *x]

    missing_cols = [c for c in required if c not in data.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    df = data[required].copy()
    df = df.sort_values([entity, time])

    diff_cols = [y, *x]
    d = df[[entity, time]].copy()

    for col in diff_cols:
        d[f"D_{col}"] = df.groupby(entity, sort=False)[col].diff()

    if drop_missing:
        d = d.dropna(subset=[f"D_{y}", *[f"D_{v}" for v in x]])

    if d.empty:
        raise ValueError("No usable observations after first differencing.")

    Y = d[f"D_{y}"].to_numpy(dtype=float)
    X = d[[f"D_{v}" for v in x]].to_numpy(dtype=float)

    beta, *_ = np.linalg.lstsq(X, Y, rcond=None)

    fitted = X @ beta
    residuals = Y - fitted

    params = {name: float(value) for name, value in zip(x, beta)}

    return FirstDifferenceResult(
        params=params,
        residuals=pd.Series(residuals, index=d.index, name="residual"),
        fitted_values=pd.Series(fitted, index=d.index, name="fitted"),
        nobs=int(len(d)),
        entity=entity,
        time=time,
        y=y,
        x=x,
    )
