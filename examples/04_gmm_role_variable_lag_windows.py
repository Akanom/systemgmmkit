from __future__ import annotations

import pandas as pd

from systemgmmkit import build_system_gmm_spec

df = pd.DataFrame(
    {
        "firm_id": [1, 1, 1, 1, 2, 2, 2, 2],
        "year": [2020, 2021, 2022, 2023, 2020, 2021, 2022, 2023],
        "y": [1.0, 1.2, 1.3, 1.5, 0.8, 0.9, 1.0, 1.1],
        "investment": [10, 11, 13, 12, 8, 9, 10, 11],
        "cashflow": [4, 5, 5, 6, 3, 3, 4, 5],
        "firm_size": [100, 101, 102, 103, 80, 81, 82, 83],
    }
)

df = df.sort_values(["firm_id", "year"]).copy()

df["L1_y"] = df.groupby("firm_id")["y"].shift(1)
df["L1_investment"] = df.groupby("firm_id")["investment"].shift(1)
df["L1_cashflow"] = df.groupby("firm_id")["cashflow"].shift(1)
df["L1_firm_size"] = df.groupby("firm_id")["firm_size"].shift(1)

df = df.dropna(
    subset=[
        "L1_y",
        "L1_investment",
        "L1_cashflow",
        "L1_firm_size",
    ]
)

spec = build_system_gmm_spec(
    dependent="y",
    regressors=[
        "L1_y",
        "investment",
        "L1_investment",
        "cashflow",
        "L1_cashflow",
        "firm_size",
        "L1_firm_size",
    ],
    endogenous=[
        "investment",
        "L1_investment",
    ],
    predetermined=[
        "cashflow",
        "L1_cashflow",
    ],
    exogenous=[
        "firm_size",
        "L1_firm_size",
    ],
    gmm_lags=(2, 4),
    gmm_lags_by_role={
        "endogenous": (2, 5),
        "predetermined": (1, 3),
    },
    gmm_lags_by_variable={
        "investment": (3, 5),
        "cashflow": (1, 2),
    },
    collapse=True,
    windmeijer=True,
)

print(spec)
