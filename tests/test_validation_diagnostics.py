import pandas as pd

from systemgmmkit import assess_diagnostics, validate_panel
from systemgmmkit.validation import estimate_instrument_pressure


def test_validate_panel_detects_basic_shape():
    df = pd.DataFrame(
        {
            "id": [1, 1, 1, 2, 2, 2],
            "t": [1, 2, 3, 1, 2, 3],
            "y": [1.0, 2.0, 3.0, 1.5, None, 2.5],
        }
    )
    report = validate_panel(df, entity="id", time="t", variables=["y"])
    assert report.n_obs == 6
    assert report.n_entities == 2
    assert report.balanced is True
    assert report.missing_by_variable["y"] == 1


def test_instrument_pressure_low_when_collapsed():
    out = estimate_instrument_pressure(
        n_entities=100,
        gmm_blocks=[(2, 3), (2, 2)],
        n_iv=3,
        n_time_dummies=13,
        system=True,
        collapse=True,
    )
    assert out["approx_instruments"] < 100
    assert out["risk"] in {"low", "moderate"}


def test_diagnostics_recommendation_flags_ar2_failure():
    report = assess_diagnostics(
        ar1_p=0.03, ar2_p=0.02, hansen_p=0.2, n_instruments=40, n_entities=90
    )
    assert "serial-correlation" in report.recommendation
