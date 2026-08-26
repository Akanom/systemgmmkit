from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from systemgmmkit import format_inference_frame


def test_format_inference_frame_uses_t_statistic_and_fixed_p_value() -> None:
    raw = pd.DataFrame(
        {
            "name": ["investment_minus_leverage"],
            "estimate": [1.1516],
            "std_error": [0.1194],
            "statistic": [9.6428],
            "z": [np.nan],
            "t": [9.6428],
            "p_value": [0.0],
            "ci_low": [0.9165],
            "ci_high": [1.3866],
            "value": [0.0],
            "alpha": [0.05],
            "df": [295.0],
            "df_resid": [295.0],
            "distribution": ["t"],
        }
    )
    original = raw.copy(deep=True)

    displayed = format_inference_frame(raw)

    assert displayed.columns.tolist() == [
        "name",
        "estimate",
        "std_error",
        "t",
        "p_value",
        "ci_low",
        "ci_high",
        "df",
    ]
    assert displayed.loc[0, "p_value"] == "0.0000"
    pd.testing.assert_frame_equal(raw, original)


def test_format_inference_frame_validates_digits() -> None:
    with pytest.raises(ValueError, match="at least 1"):
        format_inference_frame(pd.DataFrame(), digits=0)


def test_format_inference_frame_keeps_trailing_p_value_zeroes() -> None:
    displayed = format_inference_frame(
        pd.DataFrame({"p_value": [0.0, 0.125, np.nan]}),
    )

    assert displayed["p_value"].tolist() == ["0.0000", "0.1250", ""]
