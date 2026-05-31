from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .fixed_effects import (
    CovarianceType,
    _covariance_matrix,
    _normal_pvalues_from_t,
    _require_columns,
)


@dataclass(frozen=True)
class RandomEffectsSpec:
    """Specification for a one-way entity Random Effects panel model.

    This estimator uses a Swamy-Arora-style quasi-demeaning approach. It is a
    transparent native implementation intended for applied workflows and parity
    checks. For highly specialized covariance structures, compare against Stata
    or a dedicated econometrics package.
    """

    dependent: str
    regressors: list[str]
    covariance: CovarianceType = "robust"
    add_constant: bool = True
    name: str = "random_effects"

    def __post_init__(self) -> None:
        if not self.dependent:
            raise ValueError("dependent cannot be empty.")
        if not self.regressors:
            raise ValueError("regressors cannot be empty.")
        if self.covariance not in {"unadjusted", "robust", "clustered"}:
            raise ValueError("covariance must be 'unadjusted', 'robust', or 'clustered'.")


@dataclass(frozen=True)
class RandomEffectsResult:
    spec: RandomEffectsSpec
    nobs: int
    n_entities: int
    rank: int
    df_resid: int
    params: pd.Series
    std_errors: pd.Series
    zstats: pd.Series
    pvalues: pd.Series
    residuals: pd.Series
    fitted_values: pd.Series
    theta_by_entity: pd.Series
    sigma_e2: float
    sigma_alpha2: float
    covariance_type: str
    backend: str
    notes: list[str]

    def summary_frame(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "coef": self.params,
                "std_err": self.std_errors,
                "z": self.zstats,
                "p_value": self.pvalues,
            }
        )

    def to_markdown(self, digits: int = 4) -> str:
        table = self.summary_frame().round(digits)
        lines = [f"# Random-effects result: {self.spec.name}", ""]
        lines.append(f"- Backend: `{self.backend}`")
        lines.append(f"- Observations: `{self.nobs}`")
        lines.append(f"- Entities: `{self.n_entities}`")
        lines.append(f"- Residual df: `{self.df_resid}`")
        lines.append(f"- Covariance: `{self.covariance_type}`")
        lines.append(f"- sigma_e2: `{self.sigma_e2:.{digits}f}`")
        lines.append(f"- sigma_alpha2: `{self.sigma_alpha2:.{digits}f}`")
        if self.notes:
            lines.append("- Notes:")
            for note in self.notes:
                lines.append(f"  - {note}")
        lines.append("")
        lines.append(table.to_markdown())
        return "\n".join(lines)


def _ols_beta(X: np.ndarray, y: np.ndarray) -> np.ndarray:
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    return beta


def _add_constant_frame(X: pd.DataFrame) -> pd.DataFrame:
    return pd.concat(
        [pd.DataFrame({"const": np.ones(len(X), dtype=float)}, index=X.index), X], axis=1
    )


def run_random_effects(
    spec: RandomEffectsSpec,
    data: pd.DataFrame,
    *,
    entity: str,
    time: str,
) -> RandomEffectsResult:
    """Estimate a one-way entity Random Effects model using quasi-demeaning."""

    columns = [entity, time, spec.dependent, *spec.regressors]
    _require_columns(data, columns)
    work = data[columns].dropna().copy().sort_values([entity, time])
    if work.empty:
        raise ValueError("No complete observations remain after dropping missing values.")

    y = work[spec.dependent].astype(float)
    X = work[spec.regressors].astype(float)
    if spec.add_constant:
        X = _add_constant_frame(X)

    X_np = X.to_numpy(dtype=float)
    y_np = y.to_numpy(dtype=float)
    pooled_beta = _ols_beta(X_np, y_np)
    pooled_resid = y_np - X_np @ pooled_beta

    groups = work[entity]
    nobs = len(work)
    n_entities = int(groups.nunique())
    k = X_np.shape[1]

    # Within residual variance from entity-demeaned pooled residuals.
    resid_ser = pd.Series(pooled_resid, index=work.index)
    resid_within = resid_ser - resid_ser.groupby(groups).transform("mean")
    sigma_e2 = float(
        (resid_within.to_numpy() @ resid_within.to_numpy()) / max(nobs - n_entities - k, 1)
    )

    y_bar = y.groupby(groups).transform("mean")
    x_bar = X.groupby(groups).transform("mean")
    between_X = x_bar.groupby(groups).first().to_numpy(dtype=float)
    between_y = y_bar.groupby(groups).first().to_numpy(dtype=float)
    between_beta = _ols_beta(between_X, between_y)
    between_resid = between_y - between_X @ between_beta
    t_bar = float(work.groupby(entity).size().mean())
    sigma_between = float((between_resid @ between_resid) / max(n_entities - k, 1))
    sigma_alpha2 = max(0.0, sigma_between - sigma_e2 / max(t_bar, 1.0))

    counts = work.groupby(entity)[time].transform("size").astype(float)
    theta = 1.0 - np.sqrt(sigma_e2 / np.maximum(counts.to_numpy() * sigma_alpha2 + sigma_e2, 1e-15))
    theta_ser = pd.Series(theta, index=work.index, name="theta")

    y_star = y - theta_ser * y.groupby(groups).transform("mean")
    X_star = X - X.groupby(groups).transform("mean").mul(theta_ser, axis=0)

    Xs = X_star.to_numpy(dtype=float)
    ys = y_star.to_numpy(dtype=float)
    beta = _ols_beta(Xs, ys)
    fitted = X_np @ beta
    residuals = y_np - fitted
    rank = int(np.linalg.matrix_rank(Xs))
    df_resid = int(max(nobs - rank, 0))

    cov = _covariance_matrix(
        Xs,
        ys - Xs @ beta,
        covariance=spec.covariance,
        clusters=groups if spec.covariance == "clustered" else None,
    )
    se = np.sqrt(np.maximum(np.diag(cov), 0.0))
    with np.errstate(divide="ignore", invalid="ignore"):
        zstats = beta / se
    pvalues = _normal_pvalues_from_t(zstats)

    idx = X.columns
    theta_by_entity = theta_ser.groupby(groups).first()
    return RandomEffectsResult(
        spec=spec,
        nobs=int(nobs),
        n_entities=n_entities,
        rank=rank,
        df_resid=df_resid,
        params=pd.Series(beta, index=idx, name="coef"),
        std_errors=pd.Series(se, index=idx, name="std_err"),
        zstats=pd.Series(zstats, index=idx, name="z"),
        pvalues=pd.Series(pvalues, index=idx, name="p_value"),
        residuals=pd.Series(residuals, index=work.index, name="residual"),
        fitted_values=pd.Series(fitted, index=work.index, name="fitted"),
        theta_by_entity=theta_by_entity,
        sigma_e2=sigma_e2,
        sigma_alpha2=sigma_alpha2,
        covariance_type=spec.covariance if spec.covariance != "clustered" else "clustered-entity",
        backend="native-random-effects",
        notes=["One-way entity Random Effects estimated using quasi-demeaning."],
    )
