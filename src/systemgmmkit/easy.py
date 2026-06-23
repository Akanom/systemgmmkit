"""Convenience dynamic-panel GMM wrappers.

This module provides user-facing helpers around the validated lower-level
GMM spec builders and runners. The wrappers are intentionally additive:
they do not replace or rewrite the underlying estimators.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Optional

import pandas as pd

LagWindow = tuple[int, int]


@dataclass(frozen=True)
class DynamicGMMWorkflowResult:
    """Container returned when ``return_workflow=True``."""

    result: Any
    spec: Any
    data: pd.DataFrame
    dependent: str
    entity: str
    time: str
    regressors: tuple[str, ...]
    endogenous: tuple[str, ...]
    predetermined: tuple[str, ...]
    exogenous: tuple[str, ...]
    gmm_lags: LagWindow
    collapse: bool
    time_effects: bool
    model: str


def _as_tuple(values: Optional[Sequence[str]]) -> tuple[str, ...]:
    if values is None:
        return ()
    return tuple(str(value) for value in values)


def _unique(values: Sequence[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if value not in seen:
            out.append(value)
            seen.add(value)
    return tuple(out)


def _validate_lag_window(gmm_lags: LagWindow) -> LagWindow:
    if not isinstance(gmm_lags, tuple) or len(gmm_lags) != 2:
        raise TypeError("gmm_lags must be a tuple of two integers, for example (2, 4).")

    start, stop = int(gmm_lags[0]), int(gmm_lags[1])

    if start < 1:
        raise ValueError("gmm_lags start must be >= 1.")
    if stop < start:
        raise ValueError("gmm_lags stop must be >= start.")

    return start, stop


def _add_lagged_dependent(
    data: pd.DataFrame,
    *,
    entity: str,
    time: str,
    dependent: str,
    lagged_dependent: Optional[int],
) -> tuple[pd.DataFrame, tuple[str, ...]]:
    if lagged_dependent is None or lagged_dependent <= 0:
        return data.copy(), ()

    out = data.sort_values([entity, time]).copy()
    lagged_cols: list[str] = []

    for lag in range(1, int(lagged_dependent) + 1):
        col = f"L{lag}_{dependent}"
        if col not in out.columns:
            out[col] = out.groupby(entity)[dependent].shift(lag)
        lagged_cols.append(col)

    return out, tuple(lagged_cols)


def _prepare_roles(
    *,
    regressors: Sequence[str],
    controls: Sequence[str],
    lagged_cols: Sequence[str],
    endogenous: Sequence[str],
    predetermined: Sequence[str],
    exogenous: Sequence[str],
    lagged_dependent_role: str,
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    allowed_roles = {"endogenous", "predetermined", "exogenous", "none"}
    if lagged_dependent_role not in allowed_roles:
        raise ValueError(
            "lagged_dependent_role must be one of "
            "'endogenous', 'predetermined', 'exogenous', or 'none'."
        )

    final_regressors = _unique(tuple(regressors) + tuple(controls) + tuple(lagged_cols))
    final_endogenous = list(_unique(endogenous))
    final_predetermined = list(_unique(predetermined))
    final_exogenous = list(_unique(exogenous))

    if lagged_dependent_role == "endogenous":
        final_endogenous.extend(lagged_cols)
    elif lagged_dependent_role == "predetermined":
        final_predetermined.extend(lagged_cols)
    elif lagged_dependent_role == "exogenous":
        final_exogenous.extend(lagged_cols)

    classified = set(final_endogenous) | set(final_predetermined) | set(final_exogenous)
    unclassified = [var for var in final_regressors if var not in classified]

    # User-friendly default: regressors not explicitly classified are treated as exogenous.
    final_exogenous.extend(unclassified)

    return (
        final_regressors,
        _unique(final_endogenous),
        _unique(final_predetermined),
        _unique(final_exogenous),
    )


def _drop_model_missing(
    data: pd.DataFrame,
    *,
    entity: str,
    time: str,
    dependent: str,
    regressors: Sequence[str],
) -> pd.DataFrame:
    out = data.replace([float("inf"), float("-inf")], pd.NA).copy()
    subset = _unique((entity, time, dependent) + tuple(regressors))
    return out.dropna(subset=list(subset)).copy()


def _run_dynamic_gmm(
    *,
    model: str,
    data: pd.DataFrame,
    entity: str,
    time: str,
    dependent: str,
    regressors: Optional[Sequence[str]],
    controls: Optional[Sequence[str]],
    endogenous: Optional[Sequence[str]],
    predetermined: Optional[Sequence[str]],
    exogenous: Optional[Sequence[str]],
    lagged_dependent: Optional[int],
    lagged_dependent_role: str,
    gmm_lags: LagWindow,
    collapse: bool,
    backend: str,
    windmeijer: Optional[bool],
    time_effects: bool,
    drop_missing: bool,
    return_workflow: bool,
    spec_options: dict[str, Any],
) -> Any:
    gmm_lags = _validate_lag_window(gmm_lags)

    model_data, lagged_cols = _add_lagged_dependent(
        data,
        entity=entity,
        time=time,
        dependent=dependent,
        lagged_dependent=lagged_dependent,
    )

    final_regressors, final_endogenous, final_predetermined, final_exogenous = _prepare_roles(
        regressors=_as_tuple(regressors),
        controls=_as_tuple(controls),
        lagged_cols=lagged_cols,
        endogenous=_as_tuple(endogenous),
        predetermined=_as_tuple(predetermined),
        exogenous=_as_tuple(exogenous),
        lagged_dependent_role=lagged_dependent_role,
    )

    if drop_missing:
        model_data = _drop_model_missing(
            model_data,
            entity=entity,
            time=time,
            dependent=dependent,
            regressors=final_regressors,
        )

    spec_kwargs: dict[str, Any] = {
        "dependent": dependent,
        "regressors": list(final_regressors),
        "endogenous": list(final_endogenous),
        "predetermined": list(final_predetermined),
        "exogenous": list(final_exogenous),
        "gmm_lags": gmm_lags,
        "collapse": collapse,
        "time_dummies": time_effects,
    }
    spec_kwargs.update(spec_options)

    if model == "system":
        from systemgmmkit import build_system_gmm_spec, run_system_gmm

        if windmeijer is not None:
            spec_kwargs["windmeijer"] = windmeijer

        spec = build_system_gmm_spec(**spec_kwargs)
        run_kwargs: dict[str, Any] = {
            "spec": spec,
            "data": model_data,
            "entity": entity,
            "time": time,
            "backend": backend,
        }
        if windmeijer is not None:
            run_kwargs["windmeijer"] = windmeijer
        result = run_system_gmm(**run_kwargs)

    elif model == "difference":
        from systemgmmkit import build_difference_gmm_spec, run_difference_gmm

        spec = build_difference_gmm_spec(**spec_kwargs)
        run_kwargs = {
            "spec": spec,
            "data": model_data,
            "entity": entity,
            "time": time,
            "backend": backend,
        }
        if windmeijer is not None:
            run_kwargs["windmeijer"] = windmeijer
        result = run_difference_gmm(**run_kwargs)

    else:
        raise ValueError("model must be 'system' or 'difference'.")

    if not return_workflow:
        return result

    return DynamicGMMWorkflowResult(
        result=result,
        spec=spec,
        data=model_data,
        dependent=dependent,
        entity=entity,
        time=time,
        regressors=final_regressors,
        endogenous=final_endogenous,
        predetermined=final_predetermined,
        exogenous=final_exogenous,
        gmm_lags=gmm_lags,
        collapse=collapse,
        time_effects=time_effects,
        model=model,
    )


def system_gmm(
    *,
    data: pd.DataFrame,
    entity: str,
    time: str,
    dependent: str,
    regressors: Optional[Sequence[str]] = None,
    controls: Optional[Sequence[str]] = None,
    endogenous: Optional[Sequence[str]] = None,
    predetermined: Optional[Sequence[str]] = None,
    exogenous: Optional[Sequence[str]] = None,
    lagged_dependent: Optional[int] = 1,
    lagged_dependent_role: str = "endogenous",
    gmm_lags: LagWindow = (2, 2),
    collapse: bool = True,
    backend: str = "auto",
    windmeijer: Optional[bool] = True,
    time_effects: bool = False,
    drop_missing: bool = True,
    return_workflow: bool = False,
    **spec_options: Any,
) -> Any:
    """Build and run a System GMM model with a simpler user-facing API.

    Unclassified regressors are treated as exogenous by default. If
    ``lagged_dependent=1``, a column named ``L1_<dependent>`` is created,
    added to the model equation, and classified as endogenous by default.
    Time effects are disabled by default in the easy API to avoid
    high-dimensional time-dummy expansion in long-T panels. Set
    ``time_effects=True`` when time dummies are theoretically required.
    Time effects are disabled by default in the easy API to avoid
    high-dimensional time-dummy expansion in long-T panels. Set
    ``time_effects=True`` when time dummies are theoretically required.
    """

    return _run_dynamic_gmm(
        model="system",
        data=data,
        entity=entity,
        time=time,
        dependent=dependent,
        regressors=regressors,
        controls=controls,
        endogenous=endogenous,
        predetermined=predetermined,
        exogenous=exogenous,
        lagged_dependent=lagged_dependent,
        lagged_dependent_role=lagged_dependent_role,
        gmm_lags=gmm_lags,
        collapse=collapse,
        backend=backend,
        windmeijer=windmeijer,
        time_effects=time_effects,
        drop_missing=drop_missing,
        return_workflow=return_workflow,
        spec_options=spec_options,
    )


def difference_gmm(
    *,
    data: pd.DataFrame,
    entity: str,
    time: str,
    dependent: str,
    regressors: Optional[Sequence[str]] = None,
    controls: Optional[Sequence[str]] = None,
    endogenous: Optional[Sequence[str]] = None,
    predetermined: Optional[Sequence[str]] = None,
    exogenous: Optional[Sequence[str]] = None,
    lagged_dependent: Optional[int] = 1,
    lagged_dependent_role: str = "endogenous",
    gmm_lags: LagWindow = (2, 2),
    collapse: bool = True,
    backend: str = "auto",
    windmeijer: Optional[bool] = None,
    time_effects: bool = False,
    drop_missing: bool = True,
    return_workflow: bool = False,
    **spec_options: Any,
) -> Any:
    """Build and run a Difference GMM model with a simpler user-facing API.

    Unclassified regressors are treated as exogenous by default. If
    ``lagged_dependent=1``, a column named ``L1_<dependent>`` is created,
    added to the model equation, and classified as endogenous by default.
    """

    return _run_dynamic_gmm(
        model="difference",
        data=data,
        entity=entity,
        time=time,
        dependent=dependent,
        regressors=regressors,
        controls=controls,
        endogenous=endogenous,
        predetermined=predetermined,
        exogenous=exogenous,
        lagged_dependent=lagged_dependent,
        lagged_dependent_role=lagged_dependent_role,
        gmm_lags=gmm_lags,
        collapse=collapse,
        backend=backend,
        windmeijer=windmeijer,
        time_effects=time_effects,
        drop_missing=drop_missing,
        return_workflow=return_workflow,
        spec_options=spec_options,
    )
