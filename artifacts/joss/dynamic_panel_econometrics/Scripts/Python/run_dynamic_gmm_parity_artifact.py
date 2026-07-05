from __future__ import annotations

import json
import math
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from universal_output_hub import from_coefficient_table, outreg

import systemgmmkit as sgk

DATA_DIR = Path("Data/Processed")
RESULTS_DIR = Path("Results/systemgmmkit/dynamic_gmm_parity")
UOH_DIR = Path("Results/systemgmmkit/universal_output")
ARTIFACT_DIR = Path("Artifacts/Joss/tables")
STATA_DIR = Path("Scripts/Stata")

for p in [DATA_DIR, RESULTS_DIR, UOH_DIR, ARTIFACT_DIR, STATA_DIR]:
    p.mkdir(parents=True, exist_ok=True)


ENTITY = "id"
TIME = "time"
Y = "y"

CONTROLLED_DATA = DATA_DIR / "22_dynamic_gmm_controlled_panel.csv"

MODEL_LABELS = {
    "const": "Constant",
    "_con": "Constant",
    "L1_y": "Lagged dependent variable",
    "L.y": "Lagged dependent variable",
    "x_pred": "Predetermined regressor",
    "x_exog": "Exogenous regressor",
}


def normal_pvalue(z: float) -> float:
    if z is None or np.isnan(z):
        return np.nan
    return math.erfc(abs(float(z)) / math.sqrt(2.0))


def dataclass_or_object_to_dict(obj: Any) -> dict[str, Any]:
    if obj is None:
        return {}

    if is_dataclass(obj):
        return asdict(obj)

    if isinstance(obj, dict):
        return obj

    out: dict[str, Any] = {}

    for name in dir(obj):
        if name.startswith("_"):
            continue
        try:
            value = getattr(obj, name)
        except Exception:
            continue
        if callable(value):
            continue
        if isinstance(value, (str, int, float, bool, type(None))):
            out[name] = value

    return out


def generate_controlled_panel(
    n_units: int = 120,
    n_periods: int = 10,
    seed: int = 20260705,
) -> pd.DataFrame:
    """
    Balanced controlled panel for Dynamic GMM validation.

    DGP:
        y_it = rho*y_i,t-1 + beta_pred*x_pred_it + beta_exog*x_exog_it
               + alpha_i + tau_t + eps_it

    x_pred is predetermined because it is correlated with the previous-period
    shock, not the current-period shock.
    """
    rng = np.random.default_rng(seed)

    rows = []

    rho = 0.55
    beta_pred = 0.35
    beta_exog = 0.25

    for i in range(1, n_units + 1):
        alpha_i = rng.normal(0.0, 0.8)
        y_lag = rng.normal(0.0, 1.0)
        x_pred_lag = rng.normal(0.0, 1.0)
        eps_lag = rng.normal(0.0, 0.4)

        for t in range(1, n_periods + 1):
            tau_t = 0.03 * t
            eps = rng.normal(0.0, 0.5)
            x_exog = rng.normal(0.0, 1.0)

            # Predetermined: depends on previous shock, not current shock.
            x_pred = 0.45 * x_pred_lag + 0.35 * eps_lag + rng.normal(0.0, 0.8)

            y = rho * y_lag + beta_pred * x_pred + beta_exog * x_exog + alpha_i + tau_t + eps

            rows.append(
                {
                    ENTITY: i,
                    TIME: t,
                    Y: y,
                    "x_pred": x_pred,
                    "x_exog": x_exog,
                    "alpha_true": alpha_i,
                    "eps_true": eps,
                }
            )

            y_lag = y
            x_pred_lag = x_pred
            eps_lag = eps

    df = pd.DataFrame(rows)
    df = df.sort_values([ENTITY, TIME]).reset_index(drop=True)

    df["L1_y"] = df.groupby(ENTITY)[Y].shift(1)

    return df


def write_data_artifacts(df: pd.DataFrame) -> None:
    df.to_csv(CONTROLLED_DATA, index=False)

    summary = {
        "dataset": "Controlled synthetic dynamic panel",
        "purpose": "Formal Difference/System GMM smoke and parity reference artifact",
        "rows": int(len(df)),
        "n_units": int(df[ENTITY].nunique()),
        "n_periods": int(df[TIME].nunique()),
        "balanced": bool(df.groupby(ENTITY)[TIME].nunique().nunique() == 1),
        "entity": ENTITY,
        "time": TIME,
        "dependent": Y,
        "dgp": "y_it = 0.55*y_i,t-1 + 0.35*x_pred_it + 0.25*x_exog_it + alpha_i + tau_t + eps_it",
        "roles": {
            "lagged_dependent": "endogenous, GMM-style lags 2:3",
            "x_pred": "predetermined, GMM-style lags 2:3",
            "x_exog": "exogenous, IV-style",
        },
    }

    (RESULTS_DIR / "22_dynamic_gmm_controlled_panel_summary.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )

    (ARTIFACT_DIR / "22_dynamic_gmm_controlled_panel_summary.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )

    df.head(20).to_csv(
        ARTIFACT_DIR / "22_dynamic_gmm_controlled_panel_preview.csv",
        index=False,
    )


def build_specs():
    diff_spec = sgk.build_dynamic_panel_gmm_spec(
        dependent=Y,
        regressors=["x_pred", "x_exog"],
        lagged_dependent=True,
        lagged_dependent_lag=1,
        predetermined=["x_pred"],
        exogenous=["x_exog"],
        gmm_lags=(2, 3),
        gmm_lags_by_variable={
            "L1_y": (2, 3),
            "x_pred": (2, 3),
        },
        system=False,
        collapse=True,
        time_dummies=False,
        transformation="fd",
        steps="twostep",
        name="difference_gmm_controlled",
    )

    sys_spec = sgk.build_dynamic_panel_gmm_spec(
        dependent=Y,
        regressors=["x_pred", "x_exog"],
        lagged_dependent=True,
        lagged_dependent_lag=1,
        predetermined=["x_pred"],
        exogenous=["x_exog"],
        gmm_lags=(2, 3),
        gmm_lags_by_variable={
            "L1_y": (2, 3),
            "x_pred": (2, 3),
        },
        system=True,
        collapse=True,
        time_dummies=False,
        transformation="fd",
        steps="twostep",
        name="system_gmm_controlled",
    )

    return diff_spec, sys_spec


def to_series(obj: Any, name: str) -> pd.Series | None:
    if obj is None:
        return None

    if isinstance(obj, pd.Series):
        return obj.astype(float)

    if isinstance(obj, dict):
        return pd.Series(obj, name=name, dtype=float)

    if isinstance(obj, pd.DataFrame):
        if obj.shape[1] == 1:
            return obj.iloc[:, 0].astype(float)
        return None

    try:
        arr = np.asarray(obj, dtype=float)
        return pd.Series(arr, index=[f"param_{i}" for i in range(len(arr))], name=name)
    except Exception:
        return None


def extract_params(result: Any) -> pd.Series:
    if hasattr(sgk, "result_to_frame"):
        try:
            frame = sgk.result_to_frame(result)
            if isinstance(frame, pd.DataFrame):
                cols = {c.lower(): c for c in frame.columns}
                term_col = cols.get("term") or cols.get("variable") or cols.get("parameter")
                coef_col = cols.get("coefficient") or cols.get("coef") or cols.get("estimate")
                if term_col and coef_col:
                    s = pd.Series(
                        pd.to_numeric(frame[coef_col], errors="coerce").values,
                        index=frame[term_col].astype(str),
                        name="coefficient",
                    )
                    s = s.dropna()
                    if not s.empty:
                        s.index = s.index.map(lambda x: "const" if x in ["_con", "Intercept"] else x)
                        return s
        except Exception:
            pass

    for attr in ["params", "coefficients", "coef"]:
        if hasattr(result, attr):
            s = to_series(getattr(result, attr), "coefficient")
            if s is not None:
                s.index = s.index.astype(str)
                s.index = s.index.map(lambda x: "const" if x in ["_con", "Intercept"] else x)
                return s

    raise RuntimeError(f"Could not extract coefficients from {type(result).__name__}")


def extract_named_series_from_frame(result: Any, target_names: list[str]) -> pd.Series | None:
    if not hasattr(sgk, "result_to_frame"):
        return None

    try:
        frame = sgk.result_to_frame(result)
    except Exception:
        return None

    if not isinstance(frame, pd.DataFrame):
        return None

    cols = {c.lower(): c for c in frame.columns}
    term_col = cols.get("term") or cols.get("variable") or cols.get("parameter")

    if term_col is None:
        return None

    for target in target_names:
        col = cols.get(target.lower())
        if col:
            return pd.Series(
                pd.to_numeric(frame[col], errors="coerce").values,
                index=frame[term_col].astype(str),
                name=target,
            )

    return None


def extract_se(result: Any, params: pd.Series) -> pd.Series:
    from_frame = extract_named_series_from_frame(
        result,
        ["std_error", "std_err", "stderr", "standard_error", "se"],
    )

    if from_frame is not None:
        from_frame.index = from_frame.index.map(lambda x: "const" if x in ["_con", "Intercept"] else x)
        return from_frame.reindex(params.index)

    for attr in ["std_errors", "standard_errors", "stderr", "bse", "se"]:
        if hasattr(result, attr):
            s = to_series(getattr(result, attr), "std_error")
            if s is not None:
                s.index = s.index.astype(str)
                s.index = s.index.map(lambda x: "const" if x in ["_con", "Intercept"] else x)
                return s.reindex(params.index)

    if hasattr(sgk, "vcov"):
        try:
            v = sgk.vcov(result)

            if isinstance(v, pd.DataFrame):
                diag = np.diag(v.values)
                names = list(v.index.astype(str))
                names = ["const" if n in ["_con", "Intercept"] else n for n in names]
                return pd.Series(
                    np.sqrt(np.maximum(diag, 0)),
                    index=names,
                    name="std_error",
                ).reindex(params.index)

            arr = np.asarray(v, dtype=float)
            if arr.ndim == 2:
                diag = np.diag(arr)
                return pd.Series(
                    np.sqrt(np.maximum(diag, 0)),
                    index=params.index[: len(diag)],
                    name="std_error",
                ).reindex(params.index)

        except Exception as exc:
            print(f"[WARN] vcov extraction failed: {exc}")

    return pd.Series(np.nan, index=params.index, name="std_error")


def tidy_result(result: Any, model_name: str) -> pd.DataFrame:
    params = extract_params(result)
    se = extract_se(result, params)

    t_value = params / se.replace(0, np.nan)

    p_from_frame = extract_named_series_from_frame(
        result,
        ["p_value", "pvalue", "p"],
    )

    if p_from_frame is not None:
        p_from_frame.index = p_from_frame.index.map(lambda x: "const" if x in ["_con", "Intercept"] else x)
        p_value = p_from_frame.reindex(params.index)
    else:
        p_value = t_value.map(normal_pvalue)

    out = pd.DataFrame(
        {
            "model": model_name,
            "term": params.index,
            "coefficient": params.values,
            "std_error": se.values,
            "t_value": t_value.values,
            "p_value": p_value.values,
        }
    )

    return out


def run_gmm_models(df: pd.DataFrame):
    diff_spec, sys_spec = build_specs()

    print("[INFO] Running Difference GMM")
    try:
        diff_result = sgk.difference_gmm(
            data=df,
            entity=ENTITY,
            time=TIME,
            dependent=Y,
            regressors=["x_pred", "x_exog"],
            predetermined=["x_pred"],
            exogenous=["x_exog"],
            lagged_dependent=1,
            gmm_lags=(2, 3),
            gmm_lags_by_variable={
                "L1_y": (2, 3),
                "x_pred": (2, 3),
            },
            collapse=True,
            backend="native",
            windmeijer=True,
            time_effects=False,
            transformation="fd",
            steps="twostep",
        )
    except Exception as exc:
        print(f"[WARN] difference_gmm convenience call failed: {exc}")
        diff_result = sgk.run_difference_gmm(
            diff_spec,
            df,
            entity=ENTITY,
            time=TIME,
            backend="native",
            windmeijer=True,
        )

    print("[INFO] Running System GMM")
    try:
        sys_result = sgk.system_gmm(
            data=df,
            entity=ENTITY,
            time=TIME,
            dependent=Y,
            regressors=["x_pred", "x_exog"],
            predetermined=["x_pred"],
            exogenous=["x_exog"],
            lagged_dependent=1,
            gmm_lags=(2, 3),
            gmm_lags_by_variable={
                "L1_y": (2, 3),
                "x_pred": (2, 3),
            },
            collapse=True,
            backend="native",
            windmeijer=True,
            time_effects=False,
            transformation="fd",
            steps="twostep",
        )
    except Exception as exc:
        print(f"[WARN] system_gmm convenience call failed: {exc}")
        sys_result = sgk.run_system_gmm(
            sys_spec,
            df,
            entity=ENTITY,
            time=TIME,
            backend="native",
            windmeijer=True,
        )

    return {
        "Difference GMM": {
            "spec": diff_spec,
            "result": diff_result,
        },
        "System GMM": {
            "spec": sys_spec,
            "result": sys_result,
        },
    }


def extract_health_and_instruments(outputs: dict[str, dict[str, Any]], df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    health_rows = []
    instrument_rows = []

    for model_name, bundle in outputs.items():
        result = bundle["result"]
        spec = bundle["spec"]

        try:
            health = sgk.extract_health_metrics(
                result,
                estimator=model_name,
                collapsed=True,
                transformation="fd",
                covariance_type="twostep",
            )
            hdict = dataclass_or_object_to_dict(health)
        except Exception as exc:
            hdict = {"error": str(exc)}

        hdict["model"] = model_name
        health_rows.append(hdict)

        try:
            arch = sgk.extract_instrument_architecture(
                result,
                estimator=model_name,
                lag_range=(2, 3),
                collapsed=True,
                transformation="fd",
                groups=int(df[ENTITY].nunique()),
            )
            adict = dataclass_or_object_to_dict(arch)
        except Exception as exc:
            adict = {
                "error": str(exc),
                "estimator": model_name,
                "lag_range": "2:3",
                "collapsed": True,
                "transformation": "fd",
                "groups": int(df[ENTITY].nunique()),
            }

        adict["model"] = model_name
        adict["spec_system"] = bool(spec.system)
        adict["spec_collapse"] = bool(spec.collapse)
        adict["spec_transformation"] = str(spec.transformation)
        adict["spec_steps"] = str(spec.steps)
        instrument_rows.append(adict)

    return pd.DataFrame(health_rows), pd.DataFrame(instrument_rows)


def write_stata_references(diff_spec: Any, sys_spec: Any) -> None:
    commands = {}

    for name, spec in [
        ("difference_gmm_controlled", diff_spec),
        ("system_gmm_controlled", sys_spec),
    ]:
        try:
            commands[name] = sgk.stata_xtabond2_command(spec, entity=ENTITY, time=TIME)
        except Exception as exc:
            commands[name] = f"stata_xtabond2_command failed: {exc}"

    command_path = RESULTS_DIR / "22_stata_xtabond2_command_reference.txt"
    command_path.write_text(
        "\n\n".join([f"{k}:\n{v}" for k, v in commands.items()]),
        encoding="utf-8",
    )

    (ARTIFACT_DIR / "22_stata_xtabond2_command_reference.txt").write_text(
        command_path.read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    do_path = STATA_DIR / "22_stata_xtabond2_parity_reference.do"

    try:
        sgk.write_stata_parity_do_file(
            do_path,
            data_path=str(CONTROLLED_DATA),
            entity=ENTITY,
            time=TIME,
            dynamic_gmm=[diff_spec, sys_spec],
        )
    except Exception as exc:
        manual = f"""
clear all
set more off

import delimited using "{CONTROLLED_DATA.as_posix()}", clear
xtset {ENTITY} {TIME}

* Difference GMM reference
xtabond2 {Y} L.{Y} x_pred x_exog, ///
    gmm(L.{Y} x_pred, lag(2 3) collapse) ///
    iv(x_exog) ///
    noleveleq twostep robust

* System GMM reference
xtabond2 {Y} L.{Y} x_pred x_exog, ///
    gmm(L.{Y} x_pred, lag(2 3) collapse) ///
    iv(x_exog, equation(diff)) ///
    iv(x_exog, equation(level)) ///
    twostep robust

* Auto writer failed with:
* {exc}
"""
        do_path.write_text(manual.strip() + "\n", encoding="utf-8")

    (ARTIFACT_DIR / "22_stata_xtabond2_parity_reference.do").write_text(
        do_path.read_text(encoding="utf-8"),
        encoding="utf-8",
    )


def write_uoh_table(result_tables: dict[str, pd.DataFrame]) -> None:
    models = []
    model_names = []

    for model_name, table in result_tables.items():
        uoh_table = table.rename(
            columns={
                "coefficient": "coef",
                "std_error": "se",
                "p_value": "pvalue",
            }
        )[["term", "coef", "se", "pvalue"]].copy()

        model = from_coefficient_table(
            uoh_table,
            name=model_name,
            term_col="term",
            coef_col="coef",
            se_col="se",
            pvalue_col="pvalue",
            depvar=Y,
            statistics={
                "source": "systemgmmkit 0.5.11 controlled Dynamic GMM benchmark",
            },
            diagnostics={
                "dataset": "Controlled synthetic dynamic panel",
                "entity": ENTITY,
                "time": TIME,
                "gmm_lags": "2:3",
                "collapse": True,
            },
            source="systemgmmkit-controlled-dynamic-gmm",
        )

        models.append(model)
        model_names.append(model_name)

    notes = [
        "Controlled synthetic panel.",
        "Lagged dependent variable treated as endogenous with GMM lags 2:3.",
        "x_pred treated as predetermined with GMM lags 2:3.",
        "x_exog treated as exogenous IV-style.",
        "Collapsed instruments; two-step estimation.",
        "Stata xtabond2 reference commands are exported separately.",
    ]

    md = outreg(
        models,
        using=UOH_DIR / "22_uoh_dynamic_gmm_controlled_comparison.md",
        model_names=model_names,
        title="Controlled Dynamic GMM Benchmark",
        labels=MODEL_LABELS,
        notes=notes,
        decimals=6,
        stars=True,
        replace=True,
    )

    tex = outreg(
        models,
        using=UOH_DIR / "22_uoh_dynamic_gmm_controlled_comparison.tex",
        model_names=model_names,
        title="Controlled Dynamic GMM Benchmark",
        labels=MODEL_LABELS,
        notes=notes,
        decimals=6,
        stars=True,
        replace=True,
    )

    (ARTIFACT_DIR / "22_uoh_dynamic_gmm_controlled_comparison.md").write_text(
        Path(md).read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    (ARTIFACT_DIR / "22_uoh_dynamic_gmm_controlled_comparison.tex").write_text(
        Path(tex).read_text(encoding="utf-8"),
        encoding="utf-8",
    )


def write_artifact_note() -> None:
    note = """# Controlled Dynamic GMM Parity Artifact

This artifact provides a controlled dynamic-panel benchmark for systemgmmkit's Difference GMM and System GMM workflows.

Dataset:
- Synthetic balanced dynamic panel
- Entity index: id
- Time index: time
- Dependent variable: y
- Units: 120
- Periods: 10

Data-generating process:
y_it = 0.55*y_i,t-1 + 0.35*x_pred_it + 0.25*x_exog_it + alpha_i + tau_t + eps_it

Variable roles:
- Lagged dependent variable: endogenous, GMM-style instruments, lags 2:3
- x_pred: predetermined, GMM-style instruments, lags 2:3
- x_exog: exogenous, IV-style instrument
- Instruments are collapsed
- Estimation uses two-step GMM

Purpose:
This artifact validates the formal dynamic-GMM workflow separately from the N-CMAPSS DS01 smoke workflow. The N-CMAPSS artifact validates data processing and reporting interoperability; this controlled benchmark is designed for Difference/System GMM validation and Stata xtabond2 reference generation.

Generated outputs:
- 22_dynamic_gmm_controlled_panel_summary.json
- 22_dynamic_gmm_controlled_panel_preview.csv
- 22_difference_gmm_results.csv
- 22_system_gmm_results.csv
- 22_dynamic_gmm_health_metrics.csv
- 22_dynamic_gmm_instrument_architecture.csv
- 22_stata_xtabond2_command_reference.txt
- 22_stata_xtabond2_parity_reference.do
- 22_uoh_dynamic_gmm_controlled_comparison.md
- 22_uoh_dynamic_gmm_controlled_comparison.tex

Interpretation boundary:
The Stata do-file is a reference script for external parity execution. Numerical Stata parity should be claimed only after running the exported do-file in Stata and comparing the resulting coefficients, standard errors, diagnostics, and instrument counts.
"""
    (ARTIFACT_DIR / "22_dynamic_gmm_parity_artifact_note.md").write_text(
        note,
        encoding="utf-8",
    )


def main() -> None:
    print("[INFO] systemgmmkit version:", getattr(sgk, "__version__", "unknown"))
    print("[INFO] systemgmmkit path:", getattr(sgk, "__file__", "unknown"))

    df = generate_controlled_panel()
    write_data_artifacts(df)

    outputs = run_gmm_models(df)

    result_tables: dict[str, pd.DataFrame] = {}

    for model_name, bundle in outputs.items():
        result = bundle["result"]
        table = tidy_result(result, model_name)
        result_tables[model_name] = table

        file_stem = "difference_gmm" if model_name == "Difference GMM" else "system_gmm"

        table.to_csv(
            RESULTS_DIR / f"22_{file_stem}_results.csv",
            index=False,
        )

        table.to_csv(
            ARTIFACT_DIR / f"22_{file_stem}_results.csv",
            index=False,
        )

        print(f"[PASS] {model_name}")
        print(table.to_string(index=False))

    health, instruments = extract_health_and_instruments(outputs, df)

    health.to_csv(RESULTS_DIR / "22_dynamic_gmm_health_metrics.csv", index=False)
    health.to_csv(ARTIFACT_DIR / "22_dynamic_gmm_health_metrics.csv", index=False)

    instruments.to_csv(RESULTS_DIR / "22_dynamic_gmm_instrument_architecture.csv", index=False)
    instruments.to_csv(ARTIFACT_DIR / "22_dynamic_gmm_instrument_architecture.csv", index=False)

    diff_spec = outputs["Difference GMM"]["spec"]
    sys_spec = outputs["System GMM"]["spec"]

    write_stata_references(diff_spec, sys_spec)
    write_uoh_table(result_tables)
    write_artifact_note()

    status = {
        "systemgmmkit_version": getattr(sgk, "__version__", "unknown"),
        "systemgmmkit_path": getattr(sgk, "__file__", "unknown"),
        "status": "PASS",
        "models": list(result_tables.keys()),
        "dataset": str(CONTROLLED_DATA),
        "outputs": {
            "difference_gmm_results": "Artifacts/Joss/tables/22_difference_gmm_results.csv",
            "system_gmm_results": "Artifacts/Joss/tables/22_system_gmm_results.csv",
            "health_metrics": "Artifacts/Joss/tables/22_dynamic_gmm_health_metrics.csv",
            "instrument_architecture": "Artifacts/Joss/tables/22_dynamic_gmm_instrument_architecture.csv",
            "stata_reference": "Artifacts/Joss/tables/22_stata_xtabond2_parity_reference.do",
            "uoh_markdown": "Artifacts/Joss/tables/22_uoh_dynamic_gmm_controlled_comparison.md",
            "uoh_latex": "Artifacts/Joss/tables/22_uoh_dynamic_gmm_controlled_comparison.tex",
        },
    }

    (RESULTS_DIR / "22_dynamic_gmm_parity_status.json").write_text(
        json.dumps(status, indent=2),
        encoding="utf-8",
    )

    (ARTIFACT_DIR / "22_dynamic_gmm_parity_status.json").write_text(
        json.dumps(status, indent=2),
        encoding="utf-8",
    )

    print("[DONE] Controlled Dynamic GMM artifact complete.")
    print(json.dumps(status, indent=2))


if __name__ == "__main__":
    main()
