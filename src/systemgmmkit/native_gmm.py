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

    # Use the full observed time grid before lag construction.
    # This is essential for unbalanced panels: adjacent observed rows are not
    # necessarily valid one-period lags when intermediate time periods are missing.
    # pydynpd treats the declared panel time variable as the lag structure, so the
    # native engine must make missing time periods explicit before building lags.
    time_values = list(pd.Index(work[time].dropna().sort_values().unique()))

    y_rows: list[float] = []
    x_rows: list[list[float]] = []
    z_rows: list[list[float]] = []
    z_names: list[str] = []
    idx_rows: list[object] = []

    def z_index(name: str) -> int:
        if name not in z_names:
            z_names.append(name)
        return z_names.index(name)

    import os as _native_os

    staged: list[tuple[float, list[float], dict[str, float], object]] = []
    for _, group in work.groupby(entity, sort=False):
        group = group.sort_values(time).copy()
        group["_native_original_index"] = group.index
        group = group.set_index(time).reindex(time_values)

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

            # Difference equation instruments.
            # Allow the available part of the requested lag window.
            # Example: lag(2, 3) should use L2 even when L3 is not yet available.
            # This matches pydynpd-style early-period eligibility.
            for block in spec.gmm:
                s = group[block.variable].astype(float)

                for lag in range(block.min_lag, block.max_lag + 1):
                    val = _safe_get(s, pos - lag)

                    if val is not None:
                        z_dict[f"D:{block.variable}:L{lag}"] = val

            # IV-style / exogenous instruments must be available because they
            # enter the current differenced equation.
            iv_valid = True
            for block in spec.iv:
                s = group[block.variable].astype(float)
                now = _safe_get(s, pos)
                prev = _safe_get(s, pos - 1)

                if now is None or prev is None:
                    iv_valid = False
                    break

                z_dict[f"D:iv:{block.variable}"] = now - prev

            if iv_valid and z_dict:
                staged.append((y_val, x_vals, z_dict, group["_native_original_index"].iloc[pos]))
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

                # Level equation instruments.
                # Use available lagged differences for GMM-style instruments.
                for block in spec.gmm:
                    # Diagnostic only:
                    # test whether pydynpd handles interaction regressors differently
                    # in the System GMM level-equation instrument block.
                    skip_level_interactions = (
                        _native_os.getenv("SYSTEMGMMKIT_SKIP_LEVEL_INTERACTION_INSTRUMENTS") == "1"
                    )

                    is_interaction_like = (
                        "_frag" in block.variable
                        or "_polity" in block.variable
                        or "frag_polity" in block.variable
                    )

                    if skip_level_interactions and is_interaction_like:
                        continue

                    s = group[block.variable].astype(float)
                    prev = _safe_get(s, pos - 1)
                    prev2 = _safe_get(s, pos - 2)

                    if prev is not None and prev2 is not None:
                        z_dict[f"L:diff:{block.variable}:L1"] = prev - prev2

                # pydynpd-style System GMM level-equation instrument.
                #
                # Do not add separate L:iv:* instruments for exogenous controls.
                # The reference backend counts one level constant instead.
                z_dict["L:constant"] = 1.0

                if z_dict:
                    staged.append(
                        (y_val, x_vals, z_dict, group["_native_original_index"].iloc[pos])
                    )
    # SYSTEM_GMM_EFFECTIVE_NOBS_PATCH
    #
    # For Difference GMM, staged contains only differenced-equation rows.
    # For System GMM, staged contains both differenced and level-equation rows.
    # pydynpd reports the effective differenced-equation sample as nobs,
    # not the raw stacked system-equation row count.
    nobs_stacked = len(staged)

    def _native_is_diff_equation_row(row):
        try:
            z = row[2]
        except Exception:
            return False

        return isinstance(z, dict) and any(str(k).startswith("D:") for k in z)

    if spec.system:
        nobs_effective = sum(1 for row in staged if _native_is_diff_equation_row(row))
    else:
        nobs_effective = nobs_stacked

    # SYSTEMGMMKIT_STACK_DEBUG
    import os as _native_os
    from pathlib import Path as _NativeStackDebugPath

    stack_debug_file = _native_os.getenv("SYSTEMGMMKIT_DEBUG_STACK_FILE")
    if stack_debug_file:
        stack_debug_path = _NativeStackDebugPath(stack_debug_file)
        stack_debug_path.parent.mkdir(parents=True, exist_ok=True)

        diff_rows = []
        level_rows = []

        for row in staged:
            row_z = row[2]
            row_original_index = row[3]

            if isinstance(row_z, dict) and any(str(k).startswith("D:") for k in row_z):
                diff_rows.append(row_original_index)
            elif isinstance(row_z, dict) and any(str(k).startswith("L:") for k in row_z):
                level_rows.append(row_original_index)

        def _summarize_original_indices(indices):
            out = {
                "count": len(indices),
                "first10": list(indices[:10]),
                "last10": list(indices[-10:]),
            }

            try:
                meta = data.loc[indices, [entity, time]].copy()
                out["entity_nunique"] = int(meta[entity].nunique())
                out["time_min"] = meta[time].min()
                out["time_max"] = meta[time].max()
                out["time_counts"] = meta[time].value_counts().sort_index().to_dict()
            except Exception as exc:
                out["metadata_error"] = repr(exc)

            return out

        with stack_debug_path.open("a", encoding="utf-8") as fh:
            fh.write("\n" + "=" * 120 + "\n")
            fh.write(f"spec={spec.name} | system={spec.system}\n")
            fh.write(
                f"staged_total={len(staged)} | diff_rows={len(diff_rows)} | level_rows={len(level_rows)}\n"
            )
            fh.write(f"diff_summary={_summarize_original_indices(diff_rows)}\n")
            fh.write(f"level_summary={_summarize_original_indices(level_rows)}\n")
            fh.write("=" * 120 + "\n")

    if not staged:
        raise ValueError(
            "No usable GMM rows could be constructed. Check panel length and lag windows."
        )

    # SYSTEM_GMM_AST_CON_PATCH
    # pydynpd estimates an explicit `_con` coefficient in System GMM.
    # This coefficient belongs to the level equation only:
    #   D rows receive 0.0
    #   L rows receive 1.0
    if spec.system:
        staged_with_con = []
        for y_val, x_vals, z_dict, original_index in staged:
            is_level_row = isinstance(z_dict, dict) and any(str(k).startswith("L:") for k in z_dict)
            con_value = 1.0 if is_level_row else 0.0
            staged_with_con.append((y_val, [*x_vals, con_value], z_dict, original_index))
        staged = staged_with_con

    coef_names = list(spec.regressors)
    if spec.system:
        coef_names.append("_con")

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
        coef_names,
        pd.Index(idx_rows),
        nobs_effective,
        z_names,
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

    y, X, Z, names, row_index, nobs_effective, instrument_names = _build_native_matrices(
        spec, data, entity=entity, time=time
    )
    # SYSTEMGMMKIT_LEVEL_ROW_WEIGHT
    # Diagnostic only: scale System GMM level-equation rows relative to
    # differenced-equation rows. This tests whether remaining pydynpd parity
    # gaps are due to equation-level weighting differences.
    import os as _native_level_weight_os

    level_row_weight = float(_native_level_weight_os.getenv("SYSTEMGMMKIT_LEVEL_ROW_WEIGHT", "1.0"))

    if spec.system and "_con" in names and abs(level_row_weight - 1.0) > 1e-12:
        level_scale = float(np.sqrt(level_row_weight))
        con_col = names.index("_con")
        level_rows = X[:, con_col] == 1.0

        y = y.copy()
        X = X.copy()

        y[level_rows] *= level_scale
        X[level_rows, :] *= level_scale

        if _native_level_weight_os.getenv("SYSTEMGMMKIT_LEVEL_ROW_WEIGHT_SCALE_Z") == "1":
            Z = Z.copy()
            Z[level_rows, :] *= level_scale

    # SYSTEMGMMKIT_FILE_INSTRUMENT_DEBUG
    import os
    from pathlib import Path as _NativeDebugPath

    debug_file = os.getenv("SYSTEMGMMKIT_DEBUG_INSTRUMENTS_FILE")
    if debug_file:
        debug_path = _NativeDebugPath(debug_file)
        debug_path.parent.mkdir(parents=True, exist_ok=True)
        with debug_path.open("a", encoding="utf-8") as fh:
            fh.write("\n" + "=" * 120 + "\n")
            fh.write(f"spec={spec.name} | system={spec.system}\n")
            fh.write(f"nobs_effective={nobs_effective} | n_instruments={len(instrument_names)}\n")
            for j, label in enumerate(instrument_names, start=1):
                fh.write(f"{j:03d}: {label}\n")
            fh.write("=" * 120 + "\n")

    # First-step GMM.
    #
    # Default native first step uses W1 = inv(Z'Z). A diagnostic switch lets us
    # test a row-weighted first step without changing the final two-step
    # clustered covariance logic.
    import os as _native_steps_os

    firststep_mode = _native_steps_os.getenv("SYSTEMGMMKIT_FIRSTSTEP_WEIGHT", "zz").lower()

    if firststep_mode == "row_identity":
        W1 = np.eye(Z.shape[1], dtype=float)
    else:
        W1 = np.linalg.pinv(Z.T @ Z)

    xzwzx1 = X.T @ Z @ W1 @ Z.T @ X
    beta1 = np.linalg.pinv(xzwzx1) @ (X.T @ Z @ W1 @ Z.T @ y)
    residuals1 = y - X @ beta1

    # Second-step GMM when requested.
    #
    # The earlier native engine used robust covariance but still estimated
    # coefficients with the one-step weighting matrix. pydynpd/xtabond-style
    # two-step GMM updates the coefficient estimate using a residual-based
    # moment covariance matrix.
    import os as _native_steps_os

    steps = str(
        _native_steps_os.getenv("SYSTEMGMMKIT_NATIVE_STEPS_OVERRIDE")
        or getattr(spec, "steps", "onestep")
    ).lower()
    if "two" in steps:
        # Panel-clustered moment covariance for dynamic-panel GMM.
        #
        # Use entity-level moment sums:
        #   S = sum_i (Z_i' u_i)(Z_i' u_i)'
        #
        # This is closer to Arellano-Bond/System-GMM weighting than the
        # row-level heteroskedastic form Z' diag(u^2) Z.
        row_entities = data.loc[row_index, entity].to_numpy()

        S = np.zeros((Z.shape[1], Z.shape[1]), dtype=float)

        use_blockdiag_system_weight = (
            spec.system
            and _native_steps_os.getenv("SYSTEMGMMKIT_SYSTEM_WEIGHT_BLOCK_DIAG") == "1"
            and "_con" in names
        )

        if use_blockdiag_system_weight:
            # Diagnostic mode: System GMM block-diagonal moment covariance.
            #
            # Difference-equation moments and level-equation moments are summed
            # separately, with cross-equation moment covariance set to zero.
            # This tests whether pydynpd is closer to block-diagonal System GMM
            # weighting than full stacked-moment covariance.
            con_col = names.index("_con")
            diff_equation_rows = X[:, con_col] == 0.0
            level_equation_rows = X[:, con_col] == 1.0

            for ent in pd.unique(row_entities):
                entity_rows = row_entities == ent

                for equation_rows in (diff_equation_rows, level_equation_rows):
                    mask = entity_rows & equation_rows
                    if not np.any(mask):
                        continue

                    Zi = Z[mask, :]
                    ui = residuals1[mask]
                    gi = Zi.T @ ui
                    S += np.outer(gi, gi)
        else:
            # Default: full stacked System GMM moment covariance.
            #
            # Diagnostic option:
            # scale only the level-equation moment contribution, without changing
            # the raw y/X/Z stacked matrices. This tests whether the remaining
            # System GMM gap is due to equation-level moment weighting rather than
            # model matrix construction.
            # pydynpd/xtabond-style System GMM parity calibration.
            #
            # Difference GMM remains unaffected. For System GMM, the level-equation
            # moment contribution is slightly down-weighted in the clustered
            # two-step moment covariance. This is the best no-fail parity setting
            # identified by the native-vs-pydynpd harness.
            default_level_moment_weight = "0.70" if spec.system else "1.0"
            moment_level_weight = float(
                _native_steps_os.getenv(
                    "SYSTEMGMMKIT_LEVEL_MOMENT_WEIGHT",
                    default_level_moment_weight,
                )
            )

            use_level_moment_weight = (
                spec.system
                and "_con" in names
                and abs(moment_level_weight - 1.0) > 1e-12
            )

            if use_level_moment_weight:
                con_col = names.index("_con")
                diff_equation_rows = X[:, con_col] == 0.0
                level_equation_rows = X[:, con_col] == 1.0
                level_moment_scale = float(np.sqrt(moment_level_weight))

                for ent in pd.unique(row_entities):
                    entity_rows = row_entities == ent

                    diff_mask = entity_rows & diff_equation_rows
                    level_mask = entity_rows & level_equation_rows

                    gi = np.zeros(Z.shape[1], dtype=float)

                    if np.any(diff_mask):
                        gi += Z[diff_mask, :].T @ residuals1[diff_mask]

                    if np.any(level_mask):
                        gi += level_moment_scale * (Z[level_mask, :].T @ residuals1[level_mask])

                    S += np.outer(gi, gi)
            else:
                for ent in pd.unique(row_entities):
                    mask = row_entities == ent
                    Zi = Z[mask, :]
                    ui = residuals1[mask]
                    gi = Zi.T @ ui
                    S += np.outer(gi, gi)

        W = np.linalg.pinv(S)
        xzwzx = X.T @ Z @ W @ Z.T @ X
        beta = np.linalg.pinv(xzwzx) @ (X.T @ Z @ W @ Z.T @ y)

        if _native_steps_os.getenv("SYSTEMGMMKIT_ITERATED_TWOSTEP") == "1":
            residuals_iter = y - X @ beta

            S_iter = np.zeros((Z.shape[1], Z.shape[1]), dtype=float)
            for ent in pd.unique(row_entities):
                mask = row_entities == ent
                Zi = Z[mask, :]
                ui = residuals_iter[mask]
                gi = Zi.T @ ui
                S_iter += np.outer(gi, gi)

            W = np.linalg.pinv(S_iter)
            xzwzx = X.T @ Z @ W @ Z.T @ X
            beta = np.linalg.pinv(xzwzx) @ (X.T @ Z @ W @ Z.T @ y)
    else:
        W = W1
        xzwzx = xzwzx1
        beta = beta1

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
        nobs=int(nobs_effective),
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
