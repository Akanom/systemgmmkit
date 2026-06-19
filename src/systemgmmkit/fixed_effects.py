from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

import numpy as np
import pandas as pd

CovarianceType = Literal["unadjusted", "robust", "clustered"]


@dataclass(frozen=True)
class FixedEffectsSpec:
    """Structured specification for a static panel fixed-effects model.

    The estimator is intended for the user's main fixed-effects models that sit
    beside dynamic-panel Difference/System GMM robustness checks. It is not a
    replacement for System GMM and should not be used to estimate a lagged-
    dependent-variable model without acknowledging Nickell bias in short panels.
    """

    dependent: str
    regressors: list[str]
    entity_effects: bool = True
    time_effects: bool = True
    covariance: CovarianceType = "clustered"
    cluster: Literal["entity", "time"] = "entity"
    drop_absorbed: bool = True
    name: str = "fixed_effects"

    def __post_init__(self) -> None:
        if not self.dependent:
            raise ValueError("dependent cannot be empty.")
        if not self.regressors:
            raise ValueError("regressors cannot be empty.")
        if self.covariance not in {"unadjusted", "robust", "clustered"}:
            raise ValueError("covariance must be 'unadjusted', 'robust', or 'clustered'.")
        if self.cluster not in {"entity", "time"}:
            raise ValueError("cluster must be 'entity' or 'time'.")

    @property
    def variables(self) -> set[str]:
        return {self.dependent, *self.regressors}


@dataclass(frozen=True)
class FixedEffectsResult:
    """Minimal, backend-independent fixed-effects result object."""

    spec: FixedEffectsSpec
    nobs: int
    rank: int
    df_resid: int
    params: pd.Series
    std_errors: pd.Series
    tstats: pd.Series
    pvalues: pd.Series
    residuals: pd.Series
    fitted_values: pd.Series
    r2_within: float
    covariance_type: str
    backend: str
    notes: list[str]

    def summary_frame(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "coef": self.params,
                "std_err": self.std_errors,
                "t": self.tstats,
                "p_value": self.pvalues,
            }
        )

    def to_markdown(self, digits: int = 4) -> str:
        table = self.summary_frame().round(digits)
        lines = [f"# Fixed-effects result: {self.spec.name}", ""]
        lines.append(f"- Backend: `{self.backend}`")
        lines.append(f"- Observations: `{self.nobs}`")
        lines.append(f"- Residual df: `{self.df_resid}`")
        lines.append(f"- Covariance: `{self.covariance_type}`")
        lines.append(f"- Within R²: `{self.r2_within:.{digits}f}`")
        if self.notes:
            lines.append("- Notes:")
            for note in self.notes:
                lines.append(f"  - {note}")
        lines.append("")
        lines.append(table.to_markdown())
        return "\n".join(lines)


def _require_columns(data: pd.DataFrame, columns: list[str]) -> None:
    missing = [c for c in columns if c not in data.columns]
    if missing:
        raise KeyError(f"Missing required columns: {missing}")


def _build_lsdv_design(
    data: pd.DataFrame,
    *,
    entity: str,
    time: str,
    spec: FixedEffectsSpec,
) -> tuple[pd.Series, pd.DataFrame, pd.DataFrame, list[str]]:
    """Build an explicit least-squares dummy-variable design matrix.

    LSDV is slower than within-transformation for very large panels but is exact
    for both balanced and unbalanced one-/two-way fixed-effects models and keeps
    the implementation auditable.
    """

    columns = [entity, time, spec.dependent, *spec.regressors]
    _require_columns(data, columns)
    work = data[columns].dropna().copy()
    if work.empty:
        raise ValueError("No complete observations remain after dropping missing values.")

    y = work[spec.dependent].astype(float)
    X_parts: list[pd.DataFrame] = []
    notes: list[str] = []

    # Include an intercept before fixed-effect dummies. With drop_first=True
    # for dummy variables, constant + N-1 dummies is the standard LSDV
    # parameterisation and is slope-equivalent to the within estimator used by
    # Stata xtreg, fe. Omitting the constant while also dropping a dummy
    # incorrectly constrains the base group intercept to zero and changes slopes.
    X_parts.append(pd.DataFrame({"const": np.ones(len(work), dtype=float)}, index=work.index))

    # Structural regressors follow; output is restricted to these coefficients
    # plus the constant when it survives collinearity checks.
    X_reg = work[spec.regressors].astype(float)
    X_parts.append(X_reg)

    if spec.entity_effects:
        d_entity = pd.get_dummies(
            work[entity].astype("category"), prefix=f"fe_{entity}", drop_first=True, dtype=float
        )
        if d_entity.shape[1] > 0:
            X_parts.append(d_entity)
        notes.append("Entity fixed effects included via LSDV dummies.")

    if spec.time_effects:
        d_time = pd.get_dummies(
            work[time].astype("category"), prefix=f"fe_{time}", drop_first=True, dtype=float
        )
        if d_time.shape[1] > 0:
            X_parts.append(d_time)
        notes.append("Time fixed effects included via LSDV dummies.")

    X = pd.concat(X_parts, axis=1)

    # Drop exactly collinear columns if requested. This protects against absorbed
    # variables and duplicate regressors without silently changing named slopes.
    if spec.drop_absorbed:
        keep: list[str] = []
        current = np.empty((len(X), 0), dtype=float)
        current_rank = 0
        dropped: list[str] = []
        for col in X.columns:
            candidate = np.column_stack([current, X[col].to_numpy(dtype=float)])
            candidate_rank = int(np.linalg.matrix_rank(candidate))
            if candidate_rank > current_rank:
                keep.append(col)
                current = candidate
                current_rank = candidate_rank
            else:
                dropped.append(col)
        if dropped:
            notes.append(
                f"Dropped absorbed/collinear columns: {', '.join(dropped[:10])}"
                + ("..." if len(dropped) > 10 else "")
            )
        X = X[keep]

    return y, X, work[[entity, time]], notes


def _safe_inverse_xtx(X: np.ndarray) -> np.ndarray:
    xtx = X.T @ X
    return np.linalg.pinv(xtx)


def _normal_pvalues_from_t(tstats: np.ndarray) -> np.ndarray:
    # scipy is a core dependency; imported lazily to keep module load light.
    from scipy import stats

    return 2.0 * stats.norm.sf(np.abs(tstats))


def _covariance_matrix(
    X: np.ndarray,
    residuals: np.ndarray,
    *,
    covariance: CovarianceType,
    clusters: pd.Series | None = None,
) -> np.ndarray:
    nobs, k = X.shape
    xtx_inv = _safe_inverse_xtx(X)

    if covariance == "unadjusted":
        sigma2 = float((residuals @ residuals) / max(nobs - k, 1))
        return sigma2 * xtx_inv

    if covariance == "robust":
        meat = X.T @ ((residuals**2)[:, None] * X)
        correction = nobs / max(nobs - k, 1)
        return correction * xtx_inv @ meat @ xtx_inv

    if clusters is None:
        raise ValueError("clusters must be provided when covariance='clustered'.")

    cluster_values = pd.Series(clusters).to_numpy()
    unique_clusters = pd.unique(cluster_values)
    meat = np.zeros((k, k), dtype=float)
    for c in unique_clusters:
        idx = cluster_values == c
        xg = X[idx, :]
        ug = residuals[idx]
        xu = xg.T @ ug
        meat += np.outer(xu, xu)

    g = len(unique_clusters)
    if g <= 1:
        correction = nobs / max(nobs - k, 1)
    else:
        correction = (g / (g - 1)) * ((nobs - 1) / max(nobs - k, 1))
    return correction * xtx_inv @ meat @ xtx_inv


def run_fixed_effects_native(
    spec: FixedEffectsSpec,
    data: pd.DataFrame,
    *,
    entity: str,
    time: str,
) -> FixedEffectsResult:
    """Estimate a static one-/two-way fixed-effects model using native NumPy.

    This is an exact LSDV estimator for slopes. It is intentionally conservative
    and transparent. For very large panels, install `linearmodels` and use
    `run_fixed_effects(..., prefer_backend="linearmodels")`.
    """

    y, X_df, ids, notes = _build_lsdv_design(data, entity=entity, time=time, spec=spec)
    X = X_df.to_numpy(dtype=float)
    yv = y.to_numpy(dtype=float)

    beta, *_ = np.linalg.lstsq(X, yv, rcond=None)
    fitted = X @ beta
    residuals = yv - fitted
    rank = int(np.linalg.matrix_rank(X))
    df_resid = int(max(len(yv) - rank, 0))

    cluster_series = ids[entity] if spec.cluster == "entity" else ids[time]
    cov = _covariance_matrix(
        X,
        residuals,
        covariance=spec.covariance,
        clusters=cluster_series if spec.covariance == "clustered" else None,
    )
    se = np.sqrt(np.maximum(np.diag(cov), 0.0))
    with np.errstate(divide="ignore", invalid="ignore"):
        tstats = beta / se
    pvalues = _normal_pvalues_from_t(tstats)

    params = pd.Series(beta, index=X_df.columns, name="coef")
    std_errors = pd.Series(se, index=X_df.columns, name="std_err")
    t_ser = pd.Series(tstats, index=X_df.columns, name="t")
    p_ser = pd.Series(pvalues, index=X_df.columns, name="p_value")

    # Return only structural regressors/constant in summary fields; dummies stay internal.
    reported = [c for c in (["const"] + spec.regressors) if c in params.index]
    if not reported:
        raise ValueError("No structural regressors remain after absorption/collinearity checks.")

    # Within R² approximation based on FE-adjusted residual variance relative to
    # demeaned dependent variable under the requested FE structure.
    y_center = y.copy()
    if spec.entity_effects:
        y_center = y_center - y.groupby(ids[entity]).transform("mean")
    if spec.time_effects:
        y_center = y_center - y.groupby(ids[time]).transform("mean")
        if spec.entity_effects:
            y_center = y_center + y.mean()
    denom = float(np.sum(np.asarray(y_center) ** 2))
    r2_within = float(1.0 - (residuals @ residuals) / denom) if denom > 0 else float("nan")

    return FixedEffectsResult(
        spec=spec,
        nobs=int(len(yv)),
        rank=rank,
        df_resid=df_resid,
        params=params.loc[reported],
        std_errors=std_errors.loc[reported],
        tstats=t_ser.loc[reported],
        pvalues=p_ser.loc[reported],
        residuals=pd.Series(residuals, index=y.index, name="residual"),
        fitted_values=pd.Series(fitted, index=y.index, name="fitted"),
        r2_within=r2_within,
        covariance_type=spec.covariance
        if spec.covariance != "clustered"
        else f"clustered-{spec.cluster}",
        backend="native-lsdv",
        notes=notes,
    )


def run_fixed_effects(
    spec: FixedEffectsSpec,
    data: pd.DataFrame,
    *,
    entity: str,
    time: str,
    prefer_backend: Literal["native", "linearmodels"] = "native",
) -> Any:
    """Run a fixed-effects model.

    The native backend is dependency-light and exact for slope coefficients. The
    optional `linearmodels` backend returns the upstream `PanelOLS` result object.
    """

    if prefer_backend == "native":
        return run_fixed_effects_native(spec, data, entity=entity, time=time)

    if prefer_backend != "linearmodels":
        raise ValueError("prefer_backend must be 'native' or 'linearmodels'.")

    try:
        from linearmodels.panel import PanelOLS
    except ModuleNotFoundError as exc:
        raise ImportError(
            "linearmodels is required for the linearmodels backend. Install with: "
            "python -m pip install 'systemgmmkit[fe]'"
        ) from exc

    columns = [entity, time, spec.dependent, *spec.regressors]
    _require_columns(data, columns)
    work = data[columns].dropna().set_index([entity, time]).sort_index()
    y = work[spec.dependent]
    X = work[spec.regressors]
    model = PanelOLS(
        y,
        X,
        entity_effects=spec.entity_effects,
        time_effects=spec.time_effects,
        drop_absorbed=spec.drop_absorbed,
    )
    cov_type = "clustered" if spec.covariance == "clustered" else spec.covariance
    kwargs: dict[str, Any] = {}
    if spec.covariance == "clustered":
        kwargs["cluster_entity" if spec.cluster == "entity" else "cluster_time"] = True
    return model.fit(cov_type=cov_type, **kwargs)
