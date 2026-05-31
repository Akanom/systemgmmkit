from __future__ import annotations

from .fixed_effects import FixedEffectsSpec
from .presets import build_dynamic_panel_gmm_spec, build_fixed_effects_spec
from .spec import DynamicPanelSpec
from .suite import PanelModelSuite


def aid_growth_techshare_spec(
    *,
    include_controls: bool = True,
    include_three_way: bool = True,
    system: bool = True,
) -> DynamicPanelSpec:
    """Domain preset for the author's aid-growth TechShare model.

    Kept as a domain example. The package core is generic and should not be
    interpreted as aid-growth-only.
    """

    controls = ["econ_dev_index", "human_dev_index", "lpop"] if include_controls else []
    interactions = (
        ["s_tech_frag", "s_tech_polity", "s_frag_polity", "s_tech_frag_polity"]
        if include_three_way
        else []
    )
    return build_dynamic_panel_gmm_spec(
        name="aid_growth_techshare_three_way"
        if include_three_way
        else "aid_growth_techshare_baseline",
        dependent="growth_rate",
        regressors=["lPA", "s_techshare", "frag_index_orth", "polity2"],
        controls=controls,
        interactions=interactions,
        endogenous=["lPA", "s_techshare", "frag_index_orth", "polity2"],
        exogenous=[*controls, *interactions],
        lag_limits={"growth_rate": (2, 3)},
        system=system,
    )


def aid_growth_ta_decomposition_spec(
    *,
    include_controls: bool = True,
    include_three_way: bool = True,
    system: bool = True,
) -> DynamicPanelSpec:
    """Domain preset for TA/NTA decomposition in aid-growth GMM."""

    controls = ["econ_dev_index", "human_dev_index", "lpop"] if include_controls else []
    interactions = (
        ["s_ta_frag", "s_ta_polity", "s_frag_polity", "s_ta_frag_polity"]
        if include_three_way
        else []
    )
    return build_dynamic_panel_gmm_spec(
        name="aid_growth_ta_nta_decomposition_three_way"
        if include_three_way
        else "aid_growth_ta_nta_decomposition_baseline",
        dependent="growth_rate",
        regressors=["lPA", "s_TA_frac", "s_NTA_frac", "frag_index_orth", "polity2"],
        controls=controls,
        interactions=interactions,
        endogenous=["lPA", "s_TA_frac", "s_NTA_frac", "frag_index_orth", "polity2"],
        exogenous=[*controls, *interactions],
        lag_limits={"growth_rate": (2, 3)},
        system=system,
    )


def aid_growth_fe_techshare_spec(
    *,
    include_controls: bool = True,
    include_three_way: bool = True,
    entity_effects: bool = True,
    time_effects: bool = True,
) -> FixedEffectsSpec:
    """Domain preset for aid-growth fixed effects."""

    controls = ["econ_dev_index", "human_dev_index", "lpop"] if include_controls else []
    interactions = (
        ["s_tech_frag", "s_tech_polity", "s_frag_polity", "s_tech_frag_polity"]
        if include_three_way
        else []
    )
    return build_fixed_effects_spec(
        name="aid_growth_fe_techshare_three_way"
        if include_three_way
        else "aid_growth_fe_techshare_baseline",
        dependent="growth_rate",
        regressors=["lPA", "s_techshare", "frag_index_orth", "polity2"],
        controls=controls,
        interactions=interactions,
        entity_effects=entity_effects,
        time_effects=time_effects,
    )


def aid_growth_fe_ta_decomposition_spec(
    *,
    include_controls: bool = True,
    include_three_way: bool = True,
    entity_effects: bool = True,
    time_effects: bool = True,
) -> FixedEffectsSpec:
    """Domain preset for aid-growth TA/NTA fixed effects."""

    controls = ["econ_dev_index", "human_dev_index", "lpop"] if include_controls else []
    interactions = (
        ["s_ta_frag", "s_ta_polity", "s_frag_polity", "s_ta_frag_polity"]
        if include_three_way
        else []
    )
    return build_fixed_effects_spec(
        name="aid_growth_fe_ta_nta_decomposition_three_way"
        if include_three_way
        else "aid_growth_fe_ta_nta_decomposition_baseline",
        dependent="growth_rate",
        regressors=["lPA", "s_TA_frac", "s_NTA_frac", "frag_index_orth", "polity2"],
        controls=controls,
        interactions=interactions,
        entity_effects=entity_effects,
        time_effects=time_effects,
    )


def aid_growth_techshare_suite(
    *,
    include_controls: bool = True,
    include_three_way: bool = True,
    system: bool = True,
) -> PanelModelSuite:
    """Domain suite pairing aid-growth FE with dynamic GMM robustness."""

    return PanelModelSuite(
        name="aid_growth_techshare_fe_plus_gmm",
        fixed_effects=aid_growth_fe_techshare_spec(
            include_controls=include_controls,
            include_three_way=include_three_way,
        ),
        dynamic_gmm=aid_growth_techshare_spec(
            include_controls=include_controls,
            include_three_way=include_three_way,
            system=system,
        ),
    )
