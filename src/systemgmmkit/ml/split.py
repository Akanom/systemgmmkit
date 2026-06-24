from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

import pandas as pd


def panel_train_test_split(
    data: pd.DataFrame,
    *,
    time: str,
    test_size: float | int = 0.2,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Time-respecting panel train/test split.

    test_size:
    - float between 0 and 1: share of unique time periods used as test
    - int: number of final time periods used as test
    """
    if time not in data.columns:
        raise KeyError(f"time column '{time}' not found.")

    periods = sorted(data[time].dropna().unique())
    if len(periods) < 2:
        raise ValueError("At least two time periods are required.")

    if isinstance(test_size, float):
        if not 0 < test_size < 1:
            raise ValueError("Float test_size must be between 0 and 1.")
        n_test = max(1, int(round(len(periods) * test_size)))
    else:
        n_test = int(test_size)

    if n_test <= 0 or n_test >= len(periods):
        raise ValueError("test_size leaves no train or no test periods.")

    test_periods = set(periods[-n_test:])
    train = data.loc[~data[time].isin(test_periods)].copy()
    test = data.loc[data[time].isin(test_periods)].copy()
    return train, test


@dataclass(frozen=True)
class PanelTimeSeriesSplit:
    """
    Expanding-window cross-validation for panel data.

    Splits are based on unique time periods, not random rows.
    """

    n_splits: int = 5
    min_train_periods: int | None = None
    test_periods: int = 1

    def split(self, data: pd.DataFrame, *, time: str) -> Iterator[tuple[pd.Index, pd.Index]]:
        if time not in data.columns:
            raise KeyError(f"time column '{time}' not found.")

        periods = sorted(data[time].dropna().unique())
        n_periods = len(periods)

        if self.n_splits < 1:
            raise ValueError("n_splits must be >= 1.")

        if self.test_periods < 1:
            raise ValueError("test_periods must be >= 1.")

        min_train = self.min_train_periods
        if min_train is None:
            min_train = max(1, n_periods - self.n_splits * self.test_periods)

        if min_train + self.test_periods > n_periods:
            raise ValueError("Not enough time periods for requested split design.")

        for i in range(self.n_splits):
            train_end = min_train + i * self.test_periods
            test_end = train_end + self.test_periods

            if test_end > n_periods:
                break

            train_periods = set(periods[:train_end])
            test_period_set = set(periods[train_end:test_end])

            train_idx = data.index[data[time].isin(train_periods)]
            test_idx = data.index[data[time].isin(test_period_set)]

            if len(train_idx) and len(test_idx):
                yield train_idx, test_idx
