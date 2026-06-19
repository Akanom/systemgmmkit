from __future__ import annotations

import math
from pathlib import Path

import pandas as pd

from systemgmmkit import build_system_gmm_spec, run_system_gmm

OUT = Path("artifacts/parity/gmm_lag_windows_realdata")
DATA = Path("artifacts/parity/xtabond2/system_gmm_benchmark.csv")

df = pd.read_csv(DATA)

specs = {
    "m_base": build_system_gmm_spec(
        dependent="y",
        regressors=["x", "w"],
        endogenous=["x"],
        exogenous=["w"],
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
    ),
}


def _get_attr(obj, names, default=None):
    for name in names:
        if hasattr(obj, name):
            value = getattr(obj, name)
            if value is not None:
                return value
    return default


def _to_dict_like(value):
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if hasattr(value, "to_dict"):
        return value.to_dict()
    return {}


def extract_params(result):
    # Preferred: summary/table-like output
    for attr in ["summary_frame", "parameter_table", "params_table", "coefficients_table", "table"]:
        value = _get_attr(result, [attr])
        if value is not None:
            if callable(value):
                value = value()
            try:
                frame = pd.DataFrame(value)
                if not frame.empty:
                    cols = {c.lower(): c for c in frame.columns}
                    term_col = (
                        cols.get("param")
                        or cols.get("term")
                        or cols.get("variable")
                        or cols.get("name")
                    )
                    coef_col = (
                        cols.get("coef")
                        or cols.get("coefficient")
                        or cols.get("estimate")
                        or cols.get("params")
                    )
                    se_col = (
                        cols.get("std_err")
                        or cols.get("stderr")
                        or cols.get("std_error")
                        or cols.get("standard_error")
                    )
                    if term_col and coef_col:
                        out = pd.DataFrame(
                            {
                                "param": frame[term_col].astype(str),
                                "native_coef": pd.to_numeric(frame[coef_col], errors="coerce"),
                            }
                        )
                        if se_col:
                            out["native_std_err"] = pd.to_numeric(frame[se_col], errors="coerce")
                        else:
                            out["native_std_err"] = math.nan
                        return out
            except Exception:
                pass

    params = _to_dict_like(_get_attr(result, ["params", "coefficients", "coef"]))
    ses = _to_dict_like(_get_attr(result, ["std_errors", "standard_errors", "stderr", "bse"]))

    if not params:
        raise RuntimeError(
            "Could not extract native parameters. "
            f"Result type={type(result)!r}; attrs={dir(result)}"
        )

    rows = []
    for key, coef in params.items():
        rows.append(
            {
                "param": str(key),
                "native_coef": coef,
                "native_std_err": ses.get(key, math.nan),
            }
        )

    return pd.DataFrame(rows)


def extract_diagnostics(model, result):
    diagnostics = _to_dict_like(_get_attr(result, ["diagnostics", "diag"]))

    def pick(*names):
        for name in names:
            if name in diagnostics and diagnostics[name] is not None:
                return diagnostics[name]
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


native_param_frames = []
native_diag_rows = []

for model, spec in specs.items():
    print(f"Running native System GMM: {model}")

    try:
        result = run_system_gmm(spec, df, entity="id", time="t", backend="native")
    except Exception as exc:
        print(f"backend='native' failed for {model}: {exc!r}")
        print("Retrying with backend='auto'")
        result = run_system_gmm(spec, df, entity="id", time="t", backend="auto")

    param_frame = extract_params(result)
    param_frame.insert(0, "model", model)
    native_param_frames.append(param_frame)

    native_diag_rows.append(extract_diagnostics(model, result))

    introspection_path = OUT / f"{model}_native_result_introspection.txt"
    introspection_path.write_text(
        f"type:\n{type(result)!r}\n\nattrs:\n" + "\n".join(dir(result)),
        encoding="utf-8",
    )

native_params = pd.concat(native_param_frames, ignore_index=True)
native_diags = pd.DataFrame(native_diag_rows)

native_params.to_csv(OUT / "native_lag_window_params.csv", index=False)
native_diags.to_csv(OUT / "native_lag_window_diagnostics.csv", index=False)

# Compare Stata params if available.
coef_comparisons = []

for model in specs:
    stata_path = OUT / f"{model}_params.csv"
    if not stata_path.exists():
        print(f"Missing Stata params file: {stata_path}")
        continue

    stata = pd.read_csv(stata_path)
    native = native_params[native_params["model"] == model].copy()

    stata_cols = {c.lower(): c for c in stata.columns}
    param_col = stata_cols.get("param")
    coef_col = stata_cols.get("coef")
    se_col = stata_cols.get("std_err")

    if not param_col or not coef_col:
        print(f"Skipping malformed Stata params file: {stata_path}")
        continue

    stata_clean = pd.DataFrame(
        {
            "model": model,
            "param": stata[param_col].astype(str),
            "stata_coef": pd.to_numeric(stata[coef_col], errors="coerce"),
            "stata_std_err": pd.to_numeric(stata[se_col], errors="coerce") if se_col else math.nan,
        }
    )

    merged = stata_clean.merge(native, on=["model", "param"], how="outer")
    merged["abs_coef_diff"] = (merged["native_coef"] - merged["stata_coef"]).abs()
    merged["abs_se_diff"] = (merged["native_std_err"] - merged["stata_std_err"]).abs()
    coef_comparisons.append(merged)

if coef_comparisons:
    coef_comparison = pd.concat(coef_comparisons, ignore_index=True)
    coef_comparison.to_csv(OUT / "native_vs_stata_lag_window_coef_comparison.csv", index=False)

# Compare diagnostics.
diag_comparisons = []

for model in specs:
    stata_diag_path = OUT / f"{model}_diagnostics.csv"
    if not stata_diag_path.exists():
        continue

    stata_diag = pd.read_csv(stata_diag_path)
    native_diag = native_diags[native_diags["model"] == model].copy()

    merged = stata_diag.merge(native_diag, on="model", how="outer")

    rename_map = {
        "N": "stata_nobs",
        "N_g": "stata_n_groups",
        "k_instruments": "stata_n_instruments",
        "hansen_p": "stata_hansen_p",
        "sargan_p": "stata_sargan_p",
        "ar1_p": "stata_ar1_p",
        "ar2_p": "stata_ar2_p",
    }
    merged = merged.rename(columns=rename_map)

    for left, right, out_col in [
        ("native_nobs", "stata_nobs", "abs_nobs_diff"),
        ("native_n_groups", "stata_n_groups", "abs_groups_diff"),
        ("native_n_instruments", "stata_n_instruments", "abs_instruments_diff"),
        ("native_hansen_p", "stata_hansen_p", "abs_hansen_p_diff"),
        ("native_sargan_p", "stata_sargan_p", "abs_sargan_p_diff"),
        ("native_ar1_p", "stata_ar1_p", "abs_ar1_p_diff"),
        ("native_ar2_p", "stata_ar2_p", "abs_ar2_p_diff"),
    ]:
        if left in merged.columns and right in merged.columns:
            merged[out_col] = (
                pd.to_numeric(merged[left], errors="coerce")
                - pd.to_numeric(merged[right], errors="coerce")
            ).abs()

    diag_comparisons.append(merged)

if diag_comparisons:
    diag_comparison = pd.concat(diag_comparisons, ignore_index=True)
    diag_comparison.to_csv(
        OUT / "native_vs_stata_lag_window_diagnostics_comparison.csv", index=False
    )

print("\nWrote native outputs and comparisons to:")
print(OUT)
print("\nNative diagnostics:")
print(native_diags.to_string(index=False))
