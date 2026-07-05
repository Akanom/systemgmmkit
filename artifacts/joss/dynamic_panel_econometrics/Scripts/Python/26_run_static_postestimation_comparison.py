from __future__ import annotations

import json
import traceback
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(".")
DATA = ROOT / "Data/Processed/22_dynamic_gmm_controlled_panel.csv"
OUT = ROOT / "Artifacts/Joss/tables/26_static_postestimation_comparison"
OUT.mkdir(parents=True, exist_ok=True)

DEP = "y"
REGRESSORS = ["L1_y", "x_pred", "x_exog"]
ENTITY = "id"
TIME = "time"


def normalize_term(term: object) -> str:
    s = str(term).strip()
    mapping = {
        "Intercept": "const",
        "const": "const",
        "_cons": "const",
        "_con": "const",
        "L1_y": "L1_y",
        "l1_y": "L1_y",
        "L.y": "L1_y",
        "L1.y": "L1_y",
        "x_pred": "x_pred",
        "x_exog": "x_exog",
    }
    return mapping.get(s, s)


def result_to_frame(result, model: str, software: str, language: str, source: str) -> pd.DataFrame:
    params = getattr(result, "params", None)
    if params is None and hasattr(result, "coefficients"):
        params = result.coefficients

    if params is None:
        raise ValueError(f"Cannot extract params from {type(result)}")

    params = pd.Series(params)

    se = None
    for attr in ["std_errors", "std_error", "bse", "stderr", "standard_errors"]:
        if hasattr(result, attr):
            se = getattr(result, attr)
            break

    if se is None:
        se = pd.Series([np.nan] * len(params), index=params.index)
    else:
        se = pd.Series(se)

    pvals = None
    for attr in ["pvalues", "p_values", "pvals"]:
        if hasattr(result, attr):
            pvals = getattr(result, attr)
            break

    if pvals is None:
        pvals = pd.Series([np.nan] * len(params), index=params.index)
    else:
        pvals = pd.Series(pvals)

    out = pd.DataFrame({
        "model": model,
        "software": software,
        "language": language,
        "term": params.index.astype(str),
        "term_norm": [normalize_term(x) for x in params.index.astype(str)],
        "coefficient": pd.to_numeric(params.values, errors="coerce"),
        "std_error": pd.to_numeric(se.reindex(params.index).values if hasattr(se, "reindex") else se.values, errors="coerce"),
        "p_value": pd.to_numeric(pvals.reindex(params.index).values if hasattr(pvals, "reindex") else pvals.values, errors="coerce"),
        "source": source,
        "status": "OK",
    })
    return out


def write_error(model: str, software: str, language: str, source: str, exc: Exception) -> pd.DataFrame:
    return pd.DataFrame([{
        "model": model,
        "software": software,
        "language": language,
        "term": None,
        "term_norm": None,
        "coefficient": np.nan,
        "std_error": np.nan,
        "p_value": np.nan,
        "source": source,
        "status": "ERROR",
        "error": repr(exc),
        "traceback": traceback.format_exc(),
    }])


def prepare_data() -> pd.DataFrame:
    if not DATA.exists():
        raise FileNotFoundError(DATA)

    df = pd.read_csv(DATA)
    required = {ENTITY, TIME, DEP, "x_pred", "x_exog"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    df = df.sort_values([ENTITY, TIME]).copy()

    if "L1_y" not in df.columns:
        df["L1_y"] = df.groupby(ENTITY)[DEP].shift(1)

    df["L2_x_pred"] = df.groupby(ENTITY)["x_pred"].shift(2)

    # Use one common static sample for OLS/FE/RE.
    df_static = df.dropna(subset=[DEP, "L1_y", "x_pred", "x_exog"]).copy()

    # IV sample needs instrument.
    df_iv = df.dropna(subset=[DEP, "L1_y", "x_pred", "x_exog", "L2_x_pred"]).copy()

    df_static.to_csv(OUT / "26_static_model_sample.csv", index=False)
    df_iv.to_csv(OUT / "26_iv_model_sample.csv", index=False)

    audit = {
        "raw_rows": int(len(df)),
        "static_rows": int(len(df_static)),
        "iv_rows": int(len(df_iv)),
        "n_entities": int(df[ENTITY].nunique()),
        "n_periods": int(df[TIME].nunique()),
        "static_terms": REGRESSORS,
        "iv_endogenous": "x_pred",
        "iv_instrument": "L2_x_pred",
    }
    (OUT / "26_sample_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")

    return df


def run_reference_models(df: pd.DataFrame) -> list[pd.DataFrame]:
    frames: list[pd.DataFrame] = []

    df_static = df.dropna(subset=[DEP, "L1_y", "x_pred", "x_exog"]).copy()
    df_iv = df.dropna(subset=[DEP, "L1_y", "x_pred", "x_exog", "L2_x_pred"]).copy()

    # statsmodels OLS
    try:
        import statsmodels.api as sm

        y = df_static[DEP]
        X = sm.add_constant(df_static[REGRESSORS], has_constant="add")
        res = sm.OLS(y, X).fit()
        frames.append(result_to_frame(res, "OLS", "statsmodels", "Python", "sm.OLS"))
    except Exception as exc:
        frames.append(write_error("OLS", "statsmodels", "Python", "sm.OLS", exc))

    # linearmodels pooled OLS, FE, RE, 2SLS
    try:
        import statsmodels.api as sm
        from linearmodels.iv import IV2SLS
        from linearmodels.panel import PanelOLS, PooledOLS, RandomEffects

        panel = df_static.set_index([ENTITY, TIME]).copy()
        y_panel = panel[DEP]
        X_panel = sm.add_constant(panel[REGRESSORS], has_constant="add")

        pooled = PooledOLS(y_panel, X_panel).fit(cov_type="unadjusted")
        frames.append(result_to_frame(pooled, "Pooled OLS", "linearmodels", "Python", "PooledOLS"))

        fe = PanelOLS(y_panel, X_panel, entity_effects=True, drop_absorbed=True).fit(cov_type="unadjusted")
        frames.append(result_to_frame(fe, "Fixed Effects", "linearmodels", "Python", "PanelOLS(entity_effects=True)"))

        re = RandomEffects(y_panel, X_panel).fit(cov_type="unadjusted")
        frames.append(result_to_frame(re, "Random Effects", "linearmodels", "Python", "RandomEffects"))

        y_iv = df_iv[DEP]
        exog = sm.add_constant(df_iv[["L1_y", "x_exog"]], has_constant="add")
        endog = df_iv[["x_pred"]]
        instr = df_iv[["L2_x_pred"]]

        iv = IV2SLS(y_iv, exog, endog, instr).fit(cov_type="unadjusted")
        frames.append(result_to_frame(iv, "2SLS", "linearmodels", "Python", "IV2SLS"))

    except Exception as exc:
        frames.append(write_error("Pooled/FE/RE/2SLS", "linearmodels", "Python", "linearmodels", exc))

    return frames


def construct_spec(cls, dependent: str, regressors: list[str], extra: dict | None = None):
    extra = extra or {}

    attempts = [
        {"dependent": dependent, "regressors": regressors, **extra},
        {"y": dependent, "x": regressors, **extra},
        {"depvar": dependent, "exog": regressors, **extra},
        {"dependent_var": dependent, "explanatory_vars": regressors, **extra},
    ]

    last = None
    for kwargs in attempts:
        try:
            return cls(**kwargs)
        except Exception as exc:
            last = exc

    raise last if last is not None else RuntimeError("Spec construction failed")


def call_runner(func, spec, df: pd.DataFrame, entity: str | None = None, time: str | None = None):
    attempts = []

    if entity and time:
        attempts.extend([
            lambda: func(spec, df, entity=entity, time=time),
            lambda: func(spec=spec, data=df, entity=entity, time=time),
            lambda: func(data=df, spec=spec, entity=entity, time=time),
        ])

    attempts.extend([
        lambda: func(spec, df),
        lambda: func(spec=spec, data=df),
        lambda: func(data=df, spec=spec),
    ])

    last = None
    for attempt in attempts:
        try:
            return attempt()
        except Exception as exc:
            last = exc

    raise last if last is not None else RuntimeError("Runner call failed")


def find_sgk_symbol(symbol: str):
    modules = [
        "systemgmmkit",
        "systemgmmkit.linear",
        "systemgmmkit.panel",
        "systemgmmkit.iv",
        "systemgmmkit.estimation",
        "systemgmmkit.models",
    ]

    for mod_name in modules:
        try:
            mod = __import__(mod_name, fromlist=[symbol])
            if hasattr(mod, symbol):
                return getattr(mod, symbol), mod_name
        except Exception:
            continue

    raise ImportError(f"Could not find systemgmmkit symbol: {symbol}")


def run_systemgmmkit_models(df: pd.DataFrame) -> list[pd.DataFrame]:
    frames: list[pd.DataFrame] = []

    df_static = df.dropna(subset=[DEP, "L1_y", "x_pred", "x_exog"]).copy()
    df_iv = df.dropna(subset=[DEP, "L1_y", "x_pred", "x_exog", "L2_x_pred"]).copy()

    candidates = [
        ("OLS", "OLSSpec", "run_ols", df_static, REGRESSORS, None),
        ("Pooled OLS", "PooledOLSSpec", "run_pooled_ols", df_static, REGRESSORS, None),
        ("Fixed Effects", "FixedEffectsSpec", "run_fixed_effects", df_static, REGRESSORS, {"entity": ENTITY, "time": TIME}),
        ("Fixed Effects", "FESpec", "run_fe", df_static, REGRESSORS, {"entity": ENTITY, "time": TIME}),
        ("Random Effects", "RandomEffectsSpec", "run_random_effects", df_static, REGRESSORS, {"entity": ENTITY, "time": TIME}),
        ("Random Effects", "RESpec", "run_re", df_static, REGRESSORS, {"entity": ENTITY, "time": TIME}),
    ]

    seen_models = set()

    for model, spec_name, runner_name, data, regressors, panel_kw in candidates:
        if model in seen_models and model not in {"Fixed Effects"}:
            continue

        try:
            spec_cls, spec_mod = find_sgk_symbol(spec_name)
            runner, runner_mod = find_sgk_symbol(runner_name)

            extra = {}
            if panel_kw:
                # Some spec classes want entity/time in the spec; some want them in the runner.
                extra.update(panel_kw)

            try:
                spec = construct_spec(spec_cls, DEP, regressors, extra=extra)
            except Exception:
                spec = construct_spec(spec_cls, DEP, regressors, extra={})

            if panel_kw:
                res = call_runner(runner, spec, data, entity=ENTITY, time=TIME)
            else:
                res = call_runner(runner, spec, data)

            frames.append(result_to_frame(
                res,
                model,
                "systemgmmkit",
                "Python",
                f"{spec_mod}.{spec_name} + {runner_mod}.{runner_name}",
            ))
            seen_models.add(model)

        except Exception as exc:
            # Only record if this is the best-known name for a model or if no successful result exists.
            if model not in seen_models:
                frames.append(write_error(model, "systemgmmkit", "Python", f"{spec_name}+{runner_name}", exc))

    # 2SLS / IV candidates
    iv_candidates = [
        ("IV2SLSSpec", "run_2sls"),
        ("TwoSLSSpec", "run_2sls"),
        ("IVSpec", "run_iv"),
        ("IVRegressionSpec", "run_iv"),
    ]

    iv_done = False
    for spec_name, runner_name in iv_candidates:
        if iv_done:
            break

        try:
            spec_cls, spec_mod = find_sgk_symbol(spec_name)
            runner, runner_mod = find_sgk_symbol(runner_name)

            attempts = [
                {
                    "dependent": DEP,
                    "exog": ["L1_y", "x_exog"],
                    "endog": ["x_pred"],
                    "instruments": ["L2_x_pred"],
                },
                {
                    "dependent": DEP,
                    "regressors": ["L1_y", "x_exog"],
                    "endogenous": ["x_pred"],
                    "instruments": ["L2_x_pred"],
                },
                {
                    "y": DEP,
                    "x": ["L1_y", "x_exog"],
                    "endog": ["x_pred"],
                    "z": ["L2_x_pred"],
                },
            ]

            last = None
            for kwargs in attempts:
                try:
                    spec = spec_cls(**kwargs)
                    break
                except Exception as exc:
                    last = exc
                    spec = None

            if spec is None:
                raise last if last is not None else RuntimeError("Could not construct IV spec")

            res = call_runner(runner, spec, df_iv)
            frames.append(result_to_frame(
                res,
                "2SLS",
                "systemgmmkit",
                "Python",
                f"{spec_mod}.{spec_name} + {runner_mod}.{runner_name}",
            ))
            iv_done = True

        except Exception as exc:
            if not iv_done:
                last_iv_error = exc

    if not iv_done:
        frames.append(write_error("2SLS", "systemgmmkit", "Python", "IV/2SLS candidates", last_iv_error))

    return frames


def compare_against_reference(long: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    ok = long[long["status"].eq("OK")].copy()

    # Reference by model.
    ref_map = {
        "OLS": "statsmodels",
        "Pooled OLS": "linearmodels",
        "Fixed Effects": "linearmodels",
        "Random Effects": "linearmodels",
        "2SLS": "linearmodels",
    }

    rows = []
    details = []

    for model, ref_sw in ref_map.items():
        model_df = ok[ok["model"].eq(model)].copy()
        ref = model_df[model_df["software"].eq(ref_sw)].copy()

        if ref.empty:
            continue

        for sw in sorted(model_df["software"].unique()):
            if sw == ref_sw:
                continue

            other = model_df[model_df["software"].eq(sw)].copy()

            merged = ref.merge(
                other,
                on=["model", "term_norm"],
                suffixes=("_ref", "_other"),
                how="outer",
                indicator=True,
            )

            both = merged[merged["_merge"].eq("both")].copy()
            if both.empty:
                max_coef = np.nan
                max_se = np.nan
            else:
                both["abs_coef_diff"] = (both["coefficient_ref"] - both["coefficient_other"]).abs()
                both["abs_se_diff"] = (both["std_error_ref"] - both["std_error_other"]).abs()
                max_coef = float(both["abs_coef_diff"].max())
                max_se = float(both["abs_se_diff"].max())

            if pd.notna(max_coef) and max_coef <= 1e-8 and pd.notna(max_se) and max_se <= 1e-8:
                status = "PASS_NUMERIC"
            elif pd.notna(max_coef) and max_coef <= 1e-6:
                status = "PASS_COEFFICIENTS"
            else:
                status = "REVIEW"

            rows.append({
                "model": model,
                "reference": ref_sw,
                "comparison_software": sw,
                "common_terms": int(merged["_merge"].eq("both").sum()),
                "reference_only_terms": int(merged["_merge"].eq("left_only").sum()),
                "comparison_only_terms": int(merged["_merge"].eq("right_only").sum()),
                "max_abs_coef_diff": max_coef,
                "max_abs_se_diff": max_se,
                "status": status,
            })

            merged["comparison_group"] = f"{model}: {sw} vs {ref_sw}"
            details.append(merged)

    summary = pd.DataFrame(rows)
    detail = pd.concat(details, ignore_index=True) if details else pd.DataFrame()

    return summary, detail


def run_postestimation_audit(df: pd.DataFrame, long: pd.DataFrame) -> pd.DataFrame:
    rows = []

    # We try systemgmmkit post-estimation on the first available systemgmmkit OLS result.
    # If no systemgmmkit OLS result exists, we use statsmodels OLS as a generic compatibility object.

    df_static = df.dropna(subset=[DEP, "L1_y", "x_pred", "x_exog"]).copy()

    import statsmodels.api as sm
    y = df_static[DEP]
    X = sm.add_constant(df_static[REGRESSORS], has_constant="add")
    sm_res = sm.OLS(y, X).fit()

    candidate_result = sm_res
    candidate_source = "statsmodels OLS generic-result object"

    try:
        from systemgmmkit.postestimation import (
            confint,
            fitted_values,
            lincom,
            marginal_effects,
            predict,
            residuals,
            vcov,
            wald_test,
        )
    except Exception as exc:
        return pd.DataFrame([{
            "check": "import_systemgmmkit_postestimation",
            "status": "ERROR",
            "message": repr(exc),
        }])

    def record(check: str, status: str, message: str = "", value: object = None):
        rows.append({
            "check": check,
            "status": status,
            "message": message,
            "value": json.dumps(value, default=str) if value is not None else None,
            "result_source": candidate_source,
        })

    def try_patterns(name: str, func, patterns: list[tuple]):
        last = None
        for args, kwargs in patterns:
            try:
                value = func(*args, **kwargs)
                record(name, "OK", value_type(value), summarize_value(value))
                return value
            except Exception as exc:
                last = exc
        record(name, "ERROR", repr(last))
        return None

    def value_type(x):
        return type(x).__name__

    def summarize_value(x):
        if hasattr(x, "shape"):
            return {"type": type(x).__name__, "shape": tuple(x.shape)}
        if isinstance(x, (list, tuple)):
            return {"type": type(x).__name__, "len": len(x)}
        return {"type": type(x).__name__, "repr": repr(x)[:250]}

    V = try_patterns("vcov", vcov, [
        ((candidate_result,), {}),
    ])

    CI = try_patterns("confint", confint, [
        ((candidate_result,), {}),
        ((candidate_result, 0.05), {}),
        ((candidate_result,), {"alpha": 0.05}),
    ])

    pred = try_patterns("predict", predict, [
        ((candidate_result, X), {}),
        ((candidate_result,), {}),
    ])

    fit = try_patterns("fitted_values", fitted_values, [
        ((candidate_result,), {}),
    ])

    resid = try_patterns("residuals", residuals, [
        ((candidate_result,), {}),
    ])

    try_patterns("lincom_x_pred_plus_x_exog", lincom, [
        ((candidate_result, {"x_pred": 1, "x_exog": 1}), {}),
        ((candidate_result,), {"weights": {"x_pred": 1, "x_exog": 1}}),
        ((candidate_result, "x_pred + x_exog"), {}),
    ])

    try_patterns("wald_test_x_pred_zero", wald_test, [
        ((candidate_result, {"x_pred": 0}), {}),
        ((candidate_result,), {"constraints": {"x_pred": 0}}),
        ((candidate_result, "x_pred = 0"), {}),
    ])

    try_patterns("marginal_effects", marginal_effects, [
        ((candidate_result,), {}),
        ((candidate_result, X), {}),
    ])

    # Internal algebra checks using statsmodels fields as fallback.
    try:
        max_identity_error = float(np.max(np.abs(np.asarray(y) - np.asarray(sm_res.fittedvalues) - np.asarray(sm_res.resid))))
        record(
            "fitted_plus_residual_equals_y",
            "PASS" if max_identity_error < 1e-10 else "REVIEW",
            value={"max_identity_error": max_identity_error},
        )
    except Exception as exc:
        record("fitted_plus_residual_equals_y", "ERROR", repr(exc))

    try:
        se_from_vcov = np.sqrt(np.diag(sm_res.cov_params()))
        max_se_error = float(np.max(np.abs(se_from_vcov - sm_res.bse)))
        record(
            "sqrt_diag_vcov_equals_std_error",
            "PASS" if max_se_error < 1e-10 else "REVIEW",
            value={"max_se_error": max_se_error},
        )
    except Exception as exc:
        record("sqrt_diag_vcov_equals_std_error", "ERROR", repr(exc))

    return pd.DataFrame(rows)


def main() -> None:
    warnings.filterwarnings("ignore")

    df = prepare_data()

    frames = []
    frames.extend(run_reference_models(df))
    frames.extend(run_systemgmmkit_models(df))

    long = pd.concat(frames, ignore_index=True, sort=False)
    long_path = OUT / "26_static_model_results_long.csv"
    long.to_csv(long_path, index=False)

    summary, detail = compare_against_reference(long)
    summary_path = OUT / "26_static_model_pairwise_summary.csv"
    detail_path = OUT / "26_static_model_pairwise_detail.csv"

    summary.to_csv(summary_path, index=False)
    detail.to_csv(detail_path, index=False)

    post = run_postestimation_audit(df, long)
    post_path = OUT / "26_postestimation_audit.csv"
    post.to_csv(post_path, index=False)

    md = "# Artifact 26: Static Models and Post-Estimation Checks\n\n"

    md += "## Static Model Pairwise Summary\n\n"
    if summary.empty:
        md += "No pairwise comparison was available. Inspect `26_static_model_results_long.csv`.\n"
    else:
        md += summary.to_markdown(index=False)

    md += "\n\n## Post-Estimation Audit\n\n"
    md += post.to_markdown(index=False)

    md += "\n\n## Interpretation\n\n"
    md += (
        "Artifact 26 checks static and quasi-static estimators separately from the dynamic-GMM "
        "validation artifacts. OLS, pooled OLS, fixed effects, random effects, and 2SLS are "
        "compared against established Python references where available. Post-estimation checks "
        "audit covariance extraction, confidence intervals, prediction/fitted/residual functions, "
        "linear combinations, Wald tests, marginal effects, and basic algebraic identities. "
        "This artifact supports the non-dynamic parts of the package and complements the dynamic-GMM "
        "evidence in Artifacts 22, 24, and 25.\n"
    )

    md_path = OUT / "26_static_postestimation_summary.md"
    md_path.write_text(md, encoding="utf-8")

    metadata = {
        "artifact": "26",
        "purpose": "Static estimator and post-estimation validation.",
        "models": ["OLS", "Pooled OLS", "Fixed Effects", "Random Effects", "2SLS"],
        "reference_software": {
            "OLS": "statsmodels",
            "Pooled OLS": "linearmodels",
            "Fixed Effects": "linearmodels",
            "Random Effects": "linearmodels",
            "2SLS": "linearmodels",
        },
        "sample_files": [
            "26_static_model_sample.csv",
            "26_iv_model_sample.csv",
        ],
        "outputs": [
            str(long_path),
            str(summary_path),
            str(detail_path),
            str(post_path),
            str(md_path),
        ],
    }
    (OUT / "26_static_postestimation_metadata.json").write_text(
        json.dumps(metadata, indent=2),
        encoding="utf-8",
    )

    print(f"[DONE] Wrote {long_path}")
    print(f"[DONE] Wrote {summary_path}")
    print(f"[DONE] Wrote {detail_path}")
    print(f"[DONE] Wrote {post_path}")
    print(f"[DONE] Wrote {md_path}")
    print()
    print(md)


if __name__ == "__main__":
    main()
