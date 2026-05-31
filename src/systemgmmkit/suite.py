from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from .fixed_effects import FixedEffectsResult, FixedEffectsSpec, run_fixed_effects
from .pydynpd_backend import run_pydynpd
from .spec import DynamicPanelSpec


@dataclass(frozen=True)
class PanelModelSuite:
    """Pair a static FE specification with a dynamic System/Difference GMM spec."""

    fixed_effects: FixedEffectsSpec
    dynamic_gmm: DynamicPanelSpec
    name: str = "panel_model_suite"


@dataclass(frozen=True)
class PanelModelSuiteResult:
    suite: PanelModelSuite
    fixed_effects_result: FixedEffectsResult | Any
    dynamic_gmm_result: Any | None
    notes: list[str]


def run_panel_model_suite(
    suite: PanelModelSuite,
    data: pd.DataFrame,
    *,
    entity: str,
    time: str,
    run_gmm: bool = True,
    gmm_panel_ids: list[str] | None = None,
) -> PanelModelSuiteResult:
    """Run FE first, then optionally run the configured GMM robustness model."""

    fe_res = run_fixed_effects(suite.fixed_effects, data, entity=entity, time=time)
    notes = ["Fixed effects estimated first and should be treated as the main static panel model."]
    gmm_res = None
    if run_gmm:
        panel_ids = gmm_panel_ids or [entity, time]
        gmm_res = run_pydynpd(suite.dynamic_gmm, data, panel_ids=panel_ids)
        notes.append("Dynamic GMM estimated as robustness/endogeneity check.")
    return PanelModelSuiteResult(
        suite=suite, fixed_effects_result=fe_res, dynamic_gmm_result=gmm_res, notes=notes
    )
