from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .fixed_effects import _normal_pvalues_from_t, _require_columns
from .spec import DynamicPanelSpec


@dataclass(frozen=True)
class NativeGMMResult:
    """Experimental native dynamic-panel GMM result.

    This engine is intentionally marked experimental. It provides a transparent
    one-step implementation useful for development and parity scaffolding, but
    pydynpd remains the recommended production backend until documented parity
    tests against xtabond2 are passed.
    """

    spec: DynamicPanelSpec
    nobs: int
    n_instruments: int
    params: pd.Series
    std_errors: pd.Series
    zstats: pd.Series
    pvalues: pd.Series
    residuals: pd.Series
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
        lines = [f"# Native dynamic-panel GMM result: {self.spec.name}", ""]
        lines.append(f"- Backend: `{self.backend}`")
        lines.append(f"- Observations: `{self.nobs}`")
        lines.append(f"- Instruments: `{self.n_instruments}`")
        lines.append(f"- Covariance: `{self.covariance_type}`")
        if self.notes:
            lines.append("- Notes:")
            for note in self.notes:
                lines.append(f"  - {note}")
        lines.append("")
        lines.append(table.to_markdown())
        return "\n".join(lines)


def _parse_lagged_regressor(name: str) -> tuple[int, str] | None:
    if not name.startswith("L") or "." not in name:
        return None
    lag_text, var = name.split(".", 1)
    try:
        return int(lag_text[1:]), var
    except ValueError:
        return None


def _required_variables(spec: DynamicPanelSpec) -> list[str]:
    variables = {spec.dependent}
    for reg in spec.regressors:
        parsed = _parse_lagged_regressor(reg)
        variables.add(parsed[1] if parsed else reg)
    for block in spec.gmm:
        variables.add(block.variable)
    for block in spec.iv:
        variables.add(block.variable)
    return sorted(variables)


def _safe_get(series: pd.Series, pos: int) -> float | None:
    if pos < 0 or pos >= len(series):
        return None
    value = series.iloc[pos]
    if pd.isna(value):
        return None
    return float(value)


def _build_native_matrices(
    spec: DynamicPanelSpec,
    data: pd.DataFrame,
    *,
    entity: str,
    time: str,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[str], pd.Index]:
    raw_vars = _required_variables(spec)
    _require_columns(data, [entity, time, *raw_vars])
    work = data[[entity, time, *raw_vars]].dropna().copy().sort_values([entity, time])

    y_rows: list[float] = []
    x_rows: list[list[float]] = []
    z_rows: list[list[float]] = []
    z_names: list[str] = []
    idx_rows: list[object] = []

    def z_index(name: str) -> int:
        if name not in z_names:
            z_names.append(name)
        return z_names.index(name)

    staged: list[tuple[float, list[float], dict[str, float], object]] = []
    for _, group in work.groupby(entity, sort=False):
        group = group.sort_values(time)
        dep = group[spec.dependent].astype(float)
        for pos in range(2, len(group)):
            dy = _safe_get(dep, pos)
            dy_l1 = _safe_get(dep, pos - 1)
            if dy is None or dy_l1 is None:
                continue
            y_val = dy - dy_l1
            x_vals: list[float] = []
            valid = True
            for reg in spec.regressors:
                parsed = _parse_lagged_regressor(reg)
                if parsed:
                    lag, var = parsed
                    s = group[var].astype(float)
                    now = _safe_get(s, pos - lag)
                    prev = _safe_get(s, pos - lag - 1)
                else:
                    s = group[reg].astype(float)
                    now = _safe_get(s, pos)
                    prev = _safe_get(s, pos - 1)
                if now is None or prev is None:
                    valid = False
                    break
                x_vals.append(now - prev)
            if not valid:
                continue
            z_dict: dict[str, float] = {}
            for block in spec.gmm:
                s = group[block.variable].astype(float)
                for lag in range(block.min_lag, block.max_lag + 1):
                    val = _safe_get(s, pos - lag)
                    if val is not None:
                        z_dict[f"D:{block.variable}:L{lag}"] = val
            for block in spec.iv:
                s = group[block.variable].astype(float)
                now = _safe_get(s, pos)
                prev = _safe_get(s, pos - 1)
                if now is not None and prev is not None:
                    z_dict[f"D:iv:{block.variable}"] = now - prev
            if z_dict:
                staged.append((y_val, x_vals, z_dict, group.index[pos]))

        if spec.system:
            for pos in range(1, len(group)):
                y_val = _safe_get(dep, pos)
                if y_val is None:
                    continue
                x_vals = []
                valid = True
                for reg in spec.regressors:
                    parsed = _parse_lagged_regressor(reg)
                    if parsed:
                        lag, var = parsed
                        val = _safe_get(group[var].astype(float), pos - lag)
                    else:
                        val = _safe_get(group[reg].astype(float), pos)
                    if val is None:
                        valid = False
                        break
                    x_vals.append(val)
                if not valid:
                    continue
                z_dict = {}
                for block in spec.gmm:
                    s = group[block.variable].astype(float)
                    prev = _safe_get(s, pos - 1)
                    prev2 = _safe_get(s, pos - 2)
                    if prev is not None and prev2 is not None:
                        z_dict[f"L:diff:{block.variable}:L1"] = prev - prev2
                for block in spec.iv:
                    val = _safe_get(group[block.variable].astype(float), pos)
                    if val is not None:
                        z_dict[f"L:iv:{block.variable}"] = val
                if z_dict:
                    staged.append((y_val, x_vals, z_dict, group.index[pos]))

    if not staged:
        raise ValueError(
            "No usable GMM rows could be constructed. Check panel length and lag windows."
        )

    for y_val, x_vals, z_dict, row_idx in staged:
        y_rows.append(y_val)
        x_rows.append(x_vals)
        z_rows.append([0.0] * len(z_names))
        for key, value in z_dict.items():
            j = z_index(key)
            if j >= len(z_rows[-1]):
                z_rows[-1].extend([0.0] * (j + 1 - len(z_rows[-1])))
            z_rows[-1][j] = value
        idx_rows.append(row_idx)

    max_z = len(z_names)
    Z = np.zeros((len(z_rows), max_z), dtype=float)
    for i, row in enumerate(z_rows):
        Z[i, : len(row)] = row
    return (
        np.asarray(y_rows, dtype=float),
        np.asarray(x_rows, dtype=float),
        Z,
        spec.regressors,
        pd.Index(idx_rows),
    )


def run_native_dynamic_panel_gmm(
    spec: DynamicPanelSpec,
    data: pd.DataFrame,
    *,
    entity: str,
    time: str,
    windmeijer: bool = False,
) -> NativeGMMResult:
    """Run an experimental native one-step Difference/System GMM estimator.

    Windmeijer correction is deliberately not implemented yet because an
    incorrect correction would be worse than no correction. Use pydynpd for
    production two-step Windmeijer-style inference until native parity is done.
    """

    if windmeijer:
        raise NotImplementedError(
            "Native Windmeijer correction is not certified yet. Use pydynpd for production two-step robust inference."
        )

    y, X, Z, names, row_index = _build_native_matrices(spec, data, entity=entity, time=time)
    W = np.linalg.pinv(Z.T @ Z)
    xzwzx = X.T @ Z @ W @ Z.T @ X
    beta = np.linalg.pinv(xzwzx) @ (X.T @ Z @ W @ Z.T @ y)
    residuals = y - X @ beta
    n, k = X.shape

    bread = np.linalg.pinv(xzwzx)
    meat = X.T @ Z @ W @ (Z.T @ ((residuals**2)[:, None] * Z)) @ W @ Z.T @ X
    cov = (n / max(n - k, 1)) * bread @ meat @ bread
    se = np.sqrt(np.maximum(np.diag(cov), 0.0))
    with np.errstate(divide="ignore", invalid="ignore"):
        zstats = beta / se
    pvalues = _normal_pvalues_from_t(zstats)

    return NativeGMMResult(
        spec=spec,
        nobs=int(n),
        n_instruments=int(Z.shape[1]),
        params=pd.Series(beta, index=names, name="coef"),
        std_errors=pd.Series(se, index=names, name="std_err"),
        zstats=pd.Series(zstats, index=names, name="z"),
        pvalues=pd.Series(pvalues, index=names, name="p_value"),
        residuals=pd.Series(residuals, index=row_index, name="residual"),
        covariance_type="experimental-robust-one-step",
        backend="native-experimental-gmm",
        notes=[
            "Experimental native dynamic-panel GMM engine.",
            "Not yet certified as xtabond2-equivalent.",
            "Use pydynpd for production System GMM until parity tests pass.",
        ],
    )
