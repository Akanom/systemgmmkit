from __future__ import annotations

from collections.abc import Mapping, Sequence

from .fixed_effects import CovarianceType, FixedEffectsSpec
from .spec import DynamicPanelSpec, GMMStyle, IVStyle, Steps, Transformation
from .suite import PanelModelSuite

LagMap = Mapping[str, tuple[int, int]]


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


def _lag_for(variable: str, lag_limits: LagMap | None, default: tuple[int, int]) -> tuple[int, int]:
    if lag_limits and variable in lag_limits:
        return lag_limits[variable]
    return default


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

    This is intentionally domain-neutral. It can represent pooled OLS
    (no entity/time effects), one-way FE, or two-way FE depending on the
    effect flags.
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
    lag_limits: LagMap | None = None,
    default_lag: tuple[int, int] = (2, 2),
    dependent_lag_limits: tuple[int, int] = (2, 3),
    system: bool = True,
    collapse: bool = True,
    time_dummies: bool = True,
    transformation: Transformation = "fod",
    steps: Steps = "twostep",
    name: str | None = None,
) -> DynamicPanelSpec:
    """Build a generic Difference/System GMM dynamic-panel specification.

    Parameters are deliberately econometric rather than thesis-specific:
    choose the dependent variable, regressors, controls, interaction terms,
    and classify variables as endogenous, predetermined, or exogenous.

    Notes
    -----
    The current pydynpd backend maps both endogenous and predetermined
    variables to GMM-style internal instruments. Use conservative lag windows
    and collapsed instruments for production work.
    """

    if lagged_dependent_lag < 1:
        raise ValueError("lagged_dependent_lag must be >= 1.")

    lhs_regressors: list[str] = []
    if lagged_dependent:
        lhs_regressors.append(f"L{lagged_dependent_lag}.{dependent}")

    lhs_regressors.extend([*regressors, *_as_list(controls), *_as_list(interactions)])
    lhs_regressors = _dedupe(lhs_regressors)

    gmm_blocks: list[GMMStyle] = []
    if lagged_dependent:
        min_lag, max_lag = _lag_for(dependent, lag_limits, dependent_lag_limits)
        gmm_blocks.append(GMMStyle(dependent, min_lag, max_lag))

    for variable in _dedupe([*_as_list(endogenous), *_as_list(predetermined)]):
        min_lag, max_lag = _lag_for(variable, lag_limits, default_lag)
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
        lag_limits=lag_limits,
        system=system,
    )
    return PanelModelSuite(name=name, fixed_effects=fe_spec, dynamic_gmm=gmm_spec)
