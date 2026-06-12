from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats


@dataclass(frozen=True)
class DiagnosticResult:
    name: str
    statistic: float
    pvalue: float
    df: int | None = None
    method: str | None = None
    nobs: int | None = None


def _ols(y: np.ndarray, X: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    fitted = X @ beta
    resid = y - fitted
    rss = float(resid.T @ resid)
    return beta, fitted, resid, rss


def _add_constant(X: np.ndarray) -> np.ndarray:
    return np.column_stack([np.ones(X.shape[0]), X])


def _within_transform(df: pd.DataFrame, cols: list[str], entity: str) -> pd.DataFrame:
    out = df[cols].copy()
    return out - out.groupby(df[entity]).transform("mean")


def hausman_fe_re(
    data: pd.DataFrame,
    y: str,
    x: Iterable[str],
    entity: str,
    time: str | None = None,
) -> DiagnosticResult:
    """
    Hausman-style FE vs pooled/RE proxy diagnostic.

    This is intentionally conservative: it gives a usable panel diagnostic
    without pretending to be a full Stata-equivalent xtreg postestimation test.
    Strict Stata parity should still be benchmarked separately.
    """
    x = list(x)
    required = [entity, y, *x]
    df = data[required].dropna().copy()

    yw = _within_transform(df, [y], entity)[y].to_numpy(float)
    Xw = _within_transform(df, x, entity).to_numpy(float)

    b_fe, _, _, _ = _ols(yw, Xw)

    yp = df[y].to_numpy(float)
    Xp = _add_constant(df[x].to_numpy(float))
    b_pool_full, _, resid_pool, _ = _ols(yp, Xp)
    b_pool = b_pool_full[1:]

    diff = b_fe - b_pool

    # Robust fallback variance approximation.
    scale = float(np.var(resid_pool, ddof=max(len(x), 1)))
    XtX_inv = np.linalg.pinv(Xw.T @ Xw)
    V = scale * XtX_inv

    stat = float(diff.T @ np.linalg.pinv(V) @ diff)
    dfree = len(x)
    pvalue = float(1.0 - stats.chi2.cdf(stat, dfree))

    return DiagnosticResult(
        name="hausman_fe_re",
        statistic=stat,
        pvalue=pvalue,
        df=dfree,
        method="FE vs pooled/RE proxy Hausman diagnostic",
        nobs=int(len(df)),
    )


def breusch_pagan_lm(
    data: pd.DataFrame,
    y: str,
    x: Iterable[str],
    entity: str,
    time: str | None = None,
) -> DiagnosticResult:
    """
    Breusch-Pagan LM-style test for panel random effects vs pooled OLS.

    Uses entity mean residual structure from pooled OLS.
    """
    x = list(x)
    required = [entity, y, *x]
    df = data[required].dropna().copy()

    Y = df[y].to_numpy(float)
    X = _add_constant(df[x].to_numpy(float))

    _, _, resid, _ = _ols(Y, X)
    df["_resid"] = resid

    grouped = df.groupby(entity)["_resid"]
    t_bar = grouped.size().mean()
    n = grouped.ngroups

    entity_sum = grouped.sum()
    sigma2 = float(np.mean(resid**2))

    if sigma2 <= 0:
        raise ValueError("Residual variance is zero; LM test undefined.")

    lm = float((n * t_bar / (2 * (t_bar - 1))) * ((np.sum(entity_sum**2) / np.sum(resid**2)) - 1) ** 2)
    pvalue = float(1.0 - stats.chi2.cdf(lm, 1))

    return DiagnosticResult(
        name="breusch_pagan_lm_re_vs_pooled",
        statistic=lm,
        pvalue=pvalue,
        df=1,
        method="Breusch-Pagan LM panel RE diagnostic",
        nobs=int(len(df)),
    )


def wooldridge_serial_correlation(
    data: pd.DataFrame,
    y: str,
    x: Iterable[str],
    entity: str,
    time: str,
) -> DiagnosticResult:
    """
    Wooldridge-style serial-correlation diagnostic for panel data.

    Implementation:
    1. First-difference y and x.
    2. Estimate differenced equation.
    3. Test AR(1) structure in differenced residuals.
    """
    x = list(x)
    required = [entity, time, y, *x]
    df = data[required].dropna().sort_values([entity, time]).copy()

    for col in [y, *x]:
        df[f"D_{col}"] = df.groupby(entity)[col].diff()

    d = df.dropna(subset=[f"D_{y}", *[f"D_{v}" for v in x]]).copy()

    Y = d[f"D_{y}"].to_numpy(float)
    X = d[[f"D_{v}" for v in x]].to_numpy(float)

    _, _, resid, _ = _ols(Y, X)
    d["_resid"] = resid
    d["_lag_resid"] = d.groupby(entity)["_resid"].shift(1)

    r = d.dropna(subset=["_resid", "_lag_resid"])
    if r.empty:
        raise ValueError("Insufficient observations for Wooldridge serial-correlation test.")

    Y2 = r["_resid"].to_numpy(float)
    X2 = _add_constant(r[["_lag_resid"]].to_numpy(float))

    beta, _, e2, _ = _ols(Y2, X2)

    n = len(Y2)
    k = X2.shape[1]
    sigma2 = float((e2.T @ e2) / max(n - k, 1))
    vcov = sigma2 * np.linalg.pinv(X2.T @ X2)
    se = float(np.sqrt(vcov[1, 1]))

    tstat = float(beta[1] / se) if se > 0 else np.nan
    pvalue = float(2 * (1 - stats.t.cdf(abs(tstat), df=max(n - k, 1))))

    return DiagnosticResult(
        name="wooldridge_serial_correlation",
        statistic=tstat,
        pvalue=pvalue,
        df=max(n - k, 1),
        method="Wooldridge-style AR(1) test on differenced residuals",
        nobs=int(n),
    )


def pesaran_cd(
    residuals: pd.DataFrame,
    entity: str,
    time: str,
    resid_col: str = "residual",
) -> DiagnosticResult:
    """
    Pesaran CD test for cross-sectional dependence.

    Input should contain panel residuals with columns:
    entity, time, residual.
    """
    required = [entity, time, resid_col]
    missing = [c for c in required if c not in residuals.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    wide = residuals[required].dropna().pivot(index=time, columns=entity, values=resid_col)
    wide = wide.dropna(axis=1, how="all")

    entities = list(wide.columns)
    n_entities = len(entities)

    if n_entities < 2:
        raise ValueError("Pesaran CD requires at least two entities.")

    corrs = []

    for i in range(n_entities):
        for j in range(i + 1, n_entities):
            pair = wide[[entities[i], entities[j]]].dropna()
            if len(pair) >= 3:
                corr = pair.iloc[:, 0].corr(pair.iloc[:, 1])
                if np.isfinite(corr):
                    corrs.append(corr)

    if not corrs:
        raise ValueError("Insufficient overlapping residuals for Pesaran CD.")

    cd = float(np.sqrt(2 / (n_entities * (n_entities - 1))) * np.sum(corrs))
    pvalue = float(2 * (1 - stats.norm.cdf(abs(cd))))

    return DiagnosticResult(
        name="pesaran_cd_cross_sectional_dependence",
        statistic=cd,
        pvalue=pvalue,
        df=None,
        method="Pesaran CD test",
        nobs=int(wide.shape[0]),
    )


def modified_wald_groupwise_heteroskedasticity(
    residuals: pd.DataFrame,
    entity: str,
    resid_col: str = "residual",
) -> DiagnosticResult:
    """
    Modified Wald-style groupwise heteroskedasticity diagnostic.

    Tests whether entity-level residual variances differ materially.
    """
    required = [entity, resid_col]
    missing = [c for c in required if c not in residuals.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    df = residuals[required].dropna().copy()
    grouped = df.groupby(entity)[resid_col]

    variances = grouped.var(ddof=1).dropna()
    counts = grouped.count().reindex(variances.index)

    if len(variances) < 2:
        raise ValueError("Modified Wald test requires at least two entities.")

    pooled_var = float(np.average(variances, weights=counts))

    if pooled_var <= 0:
        raise ValueError("Pooled residual variance is zero; test undefined.")

    stat = float(np.sum(counts * ((variances - pooled_var) ** 2) / (2 * pooled_var**2)))
    dfree = int(len(variances))
    pvalue = float(1.0 - stats.chi2.cdf(stat, dfree))

    return DiagnosticResult(
        name="modified_wald_groupwise_heteroskedasticity",
        statistic=stat,
        pvalue=pvalue,
        df=dfree,
        method="Modified Wald-style groupwise heteroskedasticity test",
        nobs=int(len(df)),
    )
