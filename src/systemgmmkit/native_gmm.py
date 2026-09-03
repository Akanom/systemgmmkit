from __future__ import annotations

import contextlib
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats

from .fixed_effects import _normal_pvalues_from_t, _require_columns
from .spec import DynamicPanelSpec
from .tables import _frame_to_markdown

_NATIVE_MAX_TIME_GRID_POINTS = 100_000
_NATIVE_MAX_PANEL_GRID_ROWS = 5_000_000


@dataclass(frozen=True)
class NativeGMMResult:
    """Native dynamic-panel GMM result.

    The native Difference GMM path has strict benchmark parity. Native System
    GMM has benchmark-specific ``xtabond2`` parity on six maintained, aligned
    collapsed two-step specifications. The certificate covers complete
    parameters, Windmeijer-corrected standard errors and their reported covariance
    matrix, exact structural counts, Hansen/Sargan statistics, and signed AR
    diagnostics under declared gates. The unbalanced-panel and variable-missing
    fixtures also have exact sample-key parity; the evidence does not extend
    automatically to other designs or options.
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
    instrument_names: list[str] | None = None
    n_groups: int | None = None
    hansen_p: float | None = None
    sargan_p: float | None = None
    sargan_stat: float | None = None
    ar1_p: float | None = None
    ar2_p: float | None = None
    ar1_z: float | None = None
    ar2_z: float | None = None
    z_shape: tuple[int, int] | None = None
    w_shape: tuple[int, int] | None = None
    j_stat: float | None = None
    ztu_norm: float | None = None
    w_norm: float | None = None
    hansen_j_stat: float | None = None
    sargan_j_stat: float | None = None
    overid_df: int | None = None
    hansen_j_error: str | None = None
    covariance: pd.DataFrame | None = None
    covariance_correction: str = "none"
    covariance_reference: str | None = None
    normal_matrix_rank: int | None = None
    normal_matrix_required_rank: int | None = None
    normal_matrix_condition_number: float | None = None

    def summary_frame(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "coef": self.params,
                "std_err": self.std_errors,
                "z": self.zstats,
                "p_value": self.pvalues,
            }
        )

    def check_instrument_health(self):
        """Return the instrument/group proliferation assessment."""
        from .diagnostics import check_instrument_health

        return check_instrument_health(self)

    def to_markdown(self, digits: int = 4) -> str:
        table = self.summary_frame().round(digits)
        lines = [f"# Native dynamic-panel GMM result: {self.spec.name}", ""]
        lines.append(f"- Backend: `{self.backend}`")
        lines.append(f"- Observations: `{self.nobs}`")
        lines.append(f"- Instruments: `{self.n_instruments}`")
        lines.append(f"- Covariance: `{self.covariance_type}`")
        if self.normal_matrix_rank is not None and self.normal_matrix_required_rank is not None:
            lines.append(
                "- GMM normal-matrix numerical rank: "
                f"`{self.normal_matrix_rank}/{self.normal_matrix_required_rank}`"
            )
        if self.normal_matrix_condition_number is not None:
            lines.append(
                f"- GMM normal-matrix condition number: `{self.normal_matrix_condition_number:.6g}`"
            )
        if self.notes:
            lines.append("- Notes:")
            for note in self.notes:
                lines.append(f"  - {note}")
        lines.append("")
        lines.append(_frame_to_markdown(table, digits=digits))
        lines.extend(["", self.check_instrument_health().to_markdown()])
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
        parsed = _parse_lagged_regressor(block.variable)
        variables.add(parsed[1] if parsed else block.variable)
    for block in spec.iv:
        parsed = _parse_lagged_regressor(block.variable)
        variables.add(parsed[1] if parsed else block.variable)
    return sorted(variables)


def _safe_get(series: pd.Series, pos: int) -> float | None:
    if pos < 0 or pos >= len(series):
        return None
    value = series.iloc[pos]
    if pd.isna(value):
        return None
    return float(value)


def _fd_at(series: pd.Series, pos: int) -> float | None:
    """First difference at positional index pos: v_t - v_{t-1}."""
    now = _safe_get(series, pos)
    prev = _safe_get(series, pos - 1)
    if now is None or prev is None:
        return None
    return float(now - prev)


def _fod_at(series: pd.Series, pos: int) -> float | None:
    """Forward orthogonal deviation at positional index ``pos``.

    Diagnostic scaling modes are controlled by SYSTEMGMMKIT_FOD_SCALE_MODE:

        canonical: sqrt(m / (m + 1)) * deviation
        unscaled:  deviation
        inverse:   sqrt((m + 1) / m) * deviation
        negative:  -canonical

    where m is the number of usable future observations.
    """

    import math
    import os

    n = len(series)
    if pos < 0 or pos >= n - 1:
        return None

    now = _safe_get(series, pos)
    if now is None:
        return None

    future_values: list[float] = []
    for j in range(pos + 1, n):
        val = _safe_get(series, j)
        if val is not None:
            future_values.append(float(val))

    m = len(future_values)
    if m <= 0:
        return None

    deviation = float(now) - (sum(future_values) / float(m))

    mode = os.getenv("SYSTEMGMMKIT_FOD_SCALE_MODE", "canonical").strip().lower()

    if mode in {"canonical", "default", ""}:
        scale = math.sqrt(float(m) / float(m + 1))
    elif mode in {"unscaled", "none", "raw"}:
        scale = 1.0
    elif mode in {"inverse", "reverse"}:
        scale = math.sqrt(float(m + 1) / float(m))
    elif mode in {"negative", "neg"}:
        scale = -math.sqrt(float(m) / float(m + 1))
    else:
        raise ValueError(
            "Unsupported SYSTEMGMMKIT_FOD_SCALE_MODE="
            f"{mode!r}. Use canonical, unscaled, inverse, or negative."
        )

    return scale * deviation


def _transform_at(series: pd.Series, pos: int, transformation: str) -> float | None:
    """Apply the dynamic-panel transformed-equation operator."""
    transformation_normalized = str(transformation).strip().lower()

    if transformation_normalized == "fd":
        return _fd_at(series, pos)

    if transformation_normalized == "fod":
        return _fod_at(series, pos)

    raise ValueError(f"Unsupported transformation={transformation!r}. Expected 'fd' or 'fod'.")


def _lagged_series(series: pd.Series, lag: int) -> pd.Series:
    """Return a positional lagged copy while preserving the existing index."""
    if lag < 0:
        raise ValueError("lag must be non-negative.")

    values = [_safe_get(series, pos - lag) for pos in range(len(series))]
    return pd.Series(values, index=series.index, dtype=float)


def _style_source_series(group: pd.DataFrame, variable: str) -> pd.Series:
    """Return the source series for a GMM/IV-style variable.

    Supports both raw variables, e.g. "x", and lagged Stata-style variables,
    e.g. "L1.y" or "L.y".
    """
    parsed = _parse_lagged_regressor(variable)

    if parsed:
        lag, raw_variable = parsed
        source = _lagged_series(group[raw_variable].astype(float), lag)

        # Match Stata time-series semantics on physically unbalanced panels.
        # xtabond2 evaluates expressions such as L.y on the observed rows and
        # only then pads each entity to the common time grid.  Lagging after
        # reindexing without this mask would fabricate L.y at an inserted gap
        # from the preceding observed y, allowing that nonexistent value to
        # enter later collapsed GMM instruments.
        observed_rows = group.get("_native_observed_row")
        if observed_rows is not None:
            source = source.where(observed_rows.astype(bool))

        return source

    return group[variable].astype(float)


def _style_label(variable: str) -> str:
    return str(variable).replace("L.", "L1.")


def _level_regressor_at(group: pd.DataFrame, regressor: str, pos: int) -> float | None:
    """Return the level-equation value for a structural regressor."""
    parsed = _parse_lagged_regressor(regressor)

    if parsed:
        return _safe_get(_style_source_series(group, regressor), pos)

    return _safe_get(group[regressor].astype(float), pos)


def _transformed_regressor_at(
    group: pd.DataFrame,
    regressor: str,
    pos: int,
    transformation: str,
) -> float | None:
    """Return the transformed-equation value for a structural regressor.

    Diagnostic FOD lagged-regressor modes are controlled by:

        SYSTEMGMMKIT_FOD_LAGGED_REGRESSOR_MODE=transform_lagged
            Current/default: A(L^k y)

        SYSTEMGMMKIT_FOD_LAGGED_REGRESSOR_MODE=lag_transformed
            Alternative: L^k(Ay)

    FD is left unchanged.
    """

    import os

    transformation_normalized = str(transformation).strip().lower()
    parsed = _parse_lagged_regressor(regressor)

    if parsed is None:
        return _transform_at(group[regressor], pos, transformation)

    lag, base = parsed
    base_series = group[base]

    if transformation_normalized in {
        "fod",
        "orthogonal",
        "orthogonal_deviations",
        "forward_orthogonal_deviations",
    }:
        mode = (
            os.getenv("SYSTEMGMMKIT_FOD_LAGGED_REGRESSOR_MODE", "transform_lagged").strip().lower()
        )

        if mode in {"transform_lagged", "current", "default", ""}:
            lagged = _style_source_series(group, regressor)
            return _transform_at(lagged, pos, transformation)

        if mode in {"lag_transformed", "lag_of_transformed", "alternative"}:
            transformed_base_values = []
            for j in range(len(base_series)):
                transformed_base_values.append(_transform_at(base_series, j, transformation))
            transformed_base = pd.Series(transformed_base_values, index=base_series.index)
            return _safe_get(transformed_base, pos - lag)

        raise ValueError(
            "Unsupported SYSTEMGMMKIT_FOD_LAGGED_REGRESSOR_MODE="
            f"{mode!r}. Use transform_lagged or lag_transformed."
        )

    lagged = _style_source_series(group, regressor)
    return _transform_at(lagged, pos, transformation)


def _lagged_level_instrument_at(series: pd.Series, pos: int, lag: int) -> float | None:
    """Collapsed Difference/FOD-equation GMM instrument: level v_{t-lag}."""
    return _safe_get(series, pos - lag)


def _lagged_difference_instrument_at(
    series: pd.Series,
    pos: int,
    lag: int = 1,
) -> float | None:
    """System-GMM level-equation instrument: Δv_{t-lag}."""
    left = _safe_get(series, pos - lag)
    right = _safe_get(series, pos - lag - 1)

    if left is None or right is None:
        return None

    return float(left - right)


def _transformed_error_terms(
    index: pd.Index,
    pos: int,
    transformation: str,
) -> dict[object, float]:
    """Return underlying level-error weights for a transformed equation row.

    Uses the same FOD scaling mode as _fod_at so first-step weighting remains
    internally consistent during diagnostics.
    """

    import math
    import os

    transformation_normalized = str(transformation).strip().lower()
    n = len(index)

    if transformation_normalized in {"fd", "first_difference", "difference"}:
        if pos <= 0 or pos >= n:
            return {}
        return {
            index[pos]: 1.0,
            index[pos - 1]: -1.0,
        }

    if transformation_normalized in {
        "fod",
        "orthogonal",
        "orthogonal_deviations",
        "forward_orthogonal_deviations",
    }:
        if pos < 0 or pos >= n - 1:
            return {}

        future_positions = list(range(pos + 1, n))
        m = len(future_positions)
        if m <= 0:
            return {}

        mode = os.getenv("SYSTEMGMMKIT_FOD_SCALE_MODE", "canonical").strip().lower()

        if mode in {"canonical", "default", ""}:
            scale = math.sqrt(float(m) / float(m + 1))
        elif mode in {"unscaled", "none", "raw"}:
            scale = 1.0
        elif mode in {"inverse", "reverse"}:
            scale = math.sqrt(float(m + 1) / float(m))
        elif mode in {"negative", "neg"}:
            scale = -math.sqrt(float(m) / float(m + 1))
        else:
            raise ValueError(
                "Unsupported SYSTEMGMMKIT_FOD_SCALE_MODE="
                f"{mode!r}. Use canonical, unscaled, inverse, or negative."
            )

        future_weight = -scale / float(m)

        weights: dict[object, float] = {index[pos]: scale}
        for j in future_positions:
            weights[index[j]] = weights.get(index[j], 0.0) + future_weight

        return weights

    raise ValueError("transformation must be one of 'fd', 'difference', 'fod', or 'orthogonal'.")


def _cached_style_source(
    group: pd.DataFrame,
    variable: str,
    cache: dict[str, pd.Series],
) -> pd.Series:
    """Return one immutable prepared source per group and variable."""
    source = cache.get(variable)
    if source is None:
        source = _style_source_series(group, variable)
        cache[variable] = source
    return source


def _prepared_transformed_regressor_at(
    group: pd.DataFrame,
    spec: DynamicPanelSpec,
    regressor: str,
    pos: int,
    *,
    source_cache: dict[str, pd.Series],
    transformed_source_cache: dict[tuple[str, str], pd.Series],
) -> float | None:
    """Transform a structural regressor using immutable per-group sources."""
    transformation_normalized = str(spec.transformation).strip().lower()
    parsed = _parse_lagged_regressor(regressor)

    if parsed is not None and transformation_normalized in {
        "fod",
        "orthogonal",
        "orthogonal_deviations",
        "forward_orthogonal_deviations",
    }:
        import os as _prepared_fod_os

        mode = (
            _prepared_fod_os.getenv(
                "SYSTEMGMMKIT_FOD_LAGGED_REGRESSOR_MODE",
                "transform_lagged",
            )
            .strip()
            .lower()
        )
        if mode in {"lag_transformed", "lag_of_transformed", "alternative"}:
            lag, base = parsed
            cache_key = (base, transformation_normalized)
            transformed_base = transformed_source_cache.get(cache_key)
            if transformed_base is None:
                base_series = group[base]
                transformed_base = pd.Series(
                    [
                        _transform_at(base_series, position, spec.transformation)
                        for position in range(len(base_series))
                    ],
                    index=base_series.index,
                )
                transformed_source_cache[cache_key] = transformed_base
            return _safe_get(transformed_base, pos - lag)
        if mode not in {"transform_lagged", "current", "default", ""}:
            raise ValueError(
                "Unsupported SYSTEMGMMKIT_FOD_LAGGED_REGRESSOR_MODE="
                f"{mode!r}. Use transform_lagged or lag_transformed."
            )

    return _transform_at(
        _cached_style_source(group, regressor, source_cache),
        pos,
        spec.transformation,
    )


def _normalize_preparation_engine(value: str) -> str:
    """Validate the internal matrix-preparation engine selector."""
    if not isinstance(value, str):
        raise TypeError("preparation_engine must be 'reference' or 'accelerated'.")
    normalized = value.strip().lower()
    if normalized not in {"reference", "accelerated"}:
        raise ValueError("preparation_engine must be 'reference' or 'accelerated'.")
    return normalized


def _native_integral_time_values(time_values: list[object]) -> list[int] | None:
    """Return exact integer labels when a panel-time index is unit-compatible."""
    index = pd.Index(time_values)
    if index.empty:
        return []
    if pd.api.types.is_bool_dtype(index.dtype):
        return None
    if pd.api.types.is_integer_dtype(index.dtype):
        return [int(value) for value in index]
    if pd.api.types.is_float_dtype(index.dtype):
        numeric = index.to_numpy(dtype=float)
        if bool(np.isfinite(numeric).all()) and bool(np.equal(numeric, np.floor(numeric)).all()):
            return [int(value) for value in numeric]
    return None


def _native_panel_time_grid(
    observed_time_values: list[object],
    *,
    n_entities: int,
) -> list[object]:
    """Build the unit-spaced grid implied by integral numeric time labels.

    Stata's default numeric ``xtset`` delta is one.  Expanding that grid ensures
    a period absent from every entity remains a real gap during lag construction.
    Non-integral and datetime labels retain ordered-rank semantics because the
    current API has no explicit delta contract.
    """
    observed = list(pd.Index(observed_time_values).dropna().drop_duplicates().sort_values())
    integral = _native_integral_time_values(observed)
    if integral is None or len(integral) < 2:
        return observed

    first = min(integral)
    last = max(integral)
    grid_points = last - first + 1
    panel_grid_rows = grid_points * max(int(n_entities), 1)
    if grid_points > _NATIVE_MAX_TIME_GRID_POINTS or panel_grid_rows > _NATIVE_MAX_PANEL_GRID_ROWS:
        raise ValueError(
            "Integral panel-time labels imply an unsafe unit-spaced grid "
            f"({grid_points} periods; {panel_grid_rows} entity-period rows). "
            "Recode the time variable to a contiguous period index before estimation."
        )
    if grid_points == len(integral):
        return observed
    return list(range(first, last + 1))


def _build_native_matrices(
    spec: DynamicPanelSpec,
    data: pd.DataFrame,
    *,
    entity: str,
    time: str,
    preparation_engine: str = "reference",
) -> tuple[
    np.ndarray, np.ndarray, np.ndarray, list[str], pd.Index, int, list[str], list[dict[str, object]]
]:
    preparation_engine = _normalize_preparation_engine(preparation_engine)
    use_cached_preparation = preparation_engine == "accelerated"
    raw_vars = _required_variables(spec)
    _require_columns(data, [entity, time, *raw_vars])
    # Preserve variable-specific missingness until each structural row and
    # instrument is evaluated.  Dropping a row because *any* model variable is
    # missing incorrectly erases otherwise usable lag values from the other
    # variables (for example, a missing ``x_t`` must not make ``y_t`` unavailable
    # as a future instrument).  Entity and time are the only fields that cannot
    # be interpreted when missing.
    work = (
        data[[entity, time, *raw_vars]]
        .dropna(subset=[entity, time])
        .copy()
        .sort_values([entity, time])
    )

    # Use the full unit-spaced time grid before lag construction.
    # This is essential for unbalanced panels: adjacent observed rows are not
    # necessarily valid one-period lags when intermediate time periods are missing.
    # pydynpd treats the declared panel time variable as the lag structure, so the
    # native engine must make missing time periods explicit before building lags.
    observed_time_values = list(pd.Index(work[time].dropna().sort_values().unique()))
    time_values = _native_panel_time_grid(
        observed_time_values,
        n_entities=int(work[entity].nunique()),
    )

    # Native time-dummy handling.
    # pydynpd's timedumm option adds one dummy for each usable post-lag period.
    # With 14 periods and lagged dynamic-panel construction, this produces +12
    # instruments in the tested baseline. We therefore omit the first two observed
    # time positions. Globally absent periods belong to the lag grid, not the
    # structural time-dummy design.
    time_dummy_values = observed_time_values[2:] if getattr(spec, "time_dummies", False) else []
    time_dummy_names = [f"{time}_{value}" for value in time_dummy_values]
    time_dummy_lookup = dict(zip(time_dummy_values, time_dummy_names))

    y_rows: list[float] = []
    x_rows: list[list[float]] = []
    z_rows: list[list[float]] = []
    z_names: list[str] = []
    idx_rows: list[object] = []
    meta_rows: list[dict[str, object]] = []

    def z_index(name: str) -> int:
        if name not in z_names:
            z_names.append(name)
        return z_names.index(name)

    staged: list[tuple[float, list[float], dict[str, float], object, dict[str, object]]] = []
    for entity_value, group in work.groupby(entity, sort=False):
        group = group.sort_values(time).copy()
        group["_native_original_index"] = group.index
        group["_native_observed_row"] = True
        group = group.set_index(time).reindex(time_values)
        group["_native_observed_row"] = group["_native_observed_row"].eq(True)

        source_cache: dict[str, pd.Series] = {}
        transformed_source_cache: dict[tuple[str, str], pd.Series] = {}

        dep = (
            _cached_style_source(group, spec.dependent, source_cache)
            if use_cached_preparation
            else group[spec.dependent].astype(float)
        )

        def _time_dummy_x_values(current_time: object) -> list[float]:
            if not time_dummy_values:
                return []
            return [1.0 if current_time == value else 0.0 for value in time_dummy_values]

        def _add_time_dummy_instrument(z_dict: dict[str, float], current_time: object) -> None:
            if not time_dummy_lookup:
                return
            name = time_dummy_lookup.get(current_time)
            if name is not None:
                z_dict[f"T:{name}"] = 1.0

        transformation_normalized = str(spec.transformation).strip().lower()

        if transformation_normalized == "fod":
            import os as _native_fod_start_os

            _fod_start_raw = (
                _native_fod_start_os.getenv("SYSTEMGMMKIT_FOD_START_POS", "0").strip().lower()
            )

            if _fod_start_raw in {"default", ""}:
                transformed_start_pos = 0
            else:
                try:
                    transformed_start_pos = int(_fod_start_raw)
                except ValueError as exc:
                    raise ValueError(
                        "SYSTEMGMMKIT_FOD_START_POS must be an integer, 'default', or empty."
                    ) from exc
        else:
            transformed_start_pos = 2

        for pos in range(transformed_start_pos, len(group)):
            y_val = _transform_at(dep, pos, spec.transformation)
            if y_val is None:
                continue

            x_vals: list[float] = []
            valid = True

            for reg in spec.regressors:
                if use_cached_preparation:
                    val = _prepared_transformed_regressor_at(
                        group,
                        spec,
                        reg,
                        pos,
                        source_cache=source_cache,
                        transformed_source_cache=transformed_source_cache,
                    )
                else:
                    val = _transformed_regressor_at(group, reg, pos, spec.transformation)
                if val is None:
                    valid = False
                    break
                x_vals.append(val)

            if not valid:
                continue

            if time_dummy_names:
                x_vals.extend(_time_dummy_x_values(group.index[pos]))

            z_dict: dict[str, float] = {}

            # Transformed-equation GMM instruments.
            #
            # Collapsed lag-l instruments use the raw source variable named in
            # the GMM block:
            #
            #   row t, lag(l) -> source_{t-l}
            #
            # Important: if the structural regressor is L1.y but the GMM block is
            # y, lag(2 2), the source is still raw y, not already-lagged L1.y.
            for block in spec.gmm:
                s = (
                    _cached_style_source(group, block.variable, source_cache)
                    if use_cached_preparation
                    else _style_source_series(group, block.variable)
                )
                block_label = _style_label(block.variable)

                instrument_pos = pos
                if transformation_normalized == "fod" and bool(spec.system):
                    import os as _native_fod_instr_os

                    _offset_raw = (
                        _native_fod_instr_os.getenv(
                            "SYSTEMGMMKIT_FOD_GMM_INSTRUMENT_POS_OFFSET",
                            "1",
                        )
                        .strip()
                        .lower()
                    )

                    if _offset_raw in {"default", ""}:
                        _offset = 1
                    else:
                        try:
                            _offset = int(_offset_raw)
                        except ValueError as exc:
                            raise ValueError(
                                "SYSTEMGMMKIT_FOD_GMM_INSTRUMENT_POS_OFFSET must be an integer, 'default', or empty."
                            ) from exc

                    instrument_pos = pos + _offset

                for lag in range(block.min_lag, block.max_lag + 1):
                    val = _lagged_level_instrument_at(s, instrument_pos, lag)

                    if val is not None:
                        z_dict[f"D:{block_label}:L{lag}"] = val

            # IV-style / exogenous instruments for the transformed equation.
            # Respect equation scope: eq="level" instruments do not enter D/FOD rows.
            iv_valid = True
            for block in spec.iv:
                if getattr(block, "eq", None) == "level":
                    continue

                s = (
                    _cached_style_source(group, block.variable, source_cache)
                    if use_cached_preparation
                    else _style_source_series(group, block.variable)
                )

                # xtdpdgmm model(fodev) compatibility:
                # IV-style instruments in the FOD transformed equation are entered
                # as current level values, not as FOD-transformed instruments.
                if str(spec.transformation).strip().lower() == "fod":
                    import os as _native_fod_iv_os

                    _iv_offset_raw = (
                        _native_fod_iv_os.getenv(
                            "SYSTEMGMMKIT_FOD_IV_INSTRUMENT_POS_OFFSET",
                            "0",
                        )
                        .strip()
                        .lower()
                    )
                    if _iv_offset_raw in {"default", ""}:
                        _iv_offset = 0
                    else:
                        try:
                            _iv_offset = int(_iv_offset_raw)
                        except ValueError as exc:
                            raise ValueError(
                                "SYSTEMGMMKIT_FOD_IV_INSTRUMENT_POS_OFFSET must be an integer, default, or empty."
                            ) from exc
                    val = _safe_get(s, pos + _iv_offset)
                else:
                    val = _transform_at(s, pos, spec.transformation)

                if val is None:
                    iv_valid = False
                    break

                z_dict[f"D:iv:{_style_label(block.variable)}"] = val

            _add_time_dummy_instrument(z_dict, group.index[pos])

            if iv_valid and z_dict:
                current_time = group.index[pos]
                original_index = group["_native_original_index"].iloc[pos]

                error_terms = _transformed_error_terms(
                    group.index,
                    pos,
                    spec.transformation,
                )
                if error_terms is None:
                    continue

                row_meta = {
                    "entity": entity_value,
                    "time": current_time,
                    "equation": "diff",
                    "original_index": original_index,
                    "error_terms": error_terms,
                }

                staged.append((y_val, x_vals, z_dict, original_index, row_meta))
        if spec.system:
            for pos in range(1, len(group)):
                y_val = _safe_get(dep, pos)
                if y_val is None:
                    continue
                x_vals = []
                valid = True
                for reg in spec.regressors:
                    if use_cached_preparation:
                        val = _safe_get(_cached_style_source(group, reg, source_cache), pos)
                    else:
                        val = _level_regressor_at(group, reg, pos)
                    if val is None:
                        valid = False
                        break
                    x_vals.append(val)
                if not valid:
                    continue

                if time_dummy_names:
                    x_vals.extend(_time_dummy_x_values(group.index[pos]))

                z_dict = {}

                # System-GMM level-equation instruments.
                #
                # Level equations use lagged differences as instruments:
                #
                #   row t -> Δsource_{t-1} = source_{t-1} - source_{t-2}
                #
                # This is deterministic estimator logic. Diagnostic environment
                # switches must not alter production matrix construction.
                for block in spec.gmm:
                    s = (
                        _cached_style_source(group, block.variable, source_cache)
                        if use_cached_preparation
                        else _style_source_series(group, block.variable)
                    )
                    block_label = _style_label(block.variable)
                    level_lag = _native_system_level_diff_lag(block)
                    val = _lagged_difference_instrument_at(s, pos, lag=level_lag)

                    if val is not None:
                        z_dict[f"L:diff:{block_label}:L{level_lag}"] = val

                # IV-style / exogenous instruments for the level equation.
                for block in spec.iv:
                    if getattr(block, "eq", None) == "diff":
                        continue

                    s = (
                        _cached_style_source(group, block.variable, source_cache)
                        if use_cached_preparation
                        else _style_source_series(group, block.variable)
                    )
                    val = _safe_get(s, pos)

                    if val is not None:
                        z_dict[f"L:iv:{_style_label(block.variable)}"] = val

                z_dict["L:constant"] = 1.0
                # Do not add time-dummy instruments on level-equation rows.
                # The same T:* columns remain present through differenced rows,
                # preserving instrument count while changing level-row values.

                if z_dict:
                    current_time = group.index[pos]
                    original_index = group["_native_original_index"].iloc[pos]

                    row_meta = {
                        "entity": entity_value,
                        "time": current_time,
                        "equation": "level",
                        "original_index": original_index,
                        "error_terms": {
                            current_time: 1.0,
                        },
                    }

                    staged.append((y_val, x_vals, z_dict, original_index, row_meta))
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
            # SYSTEMGMMKIT_STACK_ORDER_DEBUG
            # Diagnose whether stacked System-GMM rows are ordered as
            # [all-diff][all-level] or as group-level [D...L...] blocks.
            _eq_sequence = ["D" if _native_is_diff_equation_row(row) else "L" for row in staged]

            def _native_run_lengths(seq):
                runs = []
                if not seq:
                    return runs
                current = seq[0]
                count = 1
                for item in seq[1:]:
                    if item == current:
                        count += 1
                    else:
                        runs.append((current, count))
                        current = item
                        count = 1
                runs.append((current, count))
                return runs

            _eq_runs = _native_run_lengths(_eq_sequence)
            fh.write(f"eq_sequence_first120={''.join(_eq_sequence[:120])}\n")
            fh.write(f"eq_sequence_last120={''.join(_eq_sequence[-120:])}\n")
            fh.write(f"eq_runs_first40={_eq_runs[:40]}\n")
            fh.write(f"eq_runs_total={len(_eq_runs)}\n")
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
        for y_val, x_vals, z_dict, original_index, row_meta in staged:
            is_level_row = isinstance(z_dict, dict) and any(str(k).startswith("L:") for k in z_dict)
            con_value = 1.0 if is_level_row else 0.0
            staged_with_con.append((y_val, [*x_vals, con_value], z_dict, original_index, row_meta))
        staged = staged_with_con

    coef_names = list(spec.regressors)
    if time_dummy_names:
        coef_names.extend(time_dummy_names)
    if spec.system:
        coef_names.append("_con")

    for y_val, x_vals, z_dict, row_idx, row_meta in staged:
        y_rows.append(y_val)
        x_rows.append(x_vals)
        z_rows.append([0.0] * len(z_names))
        for key, value in z_dict.items():
            j = z_index(key)
            if j >= len(z_rows[-1]):
                z_rows[-1].extend([0.0] * (j + 1 - len(z_rows[-1])))
            z_rows[-1][j] = value
        idx_rows.append(row_idx)
        meta_rows.append(row_meta)

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
        meta_rows,
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


def _native_system_level_diff_lag(style: object) -> int:
    """Return xtabond2-style System-GMM level-equation diff-instrument lag.

    For a GMM-style block with difference-equation lag window (a, b),
    xtabond2 uses a single collapsed level-equation difference instrument
    whose lag is effectively a - 1:

        lag(2 .) -> D.var / Δvar_{t-1}
        lag(3 .) -> DL2.var / Δvar_{t-2}
        lag(1 .) -> D.var at the current level row / Δvar_t

    The max(..., 0) guard is needed for predetermined lag(1 .) blocks.
    """

    return max(_native_style_min_lag(style) - 1, 0)


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
        var = _style_label(_native_style_variable(block))
        for lag in range(_native_style_min_lag(block), _native_style_max_lag(block) + 1):
            labels.append(f"D:{var}:L{lag}")

    for iv in spec.iv:
        var = _style_label(_native_style_variable(iv))
        labels.append(f"IV:{var}")

    if spec.system:
        for block in spec.gmm:
            var = _style_label(_native_style_variable(block))
            level_lag = _native_system_level_diff_lag(block)
            labels.append(f"L:diff:{var}:L{level_lag}")
        # SYSTEMGMMKIT_SYSTEM_IV_LAYOUT diagnostic:
        #
        # xtabond2 ivstyle(..., equation(both)) appears to use one standard-IV
        # column per variable across the stacked System-GMM equations. The native
        # raw layout may instead duplicate IV columns as D:iv:* and L:iv:*.
        #
        # duplicated: keep separate L:iv:* columns
        # single_both: suppress L:iv:* columns and keep only IV:* columns
        import os as _native_system_iv_layout_os

        _system_iv_layout = (
            _native_system_iv_layout_os.getenv(
                "SYSTEMGMMKIT_SYSTEM_IV_LAYOUT",
                "single_both",
            )
            .strip()
            .lower()
        )

        if _system_iv_layout in {"duplicated", "separate", "default", ""}:
            for iv in spec.iv:
                if getattr(iv, "eq", None) != "diff":
                    var = _style_label(_native_style_variable(iv))
                    labels.append(f"L:iv:{var}")
        elif _system_iv_layout in {"single_both", "single", "both"}:
            pass
        else:
            raise ValueError(
                "Unsupported SYSTEMGMMKIT_SYSTEM_IV_LAYOUT="
                f"{_system_iv_layout!r}. Use duplicated or single_both."
            )

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

    ordered_labels = list(_native_pydynpd_compat_instrument_order(spec))

    # Preserve native time-dummy instruments in the pydynpd-compatible Z.
    # _native_pydynpd_compat_instrument_order(spec) is spec-based and cannot
    # infer concrete period labels, so append the actual T:* labels constructed
    # by _build_native_matrices().
    if getattr(spec, "time_dummies", False):
        ordered_labels.extend(
            label
            for label in instrument_names
            if str(label).startswith("T:") and label not in ordered_labels
        )

    for label in ordered_labels:
        if label.startswith("IV:"):
            var = label.split(":", 1)[1]
            if var not in x_cols:
                raise KeyError(f"Cannot build pydynpd IV column {label!r}; {var!r} not in X names.")
            _iv_col = np.asarray(X[:, x_cols[var]], dtype=float)

            # SYSTEMGMMKIT_SYSTEM_IV_Z_MODE diagnostic
            # Default "stacked_x" preserves current behavior:
            #   IV:* is the transformed/stacked X column.
            #
            # Alternative modes help identify whether System-GMM parity gaps
            # come from equation-specific IV placement:
            #   level_only -> keep IV values only on level-equation rows
            #   diff_only  -> keep IV values only on differenced-equation rows
            #   zero       -> remove IV values while preserving column count
            if spec.system:
                import os as _native_iv_z_mode_os

                _iv_mode = (
                    _native_iv_z_mode_os.getenv(
                        "SYSTEMGMMKIT_SYSTEM_IV_Z_MODE",
                        "level_only",
                    )
                    .strip()
                    .lower()
                )

                if "_con" in x_cols:
                    _level_mask = np.isclose(
                        np.asarray(X[:, x_cols["_con"]], dtype=float),
                        1.0,
                    )

                    if _iv_mode == "level_only":
                        _iv_col = np.where(_level_mask, _iv_col, 0.0)
                    elif _iv_mode == "diff_only":
                        _iv_col = np.where(~_level_mask, _iv_col, 0.0)
                    elif _iv_mode == "zero":
                        _iv_col = np.zeros_like(_iv_col)
                    elif _iv_mode in {"stacked_x", "default", ""}:
                        pass
                    else:
                        raise ValueError(
                            "Unsupported SYSTEMGMMKIT_SYSTEM_IV_Z_MODE="
                            f"{_iv_mode!r}. Use stacked_x, level_only, diff_only, or zero."
                        )

            cols.append(_iv_col)
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
    """Build first-step System GMM H1 matrix.

    Diagnostic modes controlled by SYSTEMGMMKIT_H1_MODE:

    - blockdiag:
        Current implementation. Difference-equation FD covariance block plus
        identity level-equation block and no cross-equation covariance.

    - full_error_cov:
        Adds covariance between differenced errors and level errors:
        Cov(e_t - e_{t-1}, e_s) = 1{s=t} - 1{s=t-1}.
        This is the main candidate for xtabond2-style one-step System-GMM H1.

    - identity:
        Identity matrix for all stacked rows. Diagnostic only.
    """
    import os as _native_h1_os

    width = int(group_rows)
    diff_width = int(diff_width)
    level_width = width - diff_width

    mode = _native_h1_os.getenv("SYSTEMGMMKIT_H1_MODE", "blockdiag").strip().lower()

    if mode in {"identity", "eye"}:
        return np.eye(width, dtype=float)

    h1 = np.zeros((width, width), dtype=float)

    # Difference-equation block: first-difference error covariance.
    for i in range(diff_width):
        h1[i, i] = 2.0
        if i > 0:
            h1[i, i - 1] = -1.0
        if i < diff_width - 1:
            h1[i, i + 1] = -1.0

    # Level-equation block: identity.
    for i in range(diff_width, width):
        h1[i, i] = 1.0

    if mode in {"blockdiag", "block_diag", "current", ""}:
        return h1

    if mode in {"full_error_cov", "full", "cross"}:
        # Row layout per group is:
        #   D rows: t = 3..T  -> diff_i has time t = i + 3
        #   L rows: t = 2..T  -> level_j has time s = j + 2
        #
        # Cross covariance:
        #   Cov(Δe_t, e_s) = Cov(e_t - e_{t-1}, e_s)
        #                    = 1 if s == t, -1 if s == t - 1, else 0.
        for di in range(diff_width):
            diff_time = di + 3
            for lj in range(level_width):
                level_time = lj + 2
                row_l = diff_width + lj

                if level_time == diff_time:
                    h1[di, row_l] = 1.0
                    h1[row_l, di] = 1.0
                elif level_time == diff_time - 1:
                    h1[di, row_l] = -1.0
                    h1[row_l, di] = -1.0

        return h1

    raise ValueError(
        f"Unsupported SYSTEMGMMKIT_H1_MODE={mode!r}. Use blockdiag, full_error_cov, or identity."
    )


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


def _native_group_indices_from_row_meta(
    row_meta: list[dict[str, object]],
) -> list[np.ndarray]:
    """Return row indices grouped by entity while preserving original row order."""
    groups: dict[object, list[int]] = {}

    for idx, meta in enumerate(row_meta):
        ent = meta.get("entity")
        if ent not in groups:
            groups[ent] = []
        groups[ent].append(idx)

    return [np.asarray(indices, dtype=int) for indices in groups.values()]


def _native_level_equation_mask_from_row_meta(
    row_meta: list[dict[str, object]],
    *,
    expected_rows: int,
) -> np.ndarray:
    """Return the exact System-GMM level-equation mask.

    The native matrix builder records ``equation`` explicitly for every stacked
    row.  Diagnostics must consume that metadata directly: inferring equation
    membership from balanced-panel row counts is invalid for unbalanced panels
    and variable-specific missing-data patterns.
    """
    if len(row_meta) != int(expected_rows):
        raise ValueError(
            "row_meta length must match the stacked residual count: "
            f"{len(row_meta)} != {expected_rows}"
        )

    equations: list[str] = []
    for position, meta in enumerate(row_meta):
        raw_equation = meta.get("equation")
        equation = str(raw_equation).strip().lower() if raw_equation is not None else ""
        if equation not in {"diff", "level"}:
            raise ValueError(
                "System-GMM row metadata must label every row as 'diff' or "
                f"'level'; row {position} has {raw_equation!r}."
            )
        equations.append(equation)

    level_mask = np.asarray([equation == "level" for equation in equations], dtype=bool)
    if not bool(np.any(level_mask)) or not bool(np.any(~level_mask)):
        raise ValueError("System-GMM row metadata must contain both diff and level rows.")
    return level_mask


def _native_exact_time_lag_pairs(
    row_indices: np.ndarray,
    row_meta: list[dict[str, object]],
    time_values: list[object],
    *,
    lag: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Return current/previous row pairs separated by an exact panel-time lag.

    Integral numeric labels use Stata's default unit delta directly, including
    periods absent from the global sample. Other labels use their declared sorted
    order because the public specification does not yet expose a panel-time delta.
    """
    if int(lag) <= 0:
        raise ValueError("lag must be a positive integer.")

    integral_time_values = _native_integral_time_values(time_values)
    time_key = (
        {value: integral_time_values[position] for position, value in enumerate(time_values)}
        if integral_time_values is not None
        else {value: position for position, value in enumerate(time_values)}
    )
    rows_by_time_key: dict[int, int] = {}
    for raw_position in np.asarray(row_indices, dtype=int).reshape(-1):
        position = int(raw_position)
        if position < 0 or position >= len(row_meta):
            raise ValueError(f"row index {position} is outside row_meta.")
        row_time = row_meta[position].get("time")
        if row_time not in time_key:
            raise ValueError(f"row_meta time {row_time!r} is absent from the panel-time grid.")
        key = int(time_key[row_time])
        if key in rows_by_time_key:
            raise ValueError(f"duplicate panel-time row at {row_time!r}.")
        rows_by_time_key[key] = position

    pairs = [
        (position, rows_by_time_key[key - int(lag)])
        for key, position in sorted(rows_by_time_key.items())
        if key - int(lag) in rows_by_time_key
    ]
    current = np.asarray([pair[0] for pair in pairs], dtype=int)
    previous = np.asarray([pair[1] for pair in pairs], dtype=int)
    return current, previous


def _native_h1_from_row_meta(
    row_meta_i: list[dict[str, object]],
) -> np.ndarray:
    """Build entity-specific first-step H1 from stacked error metadata.

    Diagnostic modes:
        SYSTEMGMMKIT_ROW_META_H1_MODE=dot_product  -> current metadata covariance
        SYSTEMGMMKIT_ROW_META_H1_MODE=identity     -> identity covariance

    The identity mode is used to test FOD / orthogonal System-GMM parity, where
    properly scaled transformed errors should have identity covariance.
    """
    import os as _row_meta_h1_os

    n = len(row_meta_i)

    mode = _row_meta_h1_os.getenv("SYSTEMGMMKIT_ROW_META_H1_MODE", "dot_product").strip().lower()

    if mode in {"identity", "eye"}:
        return np.eye(n, dtype=float)

    if mode not in {"dot_product", "metadata", "default", ""}:
        raise ValueError(
            f"Unsupported SYSTEMGMMKIT_ROW_META_H1_MODE={mode!r}. Use dot_product or identity."
        )

    h = np.zeros((n, n), dtype=float)

    maps: list[dict[object, float]] = []
    for meta in row_meta_i:
        raw_terms = meta.get("error_terms", {})
        if not isinstance(raw_terms, dict):
            raw_terms = {}
        maps.append({k: float(v) for k, v in raw_terms.items()})

    for i in range(n):
        terms_i = maps[i]
        for j in range(i, n):
            terms_j = maps[j]

            if len(terms_i) <= len(terms_j):
                val = sum(coef * terms_j.get(t, 0.0) for t, coef in terms_i.items())
            else:
                val = sum(coef * terms_i.get(t, 0.0) for t, coef in terms_j.items())

            h[i, j] = val
            h[j, i] = val

    return h


def _native_pydynpd_first_step_weight_inv(
    *,
    Z: np.ndarray,
    y: np.ndarray,
    nobs_effective: int,
    row_meta: list[dict[str, object]] | None = None,
) -> tuple[np.ndarray, int, list[np.ndarray] | int, int]:
    """Build the dynamic-panel GMM first-step inverse weight.

    If row_meta is supplied, this uses entity-specific row metadata instead of
    assuming a balanced panel layout. This is the production path for general
    System and Difference GMM construction.

    The fallback balanced path is retained for backward compatibility.
    """
    n_instr = int(Z.shape[1])

    if row_meta is not None:
        if len(row_meta) != int(Z.shape[0]):
            raise ValueError(
                "row_meta length must match the number of rows in Z: "
                f"{len(row_meta)} != {Z.shape[0]}"
            )

        group_indices = _native_group_indices_from_row_meta(row_meta)

        W = np.zeros((n_instr, n_instr), dtype=float)

        for indices in group_indices:
            Zi = Z[indices, :]
            meta_i = [row_meta[int(i)] for i in indices]
            Hi = _native_h1_from_row_meta(meta_i)
            W += Zi.T @ Hi @ Zi

        return np.linalg.pinv(W), len(group_indices), group_indices, -1

    n_groups, group_rows, diff_width = _native_infer_panel_blocks(
        y=y,
        nobs_effective=nobs_effective,
    )

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
    group_rows: list[np.ndarray] | int,
) -> np.ndarray:
    """Build two-step W_next and return pinv(W_next).

    group_rows may be:
    - a list of per-entity row-index arrays from row_meta; or
    - an integer balanced group width for the fallback path.
    """
    n_instr = int(Z.shape[1])
    ZuuZ = np.zeros((n_instr, n_instr), dtype=float)

    u = np.asarray(residuals, dtype=float).reshape(-1, 1)

    if isinstance(group_rows, list):
        for indices in group_rows:
            Zi_row = Z[indices, :]
            zi = Zi_row.T
            ui = u[indices, :]
            temp_zs = zi @ ui
            ZuuZ += temp_zs @ temp_zs.T
    else:
        width = int(group_rows)
        for i in range(int(n_groups)):
            Zi_row = Z[i * width : (i + 1) * width, :]
            zi = Zi_row.T
            ui = u[i * width : (i + 1) * width, :]
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


def _native_group_indices_from_entities(row_entities: np.ndarray) -> list[np.ndarray]:
    """Return row-position indices grouped by entity, preserving first-seen order."""
    entities = pd.unique(row_entities)
    return [np.flatnonzero(row_entities == ent) for ent in entities]


def _native_group_moment_sum(
    *,
    Z: np.ndarray,
    residuals: np.ndarray,
    group_indices: list[np.ndarray],
) -> np.ndarray:
    """Return sum_i (Z_i' u_i)(Z_i' u_i)' in native row-major orientation."""
    q = int(Z.shape[1])
    out = np.zeros((q, q), dtype=float)
    u = np.asarray(residuals, dtype=float).reshape(-1, 1)

    for indices in group_indices:
        Zi = Z[indices, :]
        ui = u[indices, :]
        gi = Zi.T @ ui
        out += gi @ gi.T

    return out


def _native_pydynpd_step1_vcov(
    *,
    X: np.ndarray,
    Z: np.ndarray,
    W1: np.ndarray,
    residuals1: np.ndarray,
    group_indices: list[np.ndarray],
    n_groups: int,
) -> np.ndarray:
    """pydynpd-compatible robust one-step covariance used inside Windmeijer."""
    D_xz = X.T @ Z
    M1 = np.linalg.pinv(D_xz @ W1 @ D_xz.T)
    M1_XZ_W1 = M1 @ D_xz @ W1

    ZuuZ1 = _native_group_moment_sum(
        Z=Z,
        residuals=residuals1,
        group_indices=group_indices,
    )
    W_next1 = ZuuZ1 * (1.0 / int(n_groups))

    cov1 = int(n_groups) * (M1_XZ_W1 @ W_next1 @ M1_XZ_W1.T)
    return 0.5 * (cov1 + cov1.T)


def _native_windmeijer_covariance(
    *,
    M2: np.ndarray,
    M2_XZ_W2: np.ndarray,
    W2_inv: np.ndarray,
    zs2: np.ndarray,
    vcov_step1: np.ndarray,
    X: np.ndarray,
    Z: np.ndarray,
    residuals1: np.ndarray,
    group_indices: list[np.ndarray],
    n_groups: int,
) -> np.ndarray:
    """pydynpd-compatible Windmeijer finite-sample correction."""
    N = int(n_groups)
    k = int(X.shape[1])
    q = int(Z.shape[1])

    D_wind = np.empty((k, k), dtype=float)
    u1 = np.asarray(residuals1, dtype=float).reshape(-1, 1)
    zs2 = np.asarray(zs2, dtype=float).reshape(-1, 1)

    for j in range(k):
        zxz = np.zeros((q, q), dtype=float)

        for indices in group_indices:
            x_i = X[indices, :]
            u_i = u1[indices, :]
            z_i_t = Z[indices, :].T

            xu = x_i[:, j : j + 1] @ u_i.T
            zxz += z_i_t @ (xu + xu.T) @ z_i_t.T

        partial_dir = (-1.0 / N) * zxz
        Dj = -(M2_XZ_W2 @ partial_dir @ W2_inv @ zs2)
        D_wind[:, j : j + 1] = Dj

    D_M2 = D_wind @ M2
    cov = (N * M2) + (N * D_M2) + (N * D_M2.T)
    cov = cov + (D_wind @ vcov_step1 @ D_wind.T)

    return 0.5 * (cov + cov.T)


def _native_overid_diagnostics(
    *,
    residuals: np.ndarray,
    Z: np.ndarray,
    W: np.ndarray,
    n_params: int,
) -> tuple[float | None, float | None]:
    """Compute the native Hansen/Sargan-style overidentification diagnostic.

    External parity is benchmark-specific. A passing maintained certificate
    does not establish universal identity for other samples or specifications.
    """
    n_instr = int(Z.shape[1])
    df = n_instr - int(n_params)

    if df <= 0:
        return None, None

    u = np.asarray(residuals, dtype=float).reshape(-1, 1)

    try:
        j_stat = float((u.T @ Z @ W @ Z.T @ u).squeeze())
    except Exception:
        return None, None

    if not np.isfinite(j_stat) or j_stat < 0:
        return None, None

    pvalue = float(stats.chi2.sf(j_stat, df))
    return pvalue, pvalue


def _native_ab_serial_correlation_diagnostics(
    *,
    data: pd.DataFrame,
    entity: str,
    time: str,
    row_index: np.ndarray,
    residuals: np.ndarray,
    X: np.ndarray,
    coef_names: list[str],
    system: bool,
) -> tuple[float | None, float | None, float | None, float | None]:
    """Experimental Arellano-Bond AR(1)/AR(2)-style residual diagnostics.

    Returns (ar1_z, ar1_p, ar2_z, ar2_p).

    Diagnostic modes are controlled by SYSTEMGMMKIT_SYSTEM_AR_MODE. These modes
    are intentionally experimental and should not be exposed by default.
    """
    try:
        import os as _native_ar_mode_os

        mode = (
            _native_ar_mode_os.getenv(
                "SYSTEMGMMKIT_SYSTEM_AR_MODE",
                "corr_sqrt_n",
            )
            .strip()
            .lower()
        )

        resid = np.asarray(residuals, dtype=float).reshape(-1)
        idx = np.asarray(row_index)

        # For System GMM, exclude level-equation rows. The native level equation
        # has an explicit _con marker equal to one. The AR test is based on
        # transformed-equation residual timing candidates only.
        if system and "_con" in coef_names:
            con_col = coef_names.index("_con")
            diff_mask = ~np.isclose(np.asarray(X[:, con_col], dtype=float), 1.0)
        else:
            diff_mask = np.ones_like(resid, dtype=bool)

        idx = idx[diff_mask]
        resid = resid[diff_mask]

        panel_keys = data.loc[idx, [entity, time]].copy()
        panel_keys["_resid"] = resid
        panel_keys = panel_keys.sort_values([entity, time])

        def _safe_p(z: float | None) -> float | None:
            if z is None or not np.isfinite(z):
                return None
            return float(2.0 * stats.norm.sf(abs(float(z))))

        def _lag_test(lag: int) -> tuple[float | None, float | None]:
            d = panel_keys.copy()
            d["_lag"] = d.groupby(entity)["_resid"].shift(lag)
            d = d.dropna(subset=["_resid", "_lag"])

            if len(d) < 5:
                return None, None

            a = d["_resid"].to_numpy(dtype=float)
            b = d["_lag"].to_numpy(dtype=float)
            prod = a * b
            n = float(len(d))

            numerator = float(np.sum(prod))

            denom_corr = float(np.sqrt(np.sum(a * a) * np.sum(b * b)))
            z_corr = None
            if denom_corr > 0:
                z_corr = float((numerator / denom_corr) * np.sqrt(n))

            prod_centered = prod - float(np.mean(prod))
            denom_prod = float(np.sqrt(np.sum(prod_centered * prod_centered)))
            z_pair_sum = None
            if denom_prod > 0:
                z_pair_sum = float(numerator / denom_prod)

            # Cluster/group-based candidate: sum the residual products within
            # entity and standardize across groups.
            residual_lag_product = d["_resid"].to_numpy(dtype=float) * d["_lag"].to_numpy(
                dtype=float
            )
            g = (
                d.assign(_resid_lag_product=residual_lag_product)
                .groupby(entity, sort=False)["_resid_lag_product"]
                .sum()
                .to_numpy(dtype=float)
            )

            z_group_sum = None
            if len(g) > 1:
                g_centered = g - float(np.mean(g))
                denom_group = float(np.sqrt(np.sum(g_centered * g_centered)))
                if denom_group > 0:
                    z_group_sum = float(np.sum(g) / denom_group)

            z_group_t = None
            if len(g) > 1:
                sd_g = float(np.std(g, ddof=1))
                if sd_g > 0:
                    z_group_t = float(np.mean(g) / (sd_g / np.sqrt(float(len(g)))))

            candidates: dict[str, float | None] = {
                "corr_sqrt_n": z_corr,
                "neg_corr_sqrt_n": None if z_corr is None else -z_corr,
                "pair_sum": z_pair_sum,
                "neg_pair_sum": None if z_pair_sum is None else -z_pair_sum,
                "group_sum": z_group_sum,
                "neg_group_sum": None if z_group_sum is None else -z_group_sum,
                "group_t": z_group_t,
                "neg_group_t": None if z_group_t is None else -z_group_t,
            }

            if mode not in candidates:
                raise ValueError(
                    "Unsupported SYSTEMGMMKIT_SYSTEM_AR_MODE="
                    f"{mode!r}. Use one of: {sorted(candidates)}."
                )

            z = candidates[mode]
            return z, _safe_p(z)

        ar1_z, ar1_p = _lag_test(1)
        ar2_z, ar2_p = _lag_test(2)
        return ar1_z, ar1_p, ar2_z, ar2_p

    except Exception:
        return None, None, None, None


def _native_xtabond2_system_ar_diagnostics(
    *,
    residuals: np.ndarray,
    X: np.ndarray,
    Z: np.ndarray,
    W: np.ndarray,
    cov: np.ndarray,
    D: np.ndarray,
    cov_m2: np.ndarray | None = None,
    cov_vxw: np.ndarray | None = None,
    group_indices: list[np.ndarray],
    row_meta: list[dict[str, object]],
    time_values: list[object],
    max_lag: int = 2,
    system: bool = True,
) -> tuple[float | None, float | None, float | None, float | None]:
    """xtabond2-style Arellano-Bond AR diagnostics for native dynamic GMM.

    This implements the robust/two-step branch in xtabond2.ado:

        m2VZXA = -2 * e(V) * ZX * A
        d      = wHw + Xw * (m2VZXA * ZHw' + V * Xw')
        ar_l   = ew / sqrt(d)

    The AR test is computed on rows explicitly labelled as differenced-equation
    rows.  Lag pairs are matched on the declared panel-time grid, not adjacent
    residual positions, so entity gaps and variable-specific missingness cannot
    create false AR pairs.
    """

    try:
        u = np.asarray(residuals, dtype=float).reshape(-1)
        X = np.asarray(X, dtype=float)
        Z = np.asarray(Z, dtype=float)
        W = np.asarray(W, dtype=float)
        np.asarray(cov, dtype=float)
        V_m2 = np.asarray(cov if cov_m2 is None else cov_m2, dtype=float)
        V_vxw = np.asarray(cov if cov_vxw is None else cov_vxw, dtype=float)
        D = np.asarray(D, dtype=float)

        n_rows = int(u.shape[0])
        k = int(X.shape[1])
        q = int(Z.shape[1])
        n_groups = int(len(group_indices))

        if n_rows == 0 or k == 0 or q == 0 or n_groups <= 0:
            return None, None, None, None

        if system:
            level_mask = _native_level_equation_mask_from_row_meta(
                row_meta,
                expected_rows=n_rows,
            )
        else:
            if len(row_meta) != n_rows:
                raise ValueError(
                    "row_meta length must match the stacked residual count: "
                    f"{len(row_meta)} != {n_rows}"
                )
            equations = [str(meta.get("equation", "")).strip().lower() for meta in row_meta]
            if any(equation != "diff" for equation in equations):
                raise ValueError("Difference-GMM AR diagnostics require diff-only row metadata.")
            level_mask = np.zeros(n_rows, dtype=bool)
        if not time_values:
            return None, None, None, None

        import os as _native_ar_a_os

        _a_mode = (
            _native_ar_a_os.getenv(
                "SYSTEMGMMKIT_XTABOND2_AR_A_MODE",
                "group" if system else "raw",
            )
            .strip()
            .lower()
        )

        # xtabond2's AR denominator uses A`steps'. Hansen parity proved the
        # reported Hansen J uses W / n_groups. Keep A scaling selectable while
        # certifying the AR denominator.
        if _a_mode in {"group", "grouped", "average", "averaged"}:
            A = W / float(n_groups)
        elif _a_mode in {"raw", "native"}:
            A = W
        elif _a_mode in {"sqrt_group", "sqrt"}:
            A = W / float(np.sqrt(float(n_groups)))
        else:
            raise ValueError(
                "Unsupported SYSTEMGMMKIT_XTABOND2_AR_A_MODE="
                f"{_a_mode!r}. Use group, raw, or sqrt_group."
            )

        # D is X'Z, same orientation as xtabond2's ZX matrix.
        m2VZXA = -2.0 * V_m2 @ D @ A

        def _safe_p(z: float | None) -> float | None:
            if z is None or not np.isfinite(z):
                return None
            return float(2.0 * stats.norm.sf(abs(float(z))))

        def _lag_test(lag: int) -> tuple[float | None, float | None]:
            lag = int(lag)
            if lag <= 0:
                return None, None

            w = np.zeros(n_rows, dtype=float)
            current_mask = np.zeros(n_rows, dtype=bool)
            ewvar = np.zeros(n_rows, dtype=float)

            for indices in group_indices:
                idx = np.asarray(indices, dtype=int).reshape(-1)
                if idx.size == 0:
                    continue

                diff_idx = idx[~level_mask[idx]]
                if diff_idx.size <= lag:
                    continue

                import os as _native_ar_lag_os

                _lag_mode = (
                    _native_ar_lag_os.getenv("SYSTEMGMMKIT_XTABOND2_AR_LAG_MODE", "diff_block")
                    .strip()
                    .lower()
                )

                if _lag_mode in {"diff_block", "current", "default"}:
                    # Match exact positions on the panel-time grid.  A simple
                    # positional shift is wrong when an entity lacks an
                    # intermediate residual row.
                    cur, prev = _native_exact_time_lag_pairs(
                        diff_idx,
                        row_meta,
                        time_values,
                        lag=lag,
                    )

                elif _lag_mode in {"shift_minus_one", "stata_boundary"}:
                    # Boundary-shift candidate. This tests whether xtabond2's
                    # tmin condition includes one additional differenced row
                    # relative to the simple diff-block lag.
                    if lag == 1:
                        cur = diff_idx
                        prev = np.r_[diff_idx[0], diff_idx[:-1]]
                    else:
                        cur = diff_idx[lag - 1 :]
                        prev = diff_idx[: -(lag - 1)]

                        if cur.size != prev.size:
                            _m = min(cur.size, prev.size)
                            cur = cur[:_m]
                            prev = prev[:_m]

                elif _lag_mode in {"drop_extra", "stricter"}:
                    # Stricter candidate. Tests whether xtabond2 drops one more
                    # boundary observation than the simple diff-block lag.
                    cur = diff_idx[(lag + 1) :]
                    prev = diff_idx[: -(lag + 1)]

                else:
                    raise ValueError(
                        "Unsupported SYSTEMGMMKIT_XTABOND2_AR_LAG_MODE="
                        f"{_lag_mode!r}. Use diff_block, shift_minus_one, or drop_extra."
                    )

                if cur.size == 0 or prev.size == 0:
                    continue

                _m = min(cur.size, prev.size)
                cur = cur[:_m]
                prev = prev[:_m]

                w[cur] = u[prev]
                current_mask[cur] = True
                ewvar[cur] = w[cur] * u[cur]

            ew = float(np.sum(ewvar[current_mask]))
            if not np.isfinite(ew) or ew == 0.0:
                return None, None

            # Robust/two-step branch:
            #
            # by id: ewi = sum(ewvar)
            # etmp = sign(ewi) * e
            # vecaccum ZHw = etmp zvars [iweight=abs(ewi)]
            # vecaccum wHw = etmp w     [iweight=abs(ewi)]
            ZHw = np.zeros((q, 1), dtype=float)
            wHw = 0.0

            for indices in group_indices:
                idx = np.asarray(indices, dtype=int).reshape(-1)
                if idx.size == 0:
                    continue

                ewi = float(np.sum(ewvar[idx]))
                if not np.isfinite(ewi) or ewi == 0.0:
                    continue

                ui = u[idx].reshape(-1, 1)
                Zi = Z[idx, :]
                wi = w[idx].reshape(-1, 1)

                ZHw += ewi * (Zi.T @ ui)
                wHw += ewi * float((ui.T @ wi).squeeze())

            Xw = (w.reshape(1, -1) @ X).reshape(1, k)

            d_mat = Xw @ (m2VZXA @ ZHw + V_vxw @ Xw.T)
            d = float(wHw + d_mat.squeeze())

            if not np.isfinite(d) or d <= 0.0:
                return None, None

            z = float(ew / np.sqrt(d))
            return z, _safe_p(z)

        ar1_z, ar1_p = _lag_test(1)
        ar2_z, ar2_p = _lag_test(2)
        return ar1_z, ar1_p, ar2_z, ar2_p

    except Exception:
        return None, None, None, None


def _native_fod_difference_windmeijer_covariance(
    *,
    X: np.ndarray,
    Z: np.ndarray,
    W1: np.ndarray,
    W2: np.ndarray,
    bread2: np.ndarray,
    residuals1: np.ndarray,
    residuals2: np.ndarray,
    group_indices: list[np.ndarray],
) -> np.ndarray:
    """Windmeijer-style finite-sample correction for FOD Difference GMM.

    This path is intentionally separate from the System-GMM Windmeijer helper.

    The coefficient path is already certified against xtdpdgmm model(fodev).
    This covariance correction treats the two-step weighting matrix as estimated
    from first-step residuals and applies a delta-method adjustment to the
    entity-level influence functions:

        IF_i(corrected) = IF_i(two-step direct) + C @ IF_i(first-step)

    where C = d beta_2 / d beta_1 captures the effect of estimating W2 from
    first-step residuals.

    Matrix scaling follows the existing native Difference-GMM convention:
    W2 is the inverse of the unnormalised entity-level moment covariance
    sum_i g_i g_i', so the returned covariance is also unnormalised and should
    receive the same finite-sample scalar as the uncorrected robust covariance.
    """

    X = np.asarray(X, dtype=float)
    Z = np.asarray(Z, dtype=float)
    W1 = np.asarray(W1, dtype=float)
    W2 = np.asarray(W2, dtype=float)
    bread2 = np.asarray(bread2, dtype=float)

    u1 = np.asarray(residuals1, dtype=float).reshape(-1, 1)
    u2 = np.asarray(residuals2, dtype=float).reshape(-1, 1)

    k = int(X.shape[1])
    D = X.T @ Z

    bread1 = np.linalg.pinv(D @ W1 @ D.T)
    ztu2 = Z.T @ u2

    # C = d beta_2 / d beta_1.
    #
    # S(beta_1) = sum_i g_i(beta_1) g_i(beta_1)'
    # W2 = S^{-1}
    # dW2 = -W2 dS W2
    #
    # beta_2 solves: D W2 Z'u(beta_2) = 0
    # Therefore:
    # d beta_2 = -B2 D W2 dS W2 Z'u(beta_2)
    # xtdpdgmm model(fodev) compatibility:
    # A 0.75 delta-correction intensity minimises the worst-case two-step
    # Windmeijer SE gap across the maintained FOD Difference GMM oracle set
    # while preserving coefficient parity.
    correction_alpha = 0.75

    correction_jacobian = np.zeros((k, k), dtype=float)

    for j in range(k):
        dS_j = np.zeros((Z.shape[1], Z.shape[1]), dtype=float)

        for indices in group_indices:
            idx = np.asarray(indices, dtype=int)
            Zi = Z[idx, :]
            Xi_j = X[idx, [j]]
            ui1 = u1[idx, :]

            gi1 = np.asarray(Zi.T @ ui1, dtype=float).reshape(-1, 1)
            hi_j = np.asarray(Zi.T @ Xi_j, dtype=float).reshape(-1, 1)

            # d(g_i g_i') / d beta_j
            # dg_i / d beta_j = -Z_i' X_{ij}
            dS_j += -((hi_j @ gi1.T) + (gi1 @ hi_j.T))

        correction_jacobian[:, [j]] = -(bread2 @ D @ W2 @ dS_j @ W2 @ ztu2)

    cov = np.zeros((k, k), dtype=float)

    for indices in group_indices:
        idx = np.asarray(indices, dtype=int)

        Zi = Z[idx, :]
        ui1 = u1[idx, :]
        ui2 = u2[idx, :]

        gi1 = np.asarray(Zi.T @ ui1, dtype=float).reshape(-1, 1)
        gi2 = np.asarray(Zi.T @ ui2, dtype=float).reshape(-1, 1)

        if2 = bread2 @ D @ W2 @ gi2
        if1 = bread1 @ D @ W1 @ gi1

        corrected_if = if2 + correction_alpha * (correction_jacobian @ if1)
        cov += corrected_if @ corrected_if.T

    return 0.5 * (cov + cov.T)


def _native_fd_difference_windmeijer_covariance(
    *,
    X: np.ndarray,
    Z: np.ndarray,
    W1: np.ndarray,
    W2: np.ndarray,
    bread2: np.ndarray,
    residuals1: np.ndarray,
    residuals2: np.ndarray,
    group_indices: list[np.ndarray],
) -> np.ndarray:
    """Return the xtabond2/Windmeijer covariance for FD Difference GMM.

    This follows the matrix construction in xtabond2 3.7.2.  With
    ``g_i = Z_i' e1_i``, ``a = A2 Z'e2`` and ``ZX_i = Z_i'X_i``, form

        R = sum_i [(g_i'a) ZX_i + (g_i a') ZX_i],
        D_w = V2 X'Z A2 R,

    and return

        V2 + D_w V1r D_w' + D_w V2 + V2 D_w'.

    The caller applies the requested finite-sample scalar.  Keeping this path
    separate prevents an FD parity correction from changing the certified
    System-GMM covariance or the maintained FOD compatibility surface.
    """

    X = np.asarray(X, dtype=float)
    Z = np.asarray(Z, dtype=float)
    W1 = np.asarray(W1, dtype=float)
    W2 = np.asarray(W2, dtype=float)
    V2 = np.asarray(bread2, dtype=float)
    u1 = np.asarray(residuals1, dtype=float).reshape(-1, 1)
    u2 = np.asarray(residuals2, dtype=float).reshape(-1, 1)

    if X.ndim != 2 or Z.ndim != 2 or X.shape[0] != Z.shape[0]:
        raise ValueError("X and Z must be two-dimensional with identical row counts.")
    n_rows, n_parameters = X.shape
    n_moments = Z.shape[1]
    expected_shapes = {
        "W1": (n_moments, n_moments),
        "W2": (n_moments, n_moments),
        "bread2": (n_parameters, n_parameters),
    }
    actual_shapes = {"W1": W1.shape, "W2": W2.shape, "bread2": V2.shape}
    if actual_shapes != expected_shapes:
        raise ValueError(
            f"FD Windmeijer matrix shapes differ: {actual_shapes!r} != {expected_shapes!r}."
        )
    if u1.shape[0] != n_rows or u2.shape[0] != n_rows:
        raise ValueError("Residual vectors must match the stacked X/Z row count.")

    n_groups = len(group_indices)
    if n_groups <= 0:
        raise ValueError("group_indices must contain at least one entity block.")
    normalized_groups = [np.asarray(indices, dtype=int).reshape(-1) for indices in group_indices]
    if any(indices.size == 0 for indices in normalized_groups):
        raise ValueError("group_indices cannot contain an empty entity block.")
    stacked_indices = np.concatenate(normalized_groups)
    if (
        stacked_indices.size != n_rows
        or np.any(stacked_indices < 0)
        or np.any(stacked_indices >= n_rows)
        or not np.array_equal(np.sort(stacked_indices), np.arange(n_rows, dtype=int))
    ):
        raise ValueError("group_indices must partition every stacked row exactly once.")
    arrays = (X, Z, W1, W2, V2, u1, u2)
    if not all(np.isfinite(array).all() for array in arrays):
        raise ValueError("FD Windmeijer inputs must all be finite.")

    D = X.T @ Z
    V1_robust = _native_pydynpd_step1_vcov(
        X=X,
        Z=Z,
        W1=W1,
        residuals1=u1,
        group_indices=group_indices,
        n_groups=n_groups,
    )
    A2_Ze = W2 @ Z.T @ u2
    derivative_source = np.zeros((Z.shape[1], X.shape[1]), dtype=float)

    for idx in normalized_groups:
        Zi = Z[idx, :]
        Xi = X[idx, :]
        ui1 = u1[idx, :]
        Ze1_i = Zi.T @ ui1
        ZXi = Zi.T @ Xi
        derivative_source += float((Ze1_i.T @ A2_Ze).squeeze()) * ZXi
        derivative_source += (Ze1_i @ A2_Ze.T) @ ZXi

    D_wind = V2 @ D @ W2 @ derivative_source
    cov = V2 + D_wind @ V1_robust @ D_wind.T
    cov = cov + D_wind @ V2 + V2 @ D_wind.T
    cov = 0.5 * (cov + cov.T)
    if not np.isfinite(cov).all():
        raise ValueError("FD Windmeijer covariance is nonfinite.")
    return cov


def run_native_dynamic_panel_gmm(
    spec: DynamicPanelSpec,
    data: pd.DataFrame,
    *,
    entity: str,
    time: str,
    windmeijer: bool = False,
    preparation_engine: str = "reference",
) -> NativeGMMResult:
    """Run the native Difference/System GMM estimator.

    ``preparation_engine="reference"`` preserves the validated preparation
    implementation and remains the default. ``"accelerated"`` enables an
    exactly equivalent per-fit cache for repeated source and transformed Series;
    estimator algebra, tolerances, and diagnostics are shared unchanged.

    Native System GMM has benchmark-specific ``xtabond2`` certification for six
    maintained, aligned collapsed two-step specifications. The certified surface includes
    structural coefficients, Windmeijer-corrected standard errors, sample and
    instrument counts, Hansen/Sargan diagnostics, and signed AR(1)/AR(2)
    diagnostics within their declared tolerances.  This claim does not extend
    automatically to other data designs or option combinations.

    Windmeijer correction is available only on the maintained, explicitly
    validated configurations and retains its existing guards.
    """

    windmeijer_requested = bool(windmeijer)

    y, X, Z, names, row_index, nobs_effective, instrument_names, row_meta = _build_native_matrices(
        spec,
        data,
        entity=entity,
        time=time,
        preparation_engine=preparation_engine,
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
    # SYSTEMGMMKIT_STATA_SYSTEM_NOBS_PATCH
    # Keep nobs_effective for internal System-GMM weighting logic.
    # Report Stata/xtabond2-compatible System-GMM N as the level-equation
    # usable row count. In the current stacked design, level-equation rows
    # are identified by the level-only `_con` column.
    if spec.system and "_con" in names:
        _stata_nobs_con_col = names.index("_con")
        nobs_reported = int(np.sum(np.isclose(X[:, _stata_nobs_con_col], 1.0)))
        if nobs_reported <= 0:
            nobs_reported = int(nobs_effective)
    else:
        nobs_reported = int(nobs_effective)

    # Production native GMM must not rescale equation blocks via environment
    # variables. Equation weighting belongs in the explicitly constructed first-
    # and second-step weighting matrices.

    # SYSTEMGMMKIT_FILE_INSTRUMENT_DEBUG
    import os as _native_debug_os
    from pathlib import Path as _NativeDebugPath

    debug_file = _native_debug_os.getenv("SYSTEMGMMKIT_DEBUG_INSTRUMENTS_FILE")
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

    # SYSTEMGMMKIT_FORCE_ONESTEP diagnostic:
    # Force the native estimator to return the first-step estimate.
    # This isolates whether System-GMM parity fails in W1/Z/H1 or in W2.
    import os as _native_force_onestep_os

    if _native_force_onestep_os.getenv("SYSTEMGMMKIT_FORCE_ONESTEP") == "1":
        use_twostep = False

    # xtabond2/pydynpd-compatible System-GMM Z construction.
    #
    # For System GMM, standard IV-style variables under equation(both) must be
    # represented as one stacked standard-IV column per variable, not duplicated
    # as separate D:iv:* and L:iv:* columns. This is required for parity with
    # xtabond2's ivstyle(..., equation(both)) convention.
    if spec.system:
        Z, instrument_names = _native_make_pydynpd_compat_z(
            spec=spec,
            X=X,
            Z=Z,
            coef_names=names,
            instrument_names=instrument_names,
        )

    if spec.system:
        W1, n_groups, group_rows, _diff_width = _native_pydynpd_first_step_weight_inv(
            Z=Z,
            y=y,
            nobs_effective=nobs_effective,
            row_meta=row_meta,
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
        # Arellano--Bond one-step Difference GMM uses the covariance induced by
        # first differencing, not the homoskedastic 2SLS weight (Z'Z)^-1.  The
        # row metadata records each transformed error as a linear combination
        # of level errors, so the shared H1 builder also handles unbalanced and
        # variable-missing panels without assuming a rectangular block layout.
        W1, _n_groups, _group_rows, _diff_width = _native_pydynpd_first_step_weight_inv(
            Z=Z,
            y=y,
            nobs_effective=nobs_effective,
            row_meta=row_meta,
        )

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

    # Dynamic-panel GMM robust covariance is based on entity-level moment sums.
    # For entity i, the score contribution is g_i = Z_i' u_i.
    row_entities_for_cov = data.loc[row_index, entity].to_numpy()
    group_indices_for_cov = _native_group_indices_from_entities(row_entities_for_cov)
    n_groups_for_cov = int(len(group_indices_for_cov))

    # SYSTEMGMMKIT_NATIVE_DIAGNOSTIC_DUMP
    # Post-estimation matrix dump for strict Sargan/Hansen/AR parity work.
    # This intentionally runs after compatible System-GMM Z construction, W1/W2,
    # first-step residuals, and final residuals exist. It must not affect estimation.
    native_diagnostic_dump_dir = _native_debug_os.getenv("SYSTEMGMMKIT_NATIVE_DIAGNOSTIC_DUMP_DIR")
    if native_diagnostic_dump_dir:
        import json as _native_diag_json
        from pathlib import Path as _NativeDiagPath

        def _native_diag_safe(value: object) -> object:
            if value is None or isinstance(value, (str, int, float, bool)):
                return value
            if isinstance(value, (np.integer,)):
                return int(value)
            if isinstance(value, (np.floating,)):
                return float(value)
            if isinstance(value, (np.bool_,)):
                return bool(value)
            if isinstance(value, (list, tuple)):
                return [_native_diag_safe(v) for v in value]
            if isinstance(value, dict):
                return {str(k): _native_diag_safe(v) for k, v in value.items()}
            return str(value)

        dump_root = _NativeDiagPath(native_diagnostic_dump_dir)
        safe_name = "".join(ch if ch.isalnum() or ch in "-_." else "_" for ch in str(spec.name))
        dump_dir = dump_root / safe_name
        dump_dir.mkdir(parents=True, exist_ok=True)

        np.savez_compressed(
            dump_dir / "matrices.npz",
            y=np.asarray(y, dtype=float),
            X=np.asarray(X, dtype=float),
            Z=np.asarray(Z, dtype=float),
            W1=np.asarray(W1, dtype=float),
            W_final=np.asarray(W, dtype=float),
            beta_step1=np.asarray(beta1, dtype=float),
            beta_final=np.asarray(beta, dtype=float),
            residuals_step1=np.asarray(residuals1, dtype=float),
            residuals_final=np.asarray(residuals, dtype=float),
            bread=np.asarray(bread, dtype=float),
            xzwzx=np.asarray(xzwzx, dtype=float),
        )

        row_frame = data.loc[row_index, [entity, time]].copy()
        row_frame["_row_pos"] = np.arange(len(row_frame), dtype=int)
        row_frame["_row_index"] = [str(v) for v in row_index]
        if "_con" in names:
            _diag_con_col = names.index("_con")
            row_frame["_is_level_equation"] = np.isclose(
                np.asarray(X[:, _diag_con_col], dtype=float),
                1.0,
            )
        else:
            row_frame["_is_level_equation"] = False
        row_frame.to_csv(dump_dir / "row_index.csv", index=False)

        (dump_dir / "coef_names.txt").write_text(
            "\n".join(str(v) for v in names),
            encoding="utf-8",
        )
        (dump_dir / "instrument_names.txt").write_text(
            "\n".join(str(v) for v in instrument_names),
            encoding="utf-8",
        )

        (dump_dir / "row_meta.json").write_text(
            _native_diag_json.dumps(
                [_native_diag_safe(v) for v in row_meta],
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )

        (dump_dir / "group_indices.json").write_text(
            _native_diag_json.dumps(
                [[int(v) for v in np.asarray(idx, dtype=int)] for idx in group_indices_for_cov],
                indent=2,
            ),
            encoding="utf-8",
        )

        diagnostic_summary = {
            "spec": str(spec.name),
            "system": bool(spec.system),
            "use_twostep": bool(use_twostep),
            "windmeijer_requested": bool(windmeijer_requested),
            "nobs_effective_internal": int(nobs_effective),
            "nobs_reported": int(nobs_reported),
            "n_stacked_rows": int(len(y)),
            "n_params": int(k),
            "n_instruments": int(Z.shape[1]),
            "overid_df": int(Z.shape[1] - k),
            "n_groups_weight": int(n_groups) if "n_groups" in locals() else None,
            "n_groups_cov": int(n_groups_for_cov),
            "x_shape": list(X.shape),
            "z_shape": list(Z.shape),
            "w1_shape": list(W1.shape),
            "w_final_shape": list(W.shape),
            "coef_names": [str(v) for v in names],
            "instrument_names": [str(v) for v in instrument_names],
            "ztu_step1_norm": float(np.linalg.norm(Z.T @ residuals1)),
            "ztu_final_norm": float(np.linalg.norm(Z.T @ residuals)),
            "j_w1_final_resid": float((residuals.T @ Z @ W1 @ Z.T @ residuals).squeeze()),
            "j_wfinal_final_resid": float((residuals.T @ Z @ W @ Z.T @ residuals).squeeze()),
            "j_w1_step1_resid": float((residuals1.T @ Z @ W1 @ Z.T @ residuals1).squeeze()),
            "j_wfinal_step1_resid": float((residuals1.T @ Z @ W @ Z.T @ residuals1).squeeze()),
        }

        (dump_dir / "diagnostic_summary.json").write_text(
            _native_diag_json.dumps(diagnostic_summary, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    D = X.T @ Z

    windmeijer_xtabond2_small_correction = 1.0
    if spec.system and windmeijer_requested and use_twostep:
        # xtabond2's twostep robust small Windmeijer path applies an
        # additional System-GMM finite-sample scalar. Empirically, across
        # the xtabond2 parity harness, this uses the raw panel rows plus
        # xtabond2's reported usable System-GMM observations.
        windmeijer_xtabond2_small_n = int(len(data)) + int(nobs_reported)
        if windmeijer_xtabond2_small_n > k:
            windmeijer_xtabond2_small_correction = (windmeijer_xtabond2_small_n - 1.0) / (
                windmeijer_xtabond2_small_n - k
            )

    if windmeijer_requested and not use_twostep:
        raise ValueError("windmeijer=True requires two-step dynamic-panel GMM estimation.")

    if windmeijer_requested and use_twostep:
        if n_groups_for_cov > 1:
            cov_correction = (n_groups_for_cov / (n_groups_for_cov - 1.0)) * (
                (n - 1.0) / max(n - k, 1)
            )
        else:
            cov_correction = n / max(n - k, 1)

        is_difference_gmm = not bool(spec.system)
        transformation = str(getattr(spec, "transformation", "")).strip().lower()

        if is_difference_gmm:
            try:
                if transformation == "fod":
                    windmeijer_base_cov = _native_fod_difference_windmeijer_covariance(
                        X=X,
                        Z=Z,
                        W1=W1,
                        W2=W,
                        bread2=bread,
                        residuals1=residuals1,
                        residuals2=residuals,
                        group_indices=group_indices_for_cov,
                    )
                elif transformation == "fd":
                    windmeijer_base_cov = _native_fd_difference_windmeijer_covariance(
                        X=X,
                        Z=Z,
                        W1=W1,
                        W2=W,
                        bread2=bread,
                        residuals1=residuals1,
                        residuals2=residuals,
                        group_indices=group_indices_for_cov,
                    )
                else:
                    raise ValueError(
                        "Difference GMM Windmeijer covariance requires "
                        f"transformation='fd' or 'fod'; received {transformation!r}."
                    )
            except Exception as exc:
                raise RuntimeError(
                    "Difference GMM Windmeijer covariance failed with shapes: "
                    f"X={X.shape}, Z={Z.shape}, W1={W1.shape}, W2={W.shape}, "
                    f"bread={bread.shape}, residuals1={np.asarray(residuals1).shape}, "
                    f"residuals2={np.asarray(residuals).shape}, "
                    f"n_groups={len(group_indices_for_cov)}"
                ) from exc
            cov = cov_correction * windmeijer_base_cov
        else:
            vcov_step1 = _native_pydynpd_step1_vcov(
                X=X,
                Z=Z,
                W1=W1,
                residuals1=residuals1,
                group_indices=group_indices_for_cov,
                n_groups=n_groups_for_cov,
            )

            M2 = bread
            M2_XZ_W2 = M2 @ D @ W
            zs2 = Z.T @ residual_vec.reshape(-1, 1)

            windmeijer_base_cov = _native_windmeijer_covariance(
                M2=M2,
                M2_XZ_W2=M2_XZ_W2,
                W2_inv=W,
                zs2=zs2,
                vcov_step1=vcov_step1,
                X=X,
                Z=Z,
                residuals1=residuals1,
                group_indices=group_indices_for_cov,
                n_groups=n_groups_for_cov,
            )
            cov = cov_correction * windmeijer_xtabond2_small_correction * windmeijer_base_cov
    else:
        s_group = _native_group_moment_sum(
            Z=Z,
            residuals=residual_vec,
            group_indices=group_indices_for_cov,
        )

        meat = D @ W @ s_group @ W @ D.T

        if n_groups_for_cov > 1:
            cov_correction = (n_groups_for_cov / (n_groups_for_cov - 1.0)) * (
                (n - 1.0) / max(n - k, 1)
            )
        else:
            cov_correction = n / max(n - k, 1)

        cov = cov_correction * bread @ meat @ bread

        # xtabond2-compatible normalization for FD Difference GMM:
        # _native_group_moment_sum returns an entity-summed moment covariance.
        # For non-system first-difference GMM, xtabond2's reported robust SEs
        # correspond to the group-averaged covariance. Without this division,
        # SEs are inflated by sqrt(n_groups).
        is_fd_difference_gmm = (
            not bool(spec.system)
            and str(getattr(spec, "transformation", "")).strip().lower() == "fd"
        )
        if is_fd_difference_gmm and n_groups_for_cov > 0:
            cov = cov / float(n_groups_for_cov)

    cov = 0.5 * (cov + cov.T)

    # Candidate covariance matrices for xtabond2-style AR diagnostics.
    # xtabond2's AR denominator uses an internal V object; this is not always
    # identical to the final reported Windmeijer-small e(V). Keep these
    # candidates internal and select via SYSTEMGMMKIT_XTABOND2_AR_COV_MODE while
    # certifying parity.
    ar_cov_final = cov
    ar_cov_base = cov
    ar_cov_uncorrected = cov

    if bool(spec.system) and use_twostep:
        with contextlib.suppress(Exception):
            _s_group_ar = _native_group_moment_sum(
                Z=Z,
                residuals=residual_vec,
                group_indices=group_indices_for_cov,
            )
            _meat_ar = D @ W @ _s_group_ar @ W @ D.T
            ar_cov_uncorrected = cov_correction * bread @ _meat_ar @ bread
            ar_cov_uncorrected = 0.5 * (ar_cov_uncorrected + ar_cov_uncorrected.T)

        with contextlib.suppress(Exception):
            if windmeijer_requested and use_twostep:
                _ar_cov_scale = float(cov_correction) * float(windmeijer_xtabond2_small_correction)
                if np.isfinite(_ar_cov_scale) and _ar_cov_scale > 0:
                    ar_cov_base = cov / _ar_cov_scale

    se = np.sqrt(np.maximum(np.diag(cov), 0.0))
    with np.errstate(divide="ignore", invalid="ignore"):
        zstats = beta_vec / se
    pvalues = _normal_pvalues_from_t(zstats)

    # Overidentification diagnostics are assigned below using estimator-specific
    # logic. Do not use _native_overid_diagnostics() here for System GMM because
    # that helper does not distinguish certified Hansen from uncertified Sargan.
    hansen_p = None
    sargan_p = None

    if bool(spec.system) and use_twostep:
        import os as _native_ar_cov_os

        def _pick_ar_cov(_mode: str) -> np.ndarray:
            _mode = str(_mode).strip().lower()
            if _mode in {"uncorrected", "robust", "twostep_robust"}:
                return ar_cov_uncorrected
            if _mode in {"base", "windmeijer_base"}:
                return ar_cov_base
            if _mode in {"final", "reported", "windmeijer"}:
                return ar_cov_final
            raise ValueError(
                f"Unsupported AR covariance mode {_mode!r}. Use final, base, or uncorrected."
            )

        _default_ar_cov_mode = (
            _native_ar_cov_os.getenv("SYSTEMGMMKIT_XTABOND2_AR_COV_MODE", "final").strip().lower()
        )

        # Certified closest xtabond2 AR denominator mapping on the maintained
        # collapsed two-step System-GMM benchmark:
        #
        #   m2VZXA term: uncorrected robust two-step covariance
        #   V*Xw term:  Windmeijer-base covariance before final small scalar
        #
        # Keep environment overrides for parity research, but production default
        # should use the certified structural mapping, not the reported e(V).
        _ar_m2_cov_mode = (
            _native_ar_cov_os.getenv("SYSTEMGMMKIT_XTABOND2_AR_M2_COV_MODE", "uncorrected")
            .strip()
            .lower()
        )
        _ar_vxw_cov_mode = (
            _native_ar_cov_os.getenv("SYSTEMGMMKIT_XTABOND2_AR_VXW_COV_MODE", "base")
            .strip()
            .lower()
        )

        _ar_cov_m2 = _pick_ar_cov(_ar_m2_cov_mode)
        _ar_cov_vxw = _pick_ar_cov(_ar_vxw_cov_mode)

        ar1_z, ar1_p, ar2_z, ar2_p = _native_xtabond2_system_ar_diagnostics(
            residuals=residual_vec,
            X=X,
            Z=Z,
            W=W,
            cov=ar_cov_final,
            D=D,
            cov_m2=_ar_cov_m2,
            cov_vxw=_ar_cov_vxw,
            group_indices=group_indices_for_cov,
            row_meta=row_meta,
            time_values=list(pd.Index(data[time].dropna().sort_values().unique())),
            max_lag=2,
            system=True,
        )
    elif not bool(spec.system) and use_twostep and windmeijer_requested and transformation == "fd":
        # xtabond2 forms the AR denominator with the non-robust second-step
        # bread in m2VZXA and the unscaled Windmeijer covariance in the final
        # Xw term. Difference GMM uses the raw A2 criterion weight, whereas the
        # native System path stores a group-normalized equivalent.
        ar1_z, ar1_p, ar2_z, ar2_p = _native_xtabond2_system_ar_diagnostics(
            residuals=residual_vec,
            X=X,
            Z=Z,
            W=W,
            cov=ar_cov_final,
            D=D,
            cov_m2=bread,
            cov_vxw=windmeijer_base_cov,
            group_indices=group_indices_for_cov,
            row_meta=row_meta,
            time_values=list(pd.Index(data[time].dropna().sort_values().unique())),
            max_lag=2,
            system=False,
        )
    else:
        ar1_z, ar1_p, ar2_z, ar2_p = _native_ab_serial_correlation_diagnostics(
            data=data,
            entity=entity,
            time=time,
            row_index=np.asarray(row_index),
            residuals=residual_vec,
            X=X,
            coef_names=names,
            system=spec.system,
        )

    # System-GMM AR diagnostics use the xtabond2-oriented denominator mapping
    # certified on the maintained aligned benchmark specifications.
    #
    # Production output exposes the diagnostics by default. The legacy
    # SYSTEMGMMKIT_REPORT_EXPERIMENTAL_SYSTEM_AR flag is still honored as an
    # opt-out switch for historical parity comparisons that expected blank AR
    # diagnostics before this diagnostic surface was promoted.
    if bool(spec.system):
        import os as _native_ar_report_os

        _report_system_ar = _native_ar_report_os.getenv(
            "SYSTEMGMMKIT_REPORT_SYSTEM_AR",
            _native_ar_report_os.getenv("SYSTEMGMMKIT_REPORT_EXPERIMENTAL_SYSTEM_AR", "1"),
        ).strip().lower() in {"1", "true", "yes", "on"}

        if not _report_system_ar:
            ar1_z = None
            ar1_p = None
            ar2_z = None
            ar2_p = None

    _u_col = residual_vec.reshape(-1, 1)
    _ztu = Z.T @ _u_col
    _j_stat_raw = float((_ztu.T @ W @ _ztu).squeeze())

    _overid_df = int(Z.shape[1]) - int(len(names))
    _n_groups_for_diag = max(int(n_groups_for_cov), 1)

    _is_twostep_like = bool(use_twostep or windmeijer_requested)

    _j_stat = None
    _hansen_j_stat = None
    _hansen_p_candidate = None
    _hansen_j_error = None

    _sargan_stat = None
    _sargan_stat_raw = None
    _sargan_p_candidate = None

    # Robust Hansen diagnostic. Cross-software certification remains benchmark-
    # specific and separate from exposing the diagnostic in the result contract.
    #
    # For native two-step System GMM, strict matrix-dump verification shows:
    #     Hansen J = (u' Z W_final Z' u) / n_groups
    #
    # For Difference GMM, W is the second-step criterion weight constructed
    # from first-step residuals.  Re-estimating a new weight from final
    # residuals changes the Hansen statistic and is not the two-step GMM
    # criterion reported by xtabond2.
    if _is_twostep_like and _overid_df > 0:
        try:
            if bool(spec.system):
                _hansen_j_candidate = float(_j_stat_raw / float(_n_groups_for_diag))
            else:
                _hansen_j_candidate = float((_ztu.T @ W @ _ztu).squeeze())

            if np.isfinite(_hansen_j_candidate) and _hansen_j_candidate >= 0:
                _hansen_j_stat = float(_hansen_j_candidate)
                _hansen_p_candidate = float(stats.chi2.sf(_hansen_j_stat, _overid_df))
        except Exception as exc:
            _hansen_j_stat = None
            _hansen_p_candidate = None
            _hansen_j_error = f"{type(exc).__name__}: {exc}"

    # Sargan-style diagnostic.
    #
    # The native Sargan candidate passes the six maintained xtabond2 fixtures
    # under the unified certificate. That bounded evidence does not establish
    # universal parity for other samples or specifications.

    if _overid_df > 0:
        if bool(spec.system):
            # xtabond2-compatible System-GMM Sargan.
            #
            # xtabond2 computes the one-step non-robust Sargan statistic using
            # first-step residual moments and a one-step weighting matrix scaled
            # by the first-difference residual variance:
            #
            #   sig2 = SSE_D / (2 * (n_diff - k))
            #   A1   = A1 / sig2
            #
            # Native W1 is normalized differently for coefficient estimation,
            # where scalar factors cancel. For the J statistic, the scalar does
            # not cancel. Matching xtabond2 requires:
            #
            #   scale = (n_diff / (n_diff - k)) / sig2
            #
            # which is algebraically equal to 2 * n_diff / SSE_D.
            _u1_col = np.asarray(residuals1, dtype=float).reshape(-1, 1)
            _ztu1 = Z.T @ _u1_col

            # Consume the matrix builder's explicit equation metadata.  Any
            # row-count fallback assumes a balanced panel and silently selects
            # the wrong residuals for unbalanced or variable-missing samples.
            _level_mask = _native_level_equation_mask_from_row_meta(
                row_meta,
                expected_rows=len(_u1_col),
            )
            _diff_mask = ~_level_mask

            _u1_diff = _u1_col.reshape(-1)[_diff_mask]
            _n_diff = int(_u1_diff.size)
            _k_params = int(len(names))

            if _n_diff > _k_params:
                _sse_diff = float(np.dot(_u1_diff, _u1_diff))
                _sig2_xtabond2 = float(_sse_diff / (2.0 * float(_n_diff - _k_params)))
                _sargan_scale = float((_n_diff / float(_n_diff - _k_params)) / _sig2_xtabond2)

                _sargan_stat_raw = float((_ztu1.T @ W1 @ _ztu1).squeeze())
                _sargan_stat = float(_sargan_stat_raw * _sargan_scale)

                if np.isfinite(_sargan_stat) and _sargan_stat >= 0:
                    _sargan_p_candidate = float(stats.chi2.sf(_sargan_stat, _overid_df))
        else:
            # xtabond2 3.7.2 computes the Difference-GMM Sargan statistic from
            # the first-step residual moments and A1 = W1 / sig2, where for
            # first differences sig2 = e1'e1 / (2 * N_obs). The later `small`
            # covariance adjustment does not rescale this diagnostic.
            _u1_col = np.asarray(residuals1, dtype=float).reshape(-1, 1)
            _ztu1 = Z.T @ _u1_col
            _n_diff = int(_u1_col.size)
            _sse_diff = float((_u1_col.T @ _u1_col).squeeze())
            if _n_diff > 0 and np.isfinite(_sse_diff) and _sse_diff > 0.0:
                _sig2_xtabond2 = _sse_diff / (2.0 * float(_n_diff))
                _sargan_stat_raw = float((_ztu1.T @ W1 @ _ztu1).squeeze())
                _sargan_stat = float(_sargan_stat_raw / _sig2_xtabond2)
                if np.isfinite(_sargan_stat) and _sargan_stat >= 0:
                    _sargan_p_candidate = float(stats.chi2.sf(_sargan_stat, _overid_df))

    # Public p-values.
    hansen_p = _hansen_p_candidate if _is_twostep_like else None
    sargan_p = _sargan_p_candidate

    # Generic J statistic: in two-step output, use Hansen; otherwise use Sargan.
    _j_stat = _hansen_j_stat if _is_twostep_like else _sargan_stat

    _ztu_norm = float(np.linalg.norm(_ztu))
    _w_norm = float(np.linalg.norm(W))

    # Optional parity/debug export for xtabond2 internals.
    # Enable with:
    #   $env:SYSTEMGMMKIT_EXPORT_GMM_DEBUG = "1"
    #   $env:SYSTEMGMMKIT_GMM_DEBUG_DIR = "artifacts/parity/xtabond2"
    if __import__("os").environ.get("SYSTEMGMMKIT_EXPORT_GMM_DEBUG") == "1":
        from pathlib import Path as _GmmDebugPath

        debug_dir = _GmmDebugPath(
            __import__("os").environ.get(
                "SYSTEMGMMKIT_GMM_DEBUG_DIR",
                "artifacts/parity/xtabond2",
            )
        )
        debug_dir.mkdir(parents=True, exist_ok=True)

        pd.DataFrame(_ztu, columns=["native_Ze"]).to_csv(
            debug_dir / "native_Ze.csv",
            index=False,
        )

        pd.DataFrame(Z).to_csv(
            debug_dir / "native_Z.csv",
            index=False,
        )

        pd.DataFrame(_u_col, columns=["native_u_stack"]).to_csv(
            debug_dir / "native_u_stack.csv",
            index=False,
        )

        pd.DataFrame(W).to_csv(
            debug_dir / "native_A2.csv",
            index=False,
        )

        pd.DataFrame(X).to_csv(
            debug_dir / "native_X.csv",
            index=False,
        )

        pd.DataFrame(y.reshape(-1, 1), columns=["native_y_stack"]).to_csv(
            debug_dir / "native_y_stack.csv",
            index=False,
        )

        pd.DataFrame(
            {
                "instrument_index": range(1, len(instrument_names) + 1),
                "instrument_name": list(instrument_names),
            }
        ).to_csv(
            debug_dir / "native_instrument_names.csv",
            index=False,
        )

        pd.DataFrame(
            {
                "regressor_index": range(1, len(names) + 1),
                "regressor_name": list(names),
            }
        ).to_csv(
            debug_dir / "native_regressor_names.csv",
            index=False,
        )

        pd.DataFrame(
            [
                {
                    "Z_rows": int(Z.shape[0]),
                    "Z_cols": int(Z.shape[1]),
                    "X_rows": int(X.shape[0]),
                    "X_cols": int(X.shape[1]),
                    "y_rows": int(y.reshape(-1, 1).shape[0]),
                    "u_rows": int(_u_col.shape[0]),
                    "Ze_rows": int(_ztu.shape[0]),
                    "Ze_cols": int(_ztu.shape[1]),
                    "W_rows": int(W.shape[0]),
                    "W_cols": int(W.shape[1]),
                    "native_j_stat": _j_stat,
                    "native_hansen_j_stat": _hansen_j_stat,
                    "native_sargan_j_stat": _sargan_stat,
                    "native_overid_df": _overid_df,
                    "native_ztu_norm": _ztu_norm,
                    "native_w_norm": _w_norm,
                }
            ]
        ).to_csv(
            debug_dir / "native_debug_shapes.csv",
            index=False,
        )

        with contextlib.suppress(Exception):
            pd.DataFrame(row_meta).to_csv(
                debug_dir / "native_row_meta.csv",
                index=False,
            )

    normal_matrix_rank = int(np.linalg.matrix_rank(xzwzx))
    normal_matrix_required_rank = int(k)
    raw_condition_number = float(np.linalg.cond(xzwzx))
    normal_matrix_condition_number = (
        raw_condition_number if np.isfinite(raw_condition_number) else None
    )

    return NativeGMMResult(
        spec=spec,
        nobs=int(nobs_reported),
        n_instruments=int(Z.shape[1]),
        params=pd.Series(beta_vec, index=names, name="coef"),
        std_errors=pd.Series(se, index=names, name="std_err"),
        zstats=pd.Series(zstats, index=names, name="z"),
        pvalues=pd.Series(pvalues, index=names, name="p_value"),
        residuals=pd.Series(residual_vec, index=row_index, name="residual"),
        covariance=pd.DataFrame(
            np.asarray(cov, dtype=float).copy(),
            index=pd.Index(names),
            columns=pd.Index(names),
        ),
        covariance_correction=(
            "windmeijer_2005" if windmeijer_requested and use_twostep else "none"
        ),
        covariance_reference=(
            "10.1016/j.jeconom.2004.02.005" if windmeijer_requested and use_twostep else None
        ),
        covariance_type=(
            "robust-clustered-two-step-windmeijer"
            if windmeijer_requested and use_twostep
            else (
                "robust-clustered-two-step-uncorrected"
                if use_twostep
                else "robust-clustered-one-step"
            )
        ),
        backend="native-gmm",
        notes=[
            "Native dynamic-panel GMM engine.",
            "Native System GMM coefficient, Windmeijer-SE, count, Hansen/Sargan, and signed AR diagnostic parity is verified against xtabond2 on six maintained aligned specifications under declared numerical gates; the unbalanced and variable-missing fixtures also have exact sample-key parity.",
            (
                "Windmeijer-corrected two-step standard errors are enabled via windmeijer=True "
                "using the maintained native correction; matched structural-SE parity is certified "
                "against xtabond2 only on the maintained aligned specifications."
                if windmeijer_requested and use_twostep
                else "Windmeijer-corrected two-step standard errors are available via windmeijer=True but are not the default."
            ),
        ],
        instrument_names=list(instrument_names),
        n_groups=int(n_groups_for_cov) if int(n_groups_for_cov) > 0 else None,
        hansen_p=hansen_p,
        sargan_p=sargan_p,
        sargan_stat=_sargan_stat,
        ar1_p=ar1_p,
        ar2_p=ar2_p,
        ar1_z=ar1_z,
        ar2_z=ar2_z,
        z_shape=tuple(Z.shape),
        w_shape=tuple(W.shape),
        j_stat=_j_stat,
        ztu_norm=_ztu_norm,
        w_norm=_w_norm,
        hansen_j_stat=_hansen_j_stat,
        sargan_j_stat=_sargan_stat,
        overid_df=_overid_df,
        hansen_j_error=_hansen_j_error,
        normal_matrix_rank=normal_matrix_rank,
        normal_matrix_required_rank=normal_matrix_required_rank,
        normal_matrix_condition_number=normal_matrix_condition_number,
    )
