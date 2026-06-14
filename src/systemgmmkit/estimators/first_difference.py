"""First-difference panel estimator.

This module provides a lightweight first-difference OLS estimator for panel data.
The result object exposes ``summary_frame()`` so it is compatible with
systemgmmkit reporting helpers:

- result_to_frame()
- combine_result_frames()
- export_regression_table()
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import erf, sqrt
from typing import Iterable

import numpy as np
import pandas as pd


def _normal_two_sided_pvalue(z: float) -> float:
    """Two-sided normal-approximation p-value."""
    if not np.isfinite(z):
        return float("nan")
    cdf = 0.5 * (1.0 + erf(abs(float(z)) / sqrt(2.0)))
    return float(2.0 * (1.0 - cdf))


@dataclass
class FirstDifferenceResult:
    """Result container for first-difference OLS."""

    params: dict[str, float]
    residuals: pd.Series
    fitted_values: pd.Series
    y: str
    x: list[str]
    entity: str
    time: str
    nobs: int
    method: str = "first_difference_ols"
    std_errors: dict[str, float] = field(default_factory=dict)
    t_stats: dict[str, float] = field(default_factory=dict)
    p_values: dict[str, float] = field(default_factory=dict)
    r2: float | None = None
    rss: float | None = None
    df_resid: int | None = None
    rank: int | None = None

    def summary_frame(self) -> pd.DataFrame:
        """Return coefficient table compatible with systemgmmkit reporting.

        Contract:
            systemgmmkit.tables.result_to_frame() inserts the ``term`` column
            from the summary frame index. Therefore this method must return
            terms as the DataFrame index, not as a pre-existing ``term`` column.
        """
        rows: list[dict[str, float]] = []
        terms = list(self.params.keys())

        for term in terms:
            coef = self.params.get(term, float("nan"))
            se = self.std_errors.get(term, float("nan"))
            stat = self.t_stats.get(term, float("nan"))
            pval = self.p_values.get(term, float("nan"))

            rows.append(
                {
                    "coef": coef,
                    "std_err": se,
                    "statistic": stat,
                    "p_value": pval,
                }
            )

        return pd.DataFrame(rows, index=pd.Index(terms, name="term"))


def first_difference(
    data: pd.DataFrame,
    y: str,
    x: Iterable[str],
    entity: str,
    time: str,
    drop_missing: bool = True,
) -> FirstDifferenceResult:
    """Estimate a first-difference OLS model.

    Parameters
    ----------
    data:
        Panel dataframe.
    y:
        Dependent variable.
    x:
        Regressors.
    entity:
        Entity identifier.
    time:
        Time identifier.
    drop_missing:
        Whether to drop rows with missing differenced values.

    Returns
    -------
    FirstDifferenceResult
        Result object with coefficients, residuals, fitted values,
        standard errors, test statistics, p-values, and summary_frame().
    """
    x_list = list(x)
    required = [entity, time, y] + x_list

    missing = [col for col in required if col not in data.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    df = data[required].copy()
    df = df.sort_values([entity, time]).reset_index(drop=False)

    numeric_cols = [y] + x_list
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    group = df.groupby(entity, sort=False)

    diff_cols: dict[str, pd.Series] = {}
    diff_cols[f"d_{y}"] = group[y].diff()

    for col in x_list:
        diff_cols[f"d_{col}"] = group[col].diff()

    diff_df = pd.DataFrame(diff_cols, index=df.index)
    diff_df["_original_index"] = df["index"].to_numpy()

    if drop_missing:
        diff_df = diff_df.dropna().copy()

    if diff_df.empty:
        raise ValueError("No observations remain after first differencing.")

    y_vec = diff_df[f"d_{y}"].to_numpy(dtype=float)
    x_mat = diff_df[[f"d_{col}" for col in x_list]].to_numpy(dtype=float)

    finite_mask = np.isfinite(y_vec) & np.all(np.isfinite(x_mat), axis=1)
    y_vec = y_vec[finite_mask]
    x_mat = x_mat[finite_mask]
    used_index = diff_df.loc[finite_mask, "_original_index"].to_numpy()

    if y_vec.size == 0:
        raise ValueError("No finite observations remain after differencing.")

    if x_mat.shape[1] == 0:
        raise ValueError("At least one regressor is required.")

    beta, _, rank, _ = np.linalg.lstsq(x_mat, y_vec, rcond=None)

    fitted = x_mat @ beta
    resid = y_vec - fitted

    nobs = int(y_vec.shape[0])
    k = int(x_mat.shape[1])
    df_resid = max(nobs - int(rank), 0)
    rss = float(resid @ resid)

    if nobs > 0:
        tss = float(((y_vec - y_vec.mean()) @ (y_vec - y_vec.mean())))
        r2 = float(1.0 - rss / tss) if tss > 0 else float("nan")
    else:
        r2 = float("nan")

    xtx = x_mat.T @ x_mat
    xtx_inv = np.linalg.pinv(xtx)

    if df_resid > 0:
        sigma2 = rss / df_resid
        cov = sigma2 * xtx_inv
        se_arr = np.sqrt(np.maximum(np.diag(cov), 0.0))
    else:
        se_arr = np.full(k, np.nan)

    params = {name: float(value) for name, value in zip(x_list, beta)}
    std_errors = {name: float(value) for name, value in zip(x_list, se_arr)}

    t_stats: dict[str, float] = {}
    p_values: dict[str, float] = {}

    for name in x_list:
        coef = params[name]
        se = std_errors[name]

        if np.isfinite(se) and se > 0:
            stat = float(coef / se)
        else:
            stat = float("nan")

        t_stats[name] = stat
        p_values[name] = _normal_two_sided_pvalue(stat)

    residuals = pd.Series(resid, index=used_index, name="residual")
    fitted_values = pd.Series(fitted, index=used_index, name="fitted")

    return FirstDifferenceResult(
        params=params,
        std_errors=std_errors,
        t_stats=t_stats,
        p_values=p_values,
        residuals=residuals,
        fitted_values=fitted_values,
        y=y,
        x=x_list,
        entity=entity,
        time=time,
        nobs=nobs,
        r2=r2,
        rss=rss,
        df_resid=df_resid,
        rank=int(rank),
    )
