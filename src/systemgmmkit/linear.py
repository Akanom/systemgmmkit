from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy import stats


def _as_list(values: Sequence[str] | str | None) -> list[str]:
    if values is None:
        return []
    if isinstance(values, str):
        return [values]
    return list(values)


def _unique_preserve_order(values: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            out.append(value)
    return out


@dataclass
class OLSSpec:
    dependent: str
    regressors: Sequence[str]
    controls: Sequence[str] = field(default_factory=list)
    add_constant: bool = True
    covariance: str = "nonrobust"
    cluster: str | None = None
    name: str = "ols"


@dataclass
class PooledOLSSpec(OLSSpec):
    name: str = "pooled_ols"


@dataclass
class LinearModelResult:
    spec: OLSSpec
    params: pd.Series
    covariance: pd.DataFrame
    std_errors: pd.Series
    tvalues: pd.Series
    pvalues: pd.Series
    conf_int_frame: pd.DataFrame
    nobs: int
    df_model: int
    df_resid: int
    df_inference: int | None
    r2: float
    r2_adj: float
    residual_values: pd.Series
    fitted_values_series: pd.Series
    y: pd.Series
    X: pd.DataFrame
    covariance_type: str
    entity: str | None = None
    time: str | None = None
    cluster: str | None = None
    model_name: str | None = None

    @property
    def cov(self) -> pd.DataFrame:
        return self.covariance

    @property
    def vcov_matrix(self) -> pd.DataFrame:
        return self.covariance

    @property
    def fitted(self) -> pd.Series:
        return self.fitted_values_series

    @property
    def resid(self) -> pd.Series:
        return self.residual_values

    @property
    def coefficients(self) -> pd.Series:
        return self.params

    def summary_frame(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "coef": self.params,
                "std_err": self.std_errors,
                "t": self.tvalues,
                "p_value": self.pvalues,
                "ci_lower": self.conf_int_frame["lower"],
                "ci_upper": self.conf_int_frame["upper"],
            }
        )

    def to_markdown(self) -> str:
        frame = self.summary_frame()
        try:
            return frame.to_markdown()
        except Exception:
            return frame.to_string()

    def to_csv(self, path: str | None = None) -> str | None:
        frame = self.summary_frame()
        if path is None:
            return frame.to_csv()
        frame.to_csv(path)
        return None

    def confint(self, alpha: float = 0.05) -> pd.DataFrame:
        critical = stats.t.ppf(1.0 - alpha / 2.0, self.df_resid)
        lower = self.params - critical * self.std_errors
        upper = self.params + critical * self.std_errors
        return pd.DataFrame({"lower": lower, "upper": upper})

    def residuals(self) -> pd.Series:
        return self.residual_values.copy()

    def fitted_values(self) -> pd.Series:
        return self.fitted_values_series.copy()

    def vcov(self) -> pd.DataFrame:
        return self.covariance.copy()

    def predict(self, data: pd.DataFrame | None = None) -> pd.Series:
        if data is None:
            return self.fitted_values()

        X_new = _build_prediction_matrix(
            data=data,
            params_index=list(self.params.index),
            spec=self.spec,
        )
        values = X_new.to_numpy(dtype=float) @ self.params.to_numpy(dtype=float)
        return pd.Series(values, index=X_new.index, name="prediction")

    def lincom(
        self,
        weights: Mapping[str, float] | Sequence[float],
        value: float = 0.0,
        alpha: float = 0.05,
    ) -> dict[str, float]:
        from .postestimation import lincom

        return lincom(self, weights=weights, value=value, alpha=alpha)

    def wald_test(
        self,
        R: Sequence[Sequence[float]],
        q: Sequence[float] | None = None,
    ) -> dict[str, float]:
        from .postestimation import wald_test

        return wald_test(self, R=R, q=q)


def _prepare_frame(
    spec: OLSSpec,
    data: pd.DataFrame,
    entity: str | None = None,
    time: str | None = None,
) -> tuple[pd.Series, pd.DataFrame, pd.DataFrame]:
    regressors = _as_list(spec.regressors)
    controls = _as_list(spec.controls)
    xvars = _unique_preserve_order(regressors + controls)

    required = [spec.dependent] + xvars
    if spec.cluster is not None:
        required.append(spec.cluster)
    if entity is not None:
        required.append(entity)
    if time is not None:
        required.append(time)

    missing = [col for col in required if col not in data.columns]
    if missing:
        raise KeyError(f"Missing required column(s): {missing}")

    frame = data.loc[:, _unique_preserve_order(required)].copy()
    frame = frame.dropna(subset=[spec.dependent] + xvars)

    if frame.empty:
        raise ValueError("No usable observations remain after dropping missing values.")

    y = pd.to_numeric(frame[spec.dependent], errors="coerce")
    X = frame.loc[:, xvars].apply(pd.to_numeric, errors="coerce")

    valid = y.notna()
    for col in X.columns:
        valid &= X[col].notna()

    frame = frame.loc[valid].copy()
    y = y.loc[valid].astype(float)
    X = X.loc[valid].astype(float)

    if spec.add_constant:
        X.insert(0, "_con", 1.0)

    if X.shape[0] <= X.shape[1]:
        raise ValueError(
            "OLS requires more usable observations than estimated parameters. "
            f"Got n={X.shape[0]}, k={X.shape[1]}."
        )

    return y, X, frame


def _build_prediction_matrix(
    data: pd.DataFrame,
    params_index: list[str],
    spec: OLSSpec,
) -> pd.DataFrame:
    regressors = _as_list(spec.regressors)
    controls = _as_list(spec.controls)
    xvars = _unique_preserve_order(regressors + controls)

    missing = [col for col in xvars if col not in data.columns]
    if missing:
        raise KeyError(f"Missing required prediction column(s): {missing}")

    X = data.loc[:, xvars].apply(pd.to_numeric, errors="coerce").astype(float)

    if "_con" in params_index:
        X.insert(0, "_con", 1.0)

    missing_params = [name for name in params_index if name not in X.columns]
    if missing_params:
        raise KeyError(f"Prediction matrix missing parameter column(s): {missing_params}")

    return X.loc[:, params_index]


def _covariance_matrix(
    X: np.ndarray,
    residuals: np.ndarray,
    covariance: str,
    cluster_values: np.ndarray | None = None,
) -> np.ndarray:
    n, k = X.shape
    xtx_inv = np.linalg.pinv(X.T @ X)
    cov_type = covariance.lower().replace("-", "_")

    if cov_type in {"nonrobust", "classic", "classical", "ols"}:
        sigma2 = float(residuals.T @ residuals) / max(n - k, 1)
        return sigma2 * xtx_inv

    if cov_type in {"robust", "hc1"}:
        meat = X.T @ ((residuals**2)[:, None] * X)
        hc0 = xtx_inv @ meat @ xtx_inv
        return (n / max(n - k, 1)) * hc0

    if cov_type == "hc0":
        meat = X.T @ ((residuals**2)[:, None] * X)
        return xtx_inv @ meat @ xtx_inv

    if cov_type in {"cluster", "clustered", "clustered_entity"}:
        if cluster_values is None:
            raise ValueError("Clustered covariance requested but no cluster values were supplied.")

        groups = pd.Series(cluster_values).astype("category")
        codes = groups.cat.codes.to_numpy()
        unique_codes = np.unique(codes[codes >= 0])
        g = len(unique_codes)

        if g <= 1:
            raise ValueError("Clustered covariance requires at least two clusters.")

        meat = np.zeros((k, k), dtype=float)
        for code in unique_codes:
            mask = codes == code
            Xg = X[mask, :]
            eg = residuals[mask]
            score_g = Xg.T @ eg
            meat += np.outer(score_g, score_g)

        correction = (g / (g - 1)) * ((n - 1) / max(n - k, 1))
        return correction * (xtx_inv @ meat @ xtx_inv)

    raise ValueError(
        f"Unsupported covariance type: {covariance!r}. "
        "Supported: nonrobust, robust/HC1, HC0, clustered."
    )


def _fit_linear_model(
    spec: OLSSpec,
    data: pd.DataFrame,
    entity: str | None = None,
    time: str | None = None,
    cluster_override: str | None = None,
) -> LinearModelResult:
    y, X, frame = _prepare_frame(spec=spec, data=data, entity=entity, time=time)

    X_np = X.to_numpy(dtype=float)
    y_np = y.to_numpy(dtype=float)

    beta, *_ = np.linalg.lstsq(X_np, y_np, rcond=None)
    fitted_np = X_np @ beta
    residual_np = y_np - fitted_np

    n = int(X_np.shape[0])
    k = int(X_np.shape[1])
    df_resid = int(n - k)
    df_model = int(k - (1 if "_con" in X.columns else 0))

    covariance_type = spec.covariance
    cluster_col = spec.cluster or cluster_override
    cluster_values = None
    df_inference = df_resid

    if covariance_type.lower().replace("-", "_") in {"cluster", "clustered", "clustered_entity"}:
        if cluster_col is None:
            raise ValueError("Clustered covariance requested but no cluster column was supplied.")
        if cluster_col not in frame.columns:
            raise KeyError(
                f"Cluster column not found after estimation sample filtering: {cluster_col}"
            )
        cluster_values = frame[cluster_col].to_numpy()
        df_inference = int(pd.Series(cluster_values).nunique() - 1)

    cov_np = _covariance_matrix(
        X=X_np,
        residuals=residual_np,
        covariance=covariance_type,
        cluster_values=cluster_values,
    )

    params = pd.Series(beta, index=X.columns, name="coef")
    cov = pd.DataFrame(cov_np, index=X.columns, columns=X.columns)
    se = pd.Series(np.sqrt(np.maximum(np.diag(cov_np), 0.0)), index=X.columns, name="std_err")

    with np.errstate(divide="ignore", invalid="ignore"):
        tvalues = params / se

    pvalues = pd.Series(
        2.0 * stats.t.sf(np.abs(tvalues.to_numpy(dtype=float)), df_inference),
        index=X.columns,
        name="p_value",
    )

    y_mean = float(np.mean(y_np))
    ssr = float(np.sum(residual_np**2))
    tss = float(np.sum((y_np - y_mean) ** 2))

    r2 = 1.0 - ssr / tss if tss > 0 else np.nan
    r2_adj = 1.0 - (1.0 - r2) * ((n - 1) / max(df_resid, 1)) if np.isfinite(r2) else np.nan

    critical = stats.t.ppf(0.975, df_resid)
    conf = pd.DataFrame(
        {
            "lower": params - critical * se,
            "upper": params + critical * se,
        }
    )

    return LinearModelResult(
        spec=spec,
        params=params,
        covariance=cov,
        std_errors=se,
        tvalues=pd.Series(tvalues, index=X.columns, name="t"),
        pvalues=pvalues,
        conf_int_frame=conf,
        nobs=n,
        df_model=df_model,
        df_resid=df_resid,
        df_inference=df_inference,
        r2=float(r2),
        r2_adj=float(r2_adj),
        residual_values=pd.Series(residual_np, index=y.index, name="residual"),
        fitted_values_series=pd.Series(fitted_np, index=y.index, name="fitted"),
        y=y,
        X=X,
        covariance_type=covariance_type,
        entity=entity,
        time=time,
        cluster=cluster_col,
        model_name=spec.name,
    )


def run_ols(
    spec: OLSSpec,
    data: pd.DataFrame,
    entity: str | None = None,
    time: str | None = None,
) -> LinearModelResult:
    return _fit_linear_model(spec=spec, data=data, entity=entity, time=time)


def run_pooled_ols(
    spec: PooledOLSSpec,
    data: pd.DataFrame,
    entity: str | None = None,
    time: str | None = None,
) -> LinearModelResult:
    cluster_override = None
    cov = spec.covariance.lower().replace("-", "_")

    if cov in {"cluster", "clustered", "clustered_entity"} and spec.cluster is None:
        cluster_override = entity

    return _fit_linear_model(
        spec=spec,
        data=data,
        entity=entity,
        time=time,
        cluster_override=cluster_override,
    )
