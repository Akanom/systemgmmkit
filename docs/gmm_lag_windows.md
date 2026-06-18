# Role-Specific and Variable-Specific GMM Lag Windows

The dynamic GMM API supports three levels of GMM instrument lag-window control.

| Level | Argument | Meaning |
|---|---|---|
| Global | `gmm_lags=(2, 4)` | Default GMM instrument lag window |
| Role-specific | `gmm_lags_by_role={"endogenous": (2, 5), "predetermined": (1, 3)}` | Different windows for endogenous and predetermined variables |
| Variable-specific | `gmm_lags_by_variable={"investment": (3, 5), "cashflow": (1, 2)}` | Variable-level override |

Precedence:

```text
gmm_lags_by_variable > gmm_lags_by_role > gmm_lags
```

Example:

```python
spec = build_system_gmm_spec(
    dependent="y",
    regressors=[
        "L1_y",
        "investment",
        "L1_investment",
        "cashflow",
        "L1_cashflow",
        "firm_size",
    ],
    endogenous=[
        "L1_y",
        "investment",
        "L1_investment",
    ],
    predetermined=[
        "cashflow",
        "L1_cashflow",
    ],
    exogenous=[
        "firm_size",
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
```

Exogenous variables remain IV-style by default. Do not assign exogenous variables to `gmm_lags_by_role`.

If a lagged exogenous variable belongs in the structural equation, create it as a column first and include it in both `regressors` and `exogenous`.
