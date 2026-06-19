from __future__ import annotations

from pathlib import Path

ROOT = Path.cwd()
PRESETS = ROOT / "src" / "systemgmmkit" / "presets.py"

if not PRESETS.exists():
    raise FileNotFoundError(f"Could not find {PRESETS}")


content = r'''from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Literal

from .fixed_effects import CovarianceType, FixedEffectsSpec
from .spec import DynamicPanelSpec, GMMStyle, IVStyle, Steps, Transformation
from .suite import PanelModelSuite


LagWindow = tuple[int, int]
LagMap = Mapping[str, LagWindow]
RoleName = Literal["endogenous", "predetermined"]


def _as_list(values: Sequence[str] | None) -> list[str]:
    return list(values or [])


def _dedupe(values: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if value not in seen:
            out.append(value)
            seen.add(value)
    return out


def _validate_lag_window(name: str, window: LagWindow) -> LagWindow:
    if not isinstance(window, tuple) or len(window) != 2:
        raise TypeError(f"{name} must be a tuple of two integers, for example (2, 4).")

    min_lag, max_lag = window

    if not isinstance(min_lag, int) or not isinstance(max_lag, int):
        raise TypeError(f"{name} must contain integer lag bounds.")

    if min_lag < 0 or max_lag < 0:
        raise ValueError(f"{name} cannot contain negative lag values.")

    if min_lag > max_lag:
        raise ValueError(f"{name} has min lag greater than max lag: {window!r}.")

    return min_lag, max_lag


def _normalise_role(role: str) -> RoleName:
    value = role.strip().lower()

    if value in {"endog", "endogenous"}:
        return "endogenous"

    if value in {"predet", "predetermined"}:
        return "predetermined"

    if value in {"exog", "exogenous"}:
        raise ValueError(
            "Exogenous variables are IV-style by default and should not be assigned "
            "GMM-style lag windows through gmm_lags_by_role. If a lagged exogenous "
            "variable belongs in the structural equation, create it as a column and "
            "include it in exogenous."
        )

    raise ValueError(
        f"Unknown GMM lag-window role {role!r}. "
        "Supported roles are 'endogenous' and 'predetermined'."
    )


def _normalise_role_lags(
    values: Mapping[str, LagWindow] | None,
) -> dict[RoleName, LagWindow]:
    if not values:
        return {}

    out: dict[RoleName, LagWindow] = {}
    for role, window in values.items():
        normalised = _normalise_role(role)
        out[normalised] = _validate_lag_window(f"gmm_lags_by_role[{role!r}]", window)
    return out


def _normalise_variable_lags(
    values: Mapping[str, LagWindow] | None,
) -> dict[str, LagWindow]:
    if not values:
        return {}

    out: dict[str, LagWindow] = {}
    for variable, window in values.items():
        if not isinstance(variable, str) or not variable.strip():
            raise ValueError("gmm_lags_by_variable keys must be non-empty variable names.")
        out[variable] = _validate_lag_window(
            f"gmm_lags_by_variable[{variable!r}]",
            window,
        )
    return out


def _resolve_gmm_lag_window(
    *,
    variable: str,
    role: RoleName,
    gmm_lags: LagWindow,
    gmm_lags_by_role: Mapping[RoleName, LagWindow],
    gmm_lags_by_variable: Mapping[str, LagWindow],
) -> LagWindow:
    """Resolve GMM instrument lag windows.

    Precedence:

    1. variable-specific override;
    2. role-specific override;
    3. global gmm_lags.
    """

    if variable in gmm_lags_by_variable:
        return gmm_lags_by_variable[variable]

    if role in gmm_lags_by_role:
        return gmm_lags_by_role[role]

    return gmm_lags


def build_fixed_effects_spec(
    *,
    dependent: str,
    regressors: Sequence[str],
    controls: Sequence[str] | None = None,
    interactions: Sequence[str] | None = None,
    entity_effects: bool = True,
    time_effects: bool = True,
    covariance: CovarianceType = "clustered",
    cluster: str = "entity",
    name: str = "fixed_effects",
) -> FixedEffectsSpec:
    """Build a generic static panel specification.

    This can represent pooled OLS, one-way FE, or two-way FE depending on
    the effect flags.
    """

    all_regressors = _dedupe([*regressors, *_as_list(controls), *_as_list(interactions)])

    return FixedEffectsSpec(
        name=name,
        dependent=dependent,
        regressors=all_regressors,
        entity_effects=entity_effects,
        time_effects=time_effects,
        covariance=covariance,
        cluster=cluster,  # type: ignore[arg-type]
    )


def build_dynamic_panel_gmm_spec(
    *,
    dependent: str,
    regressors: Sequence[str],
    controls: Sequence[str] | None = None,
    interactions: Sequence[str] | None = None,
    lagged_dependent: bool = True,
    lagged_dependent_lag: int = 1,
    endogenous: Sequence[str] | None = None,
    predetermined: Sequence[str] | None = None,
    exogenous: Sequence[str] | None = None,
    gmm_lags: LagWindow = (2, 2),
    gmm_lags_by_role: Mapping[str, LagWindow] | None = None,
    gmm_lags_by_variable: Mapping[str, LagWindow] | None = None,
    # Backward-compatible aliases from earlier generic preset work.
    lag_limits: LagMap | None = None,
    default_lag: LagWindow | None = None,
    dependent_lag_limits: LagWindow | None = None,
    system: bool = True,
    collapse: bool = True,
    time_dummies: bool = True,
    transformation: Transformation = "fod",
    steps: Steps = "twostep",
    name: str | None = None,
) -> DynamicPanelSpec:
    """Build a generic Difference/System GMM dynamic-panel specification.

    The function supports three levels of GMM instrument lag-window control:

    1. global default through ``gmm_lags``;
    2. role-specific overrides through ``gmm_lags_by_role``;
    3. variable-specific overrides through ``gmm_lags_by_variable``.

    Precedence:

    ``gmm_lags_by_variable > gmm_lags_by_role > gmm_lags``

    Exogenous variables remain IV-style by default.
    """

    if lagged_dependent_lag < 1:
        raise ValueError("lagged_dependent_lag must be >= 1.")

    # Backward compatibility:
    # - old default_lag is treated as the global GMM lag window when supplied;
    # - old lag_limits is treated as variable-specific lag windows.
    global_lags = _validate_lag_window("gmm_lags", default_lag or gmm_lags)

    role_lags = _normalise_role_lags(gmm_lags_by_role)

    variable_lags = _normalise_variable_lags(gmm_lags_by_variable)
    legacy_variable_lags = _normalise_variable_lags(lag_limits)

    # Explicit gmm_lags_by_variable wins over legacy lag_limits.
    merged_variable_lags = {
        **legacy_variable_lags,
        **variable_lags,
    }

    lhs_regressors: list[str] = []

    if lagged_dependent:
        lhs_regressors.append(f"L{lagged_dependent_lag}.{dependent}")

    lhs_regressors.extend(
        [
            *regressors,
            *_as_list(controls),
            *_as_list(interactions),
        ]
    )
    lhs_regressors = _dedupe(lhs_regressors)

    gmm_blocks: list[GMMStyle] = []

    if lagged_dependent:
        if (
            dependent_lag_limits is not None
            and dependent not in merged_variable_lags
            and "endogenous" not in role_lags
        ):
            dep_min_lag, dep_max_lag = _validate_lag_window(
                "dependent_lag_limits",
                dependent_lag_limits,
            )
        else:
            dep_min_lag, dep_max_lag = _resolve_gmm_lag_window(
                variable=dependent,
                role="endogenous",
                gmm_lags=global_lags,
                gmm_lags_by_role=role_lags,
                gmm_lags_by_variable=merged_variable_lags,
            )

        gmm_blocks.append(GMMStyle(dependent, dep_min_lag, dep_max_lag))

    for variable in _dedupe(_as_list(endogenous)):
        min_lag, max_lag = _resolve_gmm_lag_window(
            variable=variable,
            role="endogenous",
            gmm_lags=global_lags,
            gmm_lags_by_role=role_lags,
            gmm_lags_by_variable=merged_variable_lags,
        )
        gmm_blocks.append(GMMStyle(variable, min_lag, max_lag))

    for variable in _dedupe(_as_list(predetermined)):
        min_lag, max_lag = _resolve_gmm_lag_window(
            variable=variable,
            role="predetermined",
            gmm_lags=global_lags,
            gmm_lags_by_role=role_lags,
            gmm_lags_by_variable=merged_variable_lags,
        )
        gmm_blocks.append(GMMStyle(variable, min_lag, max_lag))

    iv_blocks = [IVStyle(variable) for variable in _dedupe(_as_list(exogenous))]

    model_label = "system_gmm" if system else "difference_gmm"

    return DynamicPanelSpec(
        name=name or model_label,
        dependent=dependent,
        regressors=lhs_regressors,
        gmm=gmm_blocks,
        iv=iv_blocks,
        time_dummies=time_dummies,
        system=system,
        collapse=collapse,
        transformation=transformation,
        steps=steps,
    )


def build_system_gmm_spec(**kwargs: object) -> DynamicPanelSpec:
    """Build a generic Blundell-Bond-style System GMM specification."""

    return build_dynamic_panel_gmm_spec(**kwargs, system=True)  # type: ignore[arg-type]


def build_difference_gmm_spec(**kwargs: object) -> DynamicPanelSpec:
    """Build a generic Arellano-Bond-style Difference GMM specification."""

    return build_dynamic_panel_gmm_spec(**kwargs, system=False)  # type: ignore[arg-type]


def build_panel_model_suite(
    *,
    name: str,
    dependent: str,
    regressors: Sequence[str],
    controls: Sequence[str] | None = None,
    interactions: Sequence[str] | None = None,
    endogenous: Sequence[str] | None = None,
    predetermined: Sequence[str] | None = None,
    exogenous: Sequence[str] | None = None,
    gmm_lags: LagWindow = (2, 2),
    gmm_lags_by_role: Mapping[str, LagWindow] | None = None,
    gmm_lags_by_variable: Mapping[str, LagWindow] | None = None,
    lag_limits: LagMap | None = None,
    system: bool = True,
    entity_effects: bool = True,
    time_effects: bool = True,
) -> PanelModelSuite:
    """Build a generic FE + dynamic GMM suite for any panel-data topic."""

    fe_spec = build_fixed_effects_spec(
        name=f"{name}_fe",
        dependent=dependent,
        regressors=regressors,
        controls=controls,
        interactions=interactions,
        entity_effects=entity_effects,
        time_effects=time_effects,
    )

    gmm_spec = build_dynamic_panel_gmm_spec(
        name=f"{name}_{'system_gmm' if system else 'difference_gmm'}",
        dependent=dependent,
        regressors=regressors,
        controls=controls,
        interactions=interactions,
        endogenous=endogenous,
        predetermined=predetermined,
        exogenous=exogenous,
        gmm_lags=gmm_lags,
        gmm_lags_by_role=gmm_lags_by_role,
        gmm_lags_by_variable=gmm_lags_by_variable,
        lag_limits=lag_limits,
        system=system,
    )

    return PanelModelSuite(
        name=name,
        fixed_effects=fe_spec,
        dynamic_gmm=gmm_spec,
    )
'''

PRESETS.write_text(content, encoding="utf-8")
print(f"Rewrote {PRESETS}")
