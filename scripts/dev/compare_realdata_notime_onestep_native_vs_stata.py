import math
from pathlib import Path

import pandas as pd

from systemgmmkit import build_system_gmm_spec, run_system_gmm

OUT = Path("artifacts/parity/gmm_lag_windows_realdata_notime")
DATA = Path("artifacts/parity/xtabond2/system_gmm_benchmark.csv")

df = pd.read_csv(DATA)

specs = {
    "m_base": build_system_gmm_spec(
        dependent="y",
        regressors=["x", "w"],
        endogenous=["x"],
        exogenous=["w"],
        time_dummies=False,
    ),
    "m_role": build_system_gmm_spec(
        dependent="y",
        regressors=["x", "w"],
        endogenous=["x"],
        predetermined=["w"],
        gmm_lags=(2, 4),
        gmm_lags_by_role={
            "endogenous": (2, 5),
            "predetermined": (1, 3),
        },
        time_dummies=False,
    ),
    "m_var": build_system_gmm_spec(
        dependent="y",
        regressors=["x", "w"],
        endogenous=["x"],
        predetermined=["w"],
        gmm_lags=(2, 4),
        gmm_lags_by_role={
            "endogenous": (2, 5),
            "predetermined": (1, 3),
        },
        gmm_lags_by_variable={
            "y": (2, 4),
            "x": (3, 5),
            "w": (1, 2),
        },
        time_dummies=False,
    ),
}

NAME_MAP = {
    "L.y": "L1.y",
    "_cons": "_con",
}


def as_dict(value):
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if hasattr(value, "to_dict"):
        return value.to_dict()
    return {}


def first_attr(obj, names):
    for name in names:
        if hasattr(obj, name):
            value = getattr(obj, name)
            if value is not None:
                return value
    return None


def native_params(result):
    params = as_dict(first_attr(result, ["params", "coefficients", "coef"]))
    ses = as_dict(first_attr(result, ["std_errors", "standard_errors", "stderr", "bse"]))

    rows = []
    for k, v in params.items():
        rows.append(
            {
                "param": str(k),
                "native_coef": v,
                "native_std_err": ses.get(k, math.nan),
            }
        )
    return pd.DataFrame(rows)


frames = []

for model, spec in specs.items():
    print(f"Running native forced one-step: {model}")
    res = run_system_gmm(spec, df, entity="id", time="t", backend="native")
    n = native_params(res)
    n.insert(0, "model", model)

    s_path = OUT / f"{model}_onestep_params.csv"
    if not s_path.exists():
        raise FileNotFoundError(f"Missing Stata one-step output: {s_path}")

    s = pd.read_csv(s_path)
    s["param"] = s["param"].replace(NAME_MAP)

    s = s.rename(columns={"coef": "stata_coef", "std_err": "stata_std_err"})[
        ["model", "param", "stata_coef", "stata_std_err"]
    ]

    merged = s.merge(n, on=["model", "param"], how="outer")
    merged["abs_coef_diff"] = (merged["native_coef"] - merged["stata_coef"]).abs()
    merged["abs_se_diff"] = (merged["native_std_err"] - merged["stata_std_err"]).abs()
    frames.append(merged)

out = pd.concat(frames, ignore_index=True)
out.to_csv(OUT / "native_vs_stata_onestep_coef_comparison.csv", index=False)

summary = (
    out.dropna(subset=["abs_coef_diff"])
    .groupby("model", as_index=False)
    .agg(
        max_abs_coef_diff=("abs_coef_diff", "max"),
        mean_abs_coef_diff=("abs_coef_diff", "mean"),
        max_abs_se_diff=("abs_se_diff", "max"),
        mean_abs_se_diff=("abs_se_diff", "mean"),
    )
)

print("\nOne-step coefficient comparison:")
print(out.to_string(index=False))

print("\nSummary:")
print(summary.to_string(index=False))
