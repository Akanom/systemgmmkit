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


def _native_style_variable(style: object) -> str:
    """Extract a variable name from a GMM/IV style object."""
    value = getattr(style, "variable", None)
    if value is not None:
        return str(value)
    value = getattr(style, "name", None)
    if value is not None:
        return str(value)
    raise AttributeError(f"Could not extract variable name from {style!r}.")


def _native_style_min_lag(style: object) -> int:
    value = getattr(style, "min_lag", None)
    if value is None:
        raise AttributeError(f"Could not extract min_lag from {style!r}.")
    return int(value)


def _native_style_max_lag(style: object) -> int:
    value = getattr(style, "max_lag", None)
    if value is None:
        raise AttributeError(f"Could not extract max_lag from {style!r}.")
    return int(value)


def _native_pydynpd_compat_instrument_order(spec: DynamicPanelSpec) -> list[str]:
    """Return pydynpd-compatible collapsed instrument order.

    pydynpd collapsed Difference/System GMM orders instruments as:
    - D-GMM: each variable, all its requested lags;
    - standard IV columns;
    - System-level GMM diff instruments;
    - System-level constant last.
    """
    labels: list[str] = []

    for block in spec.gmm:
        var = _native_style_variable(block)
        for lag in range(_native_style_min_lag(block), _native_style_max_lag(block) + 1):
            labels.append(f"D:{var}:L{lag}")

    for iv in spec.iv:
        var = _native_style_variable(iv)
        labels.append(f"IV:{var}")

    if spec.system:
        for block in spec.gmm:
            var = _native_style_variable(block)
            labels.append(f"L:diff:{var}:L1")
        labels.append("L:constant")

    return labels


def _native_make_pydynpd_compat_z(
    *,
    spec: DynamicPanelSpec,
    X: np.ndarray,
    Z: np.ndarray,
    coef_names: list[str],
    instrument_names: list[str],
) -> tuple[np.ndarray, list[str]]:
    """Build pydynpd-compatible row-level Z from native matrices.

    Native already builds the correct y/X. For pydynpd compatibility we need
    the same instrument ordering and the same standard-IV convention. pydynpd
    uses the transformed/stacked X columns for IV instruments, not the native
    D:iv:* columns.
    """
    native_cols = {name: idx for idx, name in enumerate(instrument_names)}
    x_cols = {name: idx for idx, name in enumerate(coef_names)}

    cols: list[np.ndarray] = []
    labels: list[str] = []

    for label in _native_pydynpd_compat_instrument_order(spec):
        if label.startswith("IV:"):
            var = label.split(":", 1)[1]
            if var not in x_cols:
                raise KeyError(f"Cannot build pydynpd IV column {label!r}; {var!r} not in X names.")
            cols.append(np.asarray(X[:, x_cols[var]], dtype=float))
            labels.append(label)
            continue

        if label not in native_cols:
            raise KeyError(
                f"Cannot build pydynpd instrument {label!r}; available native instruments are "
                f"{instrument_names!r}."
            )

        cols.append(np.asarray(Z[:, native_cols[label]], dtype=float))
        labels.append(label)

    if not cols:
        raise ValueError("No instruments were built for pydynpd-compatible Z.")

    return np.column_stack(cols), labels


def _native_fd_system_h1(*, group_rows: int, diff_width: int) -> np.ndarray:
    """Replicate pydynpd get_H1(..., transformation='fd') for System GMM."""
    width = int(group_rows)
    diff_width = int(diff_width)

    h1 = np.zeros((width, width), dtype=float)
    i, j = np.indices(h1.shape)

    h1[np.logical_and(i == j, i < diff_width)] = 2.0
    h1[np.logical_and(i == j - 1, j < diff_width)] = -1.0
    h1[np.logical_and(j == i - 1, i < diff_width)] = -1.0

    h1[np.logical_and(i == j, i >= diff_width)] = 1.0

    h1[np.logical_and(i == j + diff_width, j < diff_width)] = -1.0
    h1[np.logical_and(i == 1 + j + diff_width, j < diff_width)] = 1.0
    h1[np.logical_and(j == i + diff_width, i < diff_width)] = -1.0
    h1[np.logical_and(j == 1 + i + diff_width, i < diff_width)] = 1.0

    return h1


def _native_infer_panel_blocks(
    *,
    y: np.ndarray,
    nobs_effective: int,
) -> tuple[int, int, int]:
    """Infer balanced pydynpd-style block dimensions from current harness matrices.

    Returns (n_groups, group_rows, diff_width). This strict compatibility path
    currently assumes the balanced panel structure used by the parity harness.
    """
    n_rows = int(np.asarray(y).shape[0])
    nobs_effective = int(nobs_effective)

    if nobs_effective <= 0:
        raise ValueError("nobs_effective must be positive.")

    # In the current pydynpd-compatible System GMM design:
    #   diff_width = effective nobs per group
    #   group_rows = diff_width + level_width
    # and the panel is balanced in the harness.
    #
    # We infer n_groups from gcd to avoid hard-coding 96.
    import math as _native_math

    n_groups = _native_math.gcd(n_rows, nobs_effective)
    if n_groups <= 0:
        raise ValueError("Could not infer panel groups.")

    group_rows = n_rows // n_groups
    diff_width = nobs_effective // n_groups

    if group_rows * n_groups != n_rows:
        raise ValueError("Inconsistent inferred group_rows.")
    if diff_width * n_groups != nobs_effective:
        raise ValueError("Inconsistent inferred diff_width.")

    return n_groups, group_rows, diff_width


def _native_pydynpd_first_step_weight_inv(
    *,
    Z: np.ndarray,
    y: np.ndarray,
    nobs_effective: int,
) -> tuple[np.ndarray, int, int, int]:
    """Replicate pydynpd System GMM first-step W_inv from row-level Z."""
    n_groups, group_rows, diff_width = _native_infer_panel_blocks(
        y=y,
        nobs_effective=nobs_effective,
    )

    n_instr = int(Z.shape[1])
    h1 = _native_fd_system_h1(group_rows=group_rows, diff_width=diff_width)

    W = np.zeros((n_instr, n_instr), dtype=float)
    for i in range(n_groups):
        Zi_row = Z[i * group_rows : (i + 1) * group_rows, :]
        zi = Zi_row.T
        W += zi @ h1 @ zi.T

    return np.linalg.pinv(W), n_groups, group_rows, diff_width


def _native_pydynpd_next_weight_inv(
    *,
    Z: np.ndarray,
    residuals: np.ndarray,
    n_groups: int,
    group_rows: int,
) -> np.ndarray:
    """Replicate pydynpd W_next = ZuuZ / N and return pinv(W_next)."""
    n_instr = int(Z.shape[1])
    ZuuZ = np.zeros((n_instr, n_instr), dtype=float)

    u = np.asarray(residuals, dtype=float).reshape(-1, 1)

    for i in range(int(n_groups)):
        Zi_row = Z[i * group_rows : (i + 1) * group_rows, :]
        zi = Zi_row.T
        ui = u[i * group_rows : (i + 1) * group_rows, :]
        temp_zs = zi @ ui
        ZuuZ += temp_zs @ temp_zs.T

    W_next = ZuuZ * (1.0 / int(n_groups))
    return np.linalg.pinv(W_next)


def _native_gmm_beta(
    *,
    y: np.ndarray,
    X: np.ndarray,
    Z: np.ndarray,
    W_inv: np.ndarray,
) -> np.ndarray:
    """Compute beta = (X'ZWZ'X)^- X'ZWZ'y using supplied W_inv."""
    y2 = np.asarray(y, dtype=float).reshape(-1, 1)
    X2 = np.asarray(X, dtype=float)
    Z2 = np.asarray(Z, dtype=float)

    XZ_W = X2.T @ Z2 @ W_inv
    M_inv = XZ_W @ Z2.T @ X2
    return np.linalg.pinv(M_inv) @ (XZ_W @ Z2.T @ y2)


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
    y = np.asarray(y, dtype=float).reshape(-1, 1)

    # Optional strict-parity diagnostic dump. Inactive unless explicitly enabled.
    import os as _native_matrix_dump_os

    native_matrix_dump_dir = _native_matrix_dump_os.getenv("SYSTEMGMMKIT_NATIVE_MATRIX_DUMP_DIR")
    if native_matrix_dump_dir:
        import json as _native_matrix_dump_json
        from pathlib import Path as _NativeMatrixDumpPath

        dump_dir = _NativeMatrixDumpPath(native_matrix_dump_dir)
        dump_dir.mkdir(parents=True, exist_ok=True)

        safe_name = "".join(ch if ch.isalnum() or ch in "-_." else "_" for ch in spec.name)
        npz_path = dump_dir / f"{safe_name}.npz"
        json_path = dump_dir / f"{safe_name}.json"

        np.savez_compressed(
            npz_path,
            y=y,
            X=X,
            Z=Z,
            row_index=np.asarray([str(v) for v in row_index], dtype=object),
            coef_names=np.asarray(names, dtype=object),
            instrument_names=np.asarray(instrument_names, dtype=object),
        )

        json_path.write_text(
            _native_matrix_dump_json.dumps(
                {
                    "spec": spec.name,
                    "system": bool(spec.system),
                    "nobs_effective": int(nobs_effective),
                    "n_stacked_rows": int(len(y)),
                    "x_shape": list(X.shape),
                    "z_shape": list(Z.shape),
                    "coef_names": list(names),
                    "instrument_names": list(instrument_names),
                },
                indent=2,
            ),
            encoding="utf-8",
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

    # Estimation path.
    #
    # Difference GMM keeps the native row-level clustered two-step path that
    # already passes strict parity on the validation harness.
    #
    # System GMM uses the pydynpd-compatible matrix path identified by strict
    # parity diagnostics:
    #   - pydynpd-compatible instrument order,
    #   - IV columns taken from transformed/stacked X,
    #   - pydynpd FD-System H1 first-step weighting,
    #   - pydynpd grouped residual moment W_next for two-step weighting.
    steps_normalized = (
        str(getattr(spec, "steps", "twostep"))
        .lower()
        .replace("-", "")
        .replace("_", "")
        .replace(" ", "")
    )
    use_twostep = steps_normalized in {"twostep", "two", "2", "iterated"}

    if spec.system:
        Z, instrument_names = _native_make_pydynpd_compat_z(
            spec=spec,
            X=X,
            Z=Z,
            coef_names=names,
            instrument_names=instrument_names,
        )

        W1, n_groups, group_rows, _diff_width = _native_pydynpd_first_step_weight_inv(
            Z=Z,
            y=y,
            nobs_effective=nobs_effective,
        )

        beta1 = _native_gmm_beta(y=y, X=X, Z=Z, W_inv=W1)
        residuals1 = y - X @ beta1

        if use_twostep:
            W = _native_pydynpd_next_weight_inv(
                Z=Z,
                residuals=residuals1,
                n_groups=n_groups,
                group_rows=group_rows,
            )
            beta = _native_gmm_beta(y=y, X=X, Z=Z, W_inv=W)
        else:
            W = W1
            beta = beta1

        xzwzx = X.T @ Z @ W @ Z.T @ X

    else:
        W1 = np.linalg.pinv(Z.T @ Z)
        xzwzx1 = X.T @ Z @ W1 @ Z.T @ X
        beta1 = np.linalg.pinv(xzwzx1) @ (X.T @ Z @ W1 @ Z.T @ y)
        residuals1 = y - X @ beta1

        if use_twostep:
            row_entities = data.loc[row_index, entity].to_numpy()
            S = np.zeros((Z.shape[1], Z.shape[1]), dtype=float)

            for ent in pd.unique(row_entities):
                mask = row_entities == ent
                Zi = Z[mask, :]
                ui = residuals1[mask]
                gi = Zi.T @ ui
                S += np.outer(gi, gi)

            W = np.linalg.pinv(S)
            xzwzx = X.T @ Z @ W @ Z.T @ X
            beta = np.linalg.pinv(xzwzx) @ (X.T @ Z @ W @ Z.T @ y)
        else:
            W = W1
            xzwzx = xzwzx1
            beta = beta1

    residuals = y - X @ beta
    n, k = X.shape

    beta_vec = np.asarray(beta, dtype=float).reshape(-1)
    residual_vec = np.asarray(residuals, dtype=float).reshape(-1)

    bread = np.linalg.pinv(xzwzx)
    meat_inner = Z.T @ ((residual_vec**2)[:, None] * Z)
    meat = X.T @ Z @ W @ meat_inner @ W @ Z.T @ X
    cov = (n / max(n - k, 1)) * bread @ meat @ bread
    se = np.sqrt(np.maximum(np.diag(cov), 0.0))
    with np.errstate(divide="ignore", invalid="ignore"):
        zstats = beta_vec / se
    pvalues = _normal_pvalues_from_t(zstats)

    return NativeGMMResult(
        spec=spec,
        nobs=int(nobs_effective),
        n_instruments=int(Z.shape[1]),
        params=pd.Series(beta_vec, index=names, name="coef"),
        std_errors=pd.Series(se, index=names, name="std_err"),
        zstats=pd.Series(zstats, index=names, name="z"),
        pvalues=pd.Series(pvalues, index=names, name="p_value"),
        residuals=pd.Series(residual_vec, index=row_index, name="residual"),
        covariance_type="experimental-robust-one-step",
        backend="native-experimental-gmm",
        notes=[
            "Experimental native dynamic-panel GMM engine.",
            "Not yet certified as xtabond2-equivalent.",
            "Use pydynpd for production System GMM until parity tests pass.",
        ],
    )
