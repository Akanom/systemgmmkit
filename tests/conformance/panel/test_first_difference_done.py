from __future__ import annotations

import numpy as np
import pandas as pd


def test_first_difference_recovers_manual_solution():
    from systemgmmkit import first_difference

    df = pd.DataFrame(
        {
            "entity": [1, 1, 1, 2, 2, 2],
            "time": [1, 2, 3, 1, 2, 3],
            "y": [1.0, 3.0, 6.0, 2.0, 5.0, 9.0],
            "x": [1.0, 2.0, 4.0, 1.0, 3.0, 6.0],
        }
    )

    result = first_difference(
        data=df,
        y="y",
        x=["x"],
        entity="entity",
        time="time",
    )

    d = df.sort_values(["entity", "time"]).copy()
    d["dy"] = d.groupby("entity")["y"].diff()
    d["dx"] = d.groupby("entity")["x"].diff()
    d = d.dropna()

    beta = np.linalg.lstsq(d[["dx"]].to_numpy(), d["dy"].to_numpy(), rcond=None)[0][0]

    assert np.isclose(result.params["x"], beta)
    assert result.nobs == 4
