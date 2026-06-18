from pathlib import Path
import math
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

def first_attr(obj, names):
    for name in names:
        if hasattr(obj, name):
            value = getattr(obj, name)
            if value is not None:
                return value
    return None

def as_dict(value):
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if hasattr(value, "to_dict"):
        return value.to_dict()
    return {}

def extract_params(result):
    params = as_dict(first_attr(result, ["params", "coefficients", "coef"]))
    ses = as_dict(first_attr(result, ["std_errors", "standard_errors", "stderr", "bse"]))

    if not params:
        raise RuntimeError(f"Could not extract params from {type(result)}")

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

def extract_diag(model, result):
    diag = as_dict(getattr(result, "diagnostics", None))

    def pick(*names):
        for name in names:
            if name in diag and diag[name] is not None:
                return diag[name]
            if hasattr(result, name):
                value = getattr(result, name)
                if value is not None:
                    return value
        return math.nan

    return {
        "model": model,
        "native_nobs": pick("nobs", "n_obs", "N"),
        "native_n_groups": pick("n_groups", "groups", "N_g"),
        "native_n_instruments": pick("n_instruments", "k_instruments", "j"),
        "native_hansen_p": pick("hansen_p", "hansenp"),
        "native_sargan_p": pick("sargan_p", "sarganp"),
        "native_ar1_p": pick("ar1_p", "ar1p"),
        "native_ar2_p": pick("ar2_p", "ar2p"),
    }

native_params = []
native_diags = []

for model, spec in specs.items():
    print(f"Running native: {model}")
    res = run_system_gmm(spec, df, entity="id", time="t", backend="native")

    p = extract_params(res)
    p.insert(0, "model", model)
    native_params.append(p)

    native_diags.append(extract_diag(model, res))

native_params = pd.concat(native_params, ignore_index=True)
native_diags = pd.DataFrame(native_diags)

native_params.to_csv(OUT / "native_params.csv", index=False)
native_diags.to_csv(OUT / "native_diagnostics.csv", index=False)

coef_frames = []
diag_frames = []

for model in specs:
    stata_p = pd.read_csv(OUT / f"{model}_params.csv")
    stata_p["param"] = stata_p["param"].replace(NAME_MAP)

    stata_clean = stata_p.rename(
        columns={
            "coef": "stata_coef",
            "std_err": "stata_std_err",
        }
    )[["model", "param", "stata_coef", "stata_std_err"]]

    native_clean = native_params[native_params["model"] == model]

    merged = stata_clean.merge(native_clean, on=["model", "param"], how="outer")
    merged["abs_coef_diff"] = (merged["native_coef"] - merged["stata_coef"]).abs()
    merged["abs_se_diff"] = (merged["native_std_err"] - merged["stata_std_err"]).abs()
    coef_frames.append(merged)

    stata_d = pd.read_csv(OUT / f"{model}_diagnostics.csv").rename(
        columns={
            "N": "stata_nobs",
            "N_g": "stata_n_groups",
            "k_instruments": "stata_n_instruments",
            "hansen_p": "stata_hansen_p",
            "sargan_p": "stata_sargan_p",
            "ar1_p": "stata_ar1_p",
            "ar2_p": "stata_ar2_p",
        }
    )

    nd = native_diags[native_diags["model"] == model]

    dm = stata_d.merge(nd, on="model", how="outer")

    for a, b, c in [
        ("native_nobs", "stata_nobs", "abs_nobs_diff"),
        ("native_n_groups", "stata_n_groups", "abs_groups_diff"),
        ("native_n_instruments", "stata_n_instruments", "abs_instruments_diff"),
        ("native_hansen_p", "stata_hansen_p", "abs_hansen_p_diff"),
        ("native_sargan_p", "stata_sargan_p", "abs_sargan_p_diff"),
        ("native_ar1_p", "stata_ar1_p", "abs_ar1_p_diff"),
        ("native_ar2_p", "stata_ar2_p", "abs_ar2_p_diff"),
    ]:
        dm[c] = (pd.to_numeric(dm[a], errors="coerce") - pd.to_numeric(dm[b], errors="coerce")).abs()

    diag_frames.append(dm)

coef = pd.concat(coef_frames, ignore_index=True)
diag = pd.concat(diag_frames, ignore_index=True)

coef.to_csv(OUT / "native_vs_stata_coef_comparison.csv", index=False)
diag.to_csv(OUT / "native_vs_stata_diagnostics_comparison.csv", index=False)

print("\nDiagnostics comparison:")
print(diag.to_string(index=False))

print("\nCoefficient comparison:")
print(coef.to_string(index=False))
