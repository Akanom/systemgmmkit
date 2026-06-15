from __future__ import annotations

import pandas as pd

from systemgmmkit import first_difference, result_to_frame


def test_first_difference_result_exposes_summary_frame_for_reporting():
    data = pd.DataFrame(
        {
            "id": [1, 1, 1, 1, 2, 2, 2, 2],
            "t": [1, 2, 3, 4, 1, 2, 3, 4],
            "y": [1.0, 1.4, 1.9, 2.7, 0.8, 1.1, 1.5, 2.0],
            "x": [0.2, 0.4, 0.7, 1.0, 0.1, 0.3, 0.5, 0.9],
        }
    )

    result = first_difference(
        data,
        y="y",
        x=["x"],
        entity="id",
        time="t",
    )

    frame = result.summary_frame()

    assert not frame.empty
    assert {"coef", "std_err", "statistic", "p_value"}.issubset(frame.columns)
    assert frame.index[0] == "x"


def test_result_to_frame_accepts_first_difference_result():
    data = pd.DataFrame(
        {
            "id": [1, 1, 1, 1, 2, 2, 2, 2],
            "t": [1, 2, 3, 4, 1, 2, 3, 4],
            "y": [1.0, 1.4, 1.9, 2.7, 0.8, 1.1, 1.5, 2.0],
            "x": [0.2, 0.4, 0.7, 1.0, 0.1, 0.3, 0.5, 0.9],
        }
    )

    result = first_difference(
        data,
        y="y",
        x=["x"],
        entity="id",
        time="t",
    )

    frame = result_to_frame(result, model_name="FD")

    assert not frame.empty
    assert "model" in frame.columns
    assert frame["model"].iloc[0] == "FD"
