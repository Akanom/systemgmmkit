from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .fixed_effects import CovarianceType, _normal_pvalues_from_t, _require_columns


@dataclass(frozen=True)
class PanelIVSpec:
    """Specification for a native panel IV / 2SLS model.

    Entity and time effects are included as LSDV controls in both stages. This is
    transparent and reliable for moderate-size applied panels. Very large panels
    should use a specialized high-dimensional IV backend when available.
    """

    dependent: str
    exog: list[str]
    endogenous: list[str]
    instruments: list[str]
    entity_effects: bool = False
    time_effects: bool = False
    covariance: CovarianceType = "robust"
    add_constant: bool = True
    drop_absorbed: bool = True
    name: str = "panel_2sls"

    def __post_init__(self) -> None:
        if not self.dependent:
            raise ValueError("dependent cannot be empty.")
        if not self.endogenous:
            raise ValueError("At least one endogenous regressor is required.")
        if not self.instruments:
            raise ValueError("At least one excluded instrument is required.")
        if self.covariance not in {"unadjusted", "robust", "clustered"}:
            raise ValueError("covariance must be 'unadjusted', 'robust', or 'clustered'.")


@dataclass(frozen=True)
class PanelIVResult:
    spec: PanelIVSpec
    nobs: int
    rank: int
    df_resid: int
    params: pd.Series
    std_errors: pd.Series
    zstats: pd.Series
    pvalues: pd.Series
    residuals: pd.Series
    fitted_values: pd.Series
    first_stage_r2: dict[str, float]
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
        lines = [f"# Panel IV/2SLS result: {self.spec.name}", ""]
        lines.append(f"- Backend: `{self.backend}`")
        lines.append(f"- Observations: `{self.nobs}`")
        lines.append(f"- Residual df: `{self.df_resid}`")
        lines.append(f"- Covariance: `{self.covariance_type}`")
        if self.first_stage_r2:
            lines.append("- First-stage R²:")
            for var, value in self.first_stage_r2.items():
                lines.append(f"  - `{var}`: `{value:.{digits}f}`")
        if self.notes:
            lines.append("- Notes:")
            for note in self.notes:
                lines.append(f"  - {note}")
        lines.append("")
        lines.append(table.to_markdown())
        return "\n".join(lines)


def _add_constant(X: pd.DataFrame) -> pd.DataFrame:
    return pd.concat(
        [pd.DataFrame({"const": np.ones(len(X), dtype=float)}, index=X.index), X], axis=1
    )


def _drop_collinear(X: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    keep: list[str] = []
    dropped: list[str] = []
    current = np.empty((len(X), 0), dtype=float)
    current_rank = 0
    for col in X.columns:
        candidate = np.column_stack([current, X[col].to_numpy(dtype=float)])
        rank = int(np.linalg.matrix_rank(candidate))
        if rank > current_rank:
            keep.append(col)
            current = candidate
            current_rank = rank
        else:
            dropped.append(col)
    return X[keep], dropped


def _designs(
    spec: PanelIVSpec,
    data: pd.DataFrame,
    *,
    entity: str,
    time: str,
) -> tuple[pd.Series, pd.DataFrame, pd.DataFrame, pd.DataFrame, list[str]]:
    columns = [entity, time, spec.dependent, *spec.exog, *spec.endogenous, *spec.instruments]
    _require_columns(data, columns)
    work = data[columns].dropna().copy().sort_values([entity, time])
    if work.empty:
        raise ValueError("No complete observations remain after dropping missing values.")

    y = work[spec.dependent].astype(float)
    structural = work[[*spec.exog, *spec.endogenous]].astype(float)
    instruments = work[[*spec.exog, *spec.instruments]].astype(float)
    notes: list[str] = []

    if spec.add_constant:
        structural = _add_constant(structural)
        instruments = _add_constant(instruments)

    if spec.entity_effects:
        d_entity = pd.get_dummies(
            work[entity].astype("category"), prefix=f"fe_{entity}", drop_first=True, dtype=float
        )
        structural = pd.concat([structural, d_entity], axis=1)
        instruments = pd.concat([instruments, d_entity], axis=1)
        notes.append("Entity fixed effects included as LSDV controls in both stages.")

    if spec.time_effects:
        d_time = pd.get_dummies(
            work[time].astype("category"), prefix=f"fe_{time}", drop_first=True, dtype=float
        )
        structural = pd.concat([structural, d_time], axis=1)
        instruments = pd.concat([instruments, d_time], axis=1)
        notes.append("Time fixed effects included as LSDV controls in both stages.")

    if spec.drop_absorbed:
        structural, dropped_x = _drop_collinear(structural)
        instruments, dropped_z = _drop_collinear(instruments)
        if dropped_x:
            notes.append(
                f"Dropped collinear structural columns: {', '.join(dropped_x[:10])}"
                + ("..." if len(dropped_x) > 10 else "")
            )
        if dropped_z:
            notes.append(
                f"Dropped collinear instrument columns: {', '.join(dropped_z[:10])}"
                + ("..." if len(dropped_z) > 10 else "")
            )

    return y, structural, instruments, work[[entity, time]], notes


def _cov_2sls(
    X: np.ndarray, Z: np.ndarray, residuals: np.ndarray, covariance: CovarianceType
) -> np.ndarray:
    n, k = X.shape
    ztz_inv = np.linalg.pinv(Z.T @ Z)
    x_pz_x = X.T @ Z @ ztz_inv @ Z.T @ X
    bread = np.linalg.pinv(x_pz_x)
    if covariance == "unadjusted":
        sigma2 = float((residuals @ residuals) / max(n - k, 1))
        return sigma2 * bread
    # Eicker-Huber-White style robust 2SLS covariance.
    middle = X.T @ Z @ ztz_inv @ (Z.T @ ((residuals**2)[:, None] * Z)) @ ztz_inv @ Z.T @ X
    correction = n / max(n - k, 1)
    return correction * bread @ middle @ bread


def run_panel_2sls(
    spec: PanelIVSpec,
    data: pd.DataFrame,
    *,
    entity: str,
    time: str,
) -> PanelIVResult:
    """Estimate a native panel IV/2SLS model with optional LSDV effects."""

    y, X_df, Z_df, ids, notes = _designs(spec, data, entity=entity, time=time)
    X = X_df.to_numpy(dtype=float)
    Z = Z_df.to_numpy(dtype=float)
    yv = y.to_numpy(dtype=float)

    ztz_inv = np.linalg.pinv(Z.T @ Z)
    pz_x = Z @ ztz_inv @ Z.T @ X
    beta = np.linalg.pinv(X.T @ pz_x) @ X.T @ (Z @ ztz_inv @ Z.T @ yv)
    fitted = X @ beta
    residuals = yv - fitted
    rank = int(np.linalg.matrix_rank(X))
    df_resid = int(max(len(yv) - rank, 0))

    cov = _cov_2sls(
        X, Z, residuals, "robust" if spec.covariance == "clustered" else spec.covariance
    )
    se = np.sqrt(np.maximum(np.diag(cov), 0.0))
    with np.errstate(divide="ignore", invalid="ignore"):
        zstats = beta / se
    pvalues = _normal_pvalues_from_t(zstats)

    first_stage_r2: dict[str, float] = {}
    for var in spec.endogenous:
        if var in X_df.columns:
            xj = X_df[var].to_numpy(dtype=float)
            gamma = np.linalg.pinv(Z.T @ Z) @ Z.T @ xj
            fit_j = Z @ gamma
            denom = float(np.sum((xj - xj.mean()) ** 2))
            first_stage_r2[var] = (
                float(1 - np.sum((xj - fit_j) ** 2) / denom) if denom > 0 else float("nan")
            )

    reported = [c for c in ["const", *spec.exog, *spec.endogenous] if c in X_df.columns]
    return PanelIVResult(
        spec=spec,
        nobs=int(len(yv)),
        rank=rank,
        df_resid=df_resid,
        params=pd.Series(beta, index=X_df.columns, name="coef").loc[reported],
        std_errors=pd.Series(se, index=X_df.columns, name="std_err").loc[reported],
        zstats=pd.Series(zstats, index=X_df.columns, name="z").loc[reported],
        pvalues=pd.Series(pvalues, index=X_df.columns, name="p_value").loc[reported],
        residuals=pd.Series(residuals, index=y.index, name="residual"),
        fitted_values=pd.Series(fitted, index=y.index, name="fitted"),
        first_stage_r2=first_stage_r2,
        covariance_type="robust" if spec.covariance == "clustered" else spec.covariance,
        backend="native-panel-2sls",
        notes=notes,
    )
