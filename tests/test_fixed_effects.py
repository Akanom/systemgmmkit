import numpy as np
import pandas as pd

from systemgmmkit import FixedEffectsSpec, run_fixed_effects_native
from systemgmmkit.presets import aid_growth_fe_techshare_spec, aid_growth_techshare_suite


def test_fixed_effects_native_recovers_simple_slope_with_entity_and_time_effects():
    rows = []
    for i in range(8):
        for t in range(5):
            x = i * 0.3 + t * 0.7 + ((i + t) % 3) * 0.2
            y = 2.5 * x + i * 1.1 + t * -0.4
            rows.append({"id": i, "t": t, "y": y, "x": x})
    df = pd.DataFrame(rows)
    spec = FixedEffectsSpec(dependent="y", regressors=["x"], entity_effects=True, time_effects=True)
    res = run_fixed_effects_native(spec, df, entity="id", time="t")
    assert np.isclose(res.params["x"], 2.5, atol=1e-8)
    assert res.nobs == len(df)
    assert res.backend == "native-lsdv"


def test_fe_preset_excludes_lagged_dependent_variable():
    spec = aid_growth_fe_techshare_spec()
    assert "L1.growth_rate" not in spec.regressors
    assert spec.entity_effects is True
    assert spec.time_effects is True


def test_suite_pairs_fe_with_dynamic_gmm():
    suite = aid_growth_techshare_suite()
    assert suite.fixed_effects.dependent == "growth_rate"
    assert suite.dynamic_gmm.system is True
