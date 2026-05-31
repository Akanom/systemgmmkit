"""Preset specifications for common aid-growth panel models."""

from .fixed_effects import FixedEffectsSpec
from .spec import DynamicPanelSpec, GMMStyle, IVStyle
from .suite import PanelModelSuite


def aid_growth_techshare_spec(
    *,
    include_controls: bool = True,
    include_three_way: bool = True,
    system: bool = True,
) -> DynamicPanelSpec:
    """Preset for the user's aid-growth TechShare System GMM model."""

    regressors = ["L1.growth_rate", "lPA", "s_techshare", "frag_index_orth", "polity2"]
    iv = []

    if include_three_way:
        regressors.extend(["s_tech_frag", "s_tech_polity", "s_frag_polity", "s_tech_frag_polity"])
        iv.extend(
            [
                IVStyle("s_tech_frag"),
                IVStyle("s_tech_polity"),
                IVStyle("s_frag_polity"),
                IVStyle("s_tech_frag_polity"),
            ]
        )

    if include_controls:
        regressors.extend(["econ_dev_index", "human_dev_index", "lpop"])
        iv.extend([IVStyle("econ_dev_index"), IVStyle("human_dev_index"), IVStyle("lpop")])

    return DynamicPanelSpec(
        name="aid_growth_techshare_three_way"
        if include_three_way
        else "aid_growth_techshare_baseline",
        dependent="growth_rate",
        regressors=regressors,
        gmm=[
            GMMStyle("growth_rate", 2, 3),
            GMMStyle("lPA", 2, 2),
            GMMStyle("s_techshare", 2, 2),
            GMMStyle("frag_index_orth", 2, 2),
            GMMStyle("polity2", 2, 2),
        ],
        iv=iv,
        time_dummies=True,
        system=system,
        collapse=True,
        transformation="fod",
        steps="twostep",
    )


def aid_growth_ta_decomposition_spec(
    *,
    include_controls: bool = True,
    include_three_way: bool = True,
    system: bool = True,
) -> DynamicPanelSpec:
    """Preset for TA/NTA decomposition in aid-growth System GMM."""

    regressors = [
        "L1.growth_rate",
        "lPA",
        "s_TA_frac",
        "s_NTA_frac",
        "frag_index_orth",
        "polity2",
    ]
    iv = []

    if include_three_way:
        regressors.extend(["s_ta_frag", "s_ta_polity", "s_frag_polity", "s_ta_frag_polity"])
        iv.extend(
            [
                IVStyle("s_ta_frag"),
                IVStyle("s_ta_polity"),
                IVStyle("s_frag_polity"),
                IVStyle("s_ta_frag_polity"),
            ]
        )

    if include_controls:
        regressors.extend(["econ_dev_index", "human_dev_index", "lpop"])
        iv.extend([IVStyle("econ_dev_index"), IVStyle("human_dev_index"), IVStyle("lpop")])

    return DynamicPanelSpec(
        name="aid_growth_ta_nta_decomposition_three_way"
        if include_three_way
        else "aid_growth_ta_nta_decomposition_baseline",
        dependent="growth_rate",
        regressors=regressors,
        gmm=[
            GMMStyle("growth_rate", 2, 3),
            GMMStyle("lPA", 2, 2),
            GMMStyle("s_TA_frac", 2, 2),
            GMMStyle("s_NTA_frac", 2, 2),
            GMMStyle("frag_index_orth", 2, 2),
            GMMStyle("polity2", 2, 2),
        ],
        iv=iv,
        time_dummies=True,
        system=system,
        collapse=True,
        transformation="fod",
        steps="twostep",
    )


def aid_growth_fe_techshare_spec(
    *,
    include_controls: bool = True,
    include_three_way: bool = True,
    entity_effects: bool = True,
    time_effects: bool = True,
) -> FixedEffectsSpec:
    """Preset for the user's main fixed-effects TechShare model."""

    regressors = ["lPA", "s_techshare", "frag_index_orth", "polity2"]
    if include_three_way:
        regressors.extend(["s_tech_frag", "s_tech_polity", "s_frag_polity", "s_tech_frag_polity"])
    if include_controls:
        regressors.extend(["econ_dev_index", "human_dev_index", "lpop"])

    return FixedEffectsSpec(
        name="aid_growth_fe_techshare_three_way"
        if include_three_way
        else "aid_growth_fe_techshare_baseline",
        dependent="growth_rate",
        regressors=regressors,
        entity_effects=entity_effects,
        time_effects=time_effects,
        covariance="clustered",
        cluster="entity",
    )


def aid_growth_fe_ta_decomposition_spec(
    *,
    include_controls: bool = True,
    include_three_way: bool = True,
    entity_effects: bool = True,
    time_effects: bool = True,
) -> FixedEffectsSpec:
    """Preset for the user's main fixed-effects TA/NTA decomposition model."""

    regressors = ["lPA", "s_TA_frac", "s_NTA_frac", "frag_index_orth", "polity2"]
    if include_three_way:
        regressors.extend(["s_ta_frag", "s_ta_polity", "s_frag_polity", "s_ta_frag_polity"])
    if include_controls:
        regressors.extend(["econ_dev_index", "human_dev_index", "lpop"])

    return FixedEffectsSpec(
        name="aid_growth_fe_ta_nta_decomposition_three_way"
        if include_three_way
        else "aid_growth_fe_ta_nta_decomposition_baseline",
        dependent="growth_rate",
        regressors=regressors,
        entity_effects=entity_effects,
        time_effects=time_effects,
        covariance="clustered",
        cluster="entity",
    )


def aid_growth_techshare_suite(
    *,
    include_controls: bool = True,
    include_three_way: bool = True,
    system: bool = True,
) -> PanelModelSuite:
    """Preset pairing FE main model with System/Difference GMM robustness model."""

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
