from __future__ import annotations

import importlib.metadata
import io
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
from universal_output_hub import OutputHub

import systemgmmkit as sgk

ROOT = Path(__file__).resolve().parents[3]
ARTIFACTS = ROOT / "artifacts" / "joss" / "tables"
PAPER_DIR = ROOT / "paper_jss"
TABLE_DIR = PAPER_DIR / "tables"
MANIFEST = PAPER_DIR / "publication_manifest.json"

TARGET_VERSION = "1.0.0"
TARGET_TAG = "v1.0.0"
EVIDENCE_TAG = "v0.5.14"
OUTPUTHUB_VERSION = "0.2.4"

APPLICATION_PANEL = ARTIFACTS / "01_ncmapss_model_panel_summary.csv"
APPLICATION_RESULTS = ARTIFACTS / "02_ncmapss_dynamic_ols_results.csv"
APPLICATION_FIT = ARTIFACTS / "03_ncmapss_dynamic_ols_fit_summary.csv"
APPLICATION_HOLDOUT = ARTIFACTS / "04_ncmapss_holdout_metrics.csv"
APPLICATION_SPEC = ARTIFACTS / "05_ncmapss_statistical_model_specification.json"
DIFFERENCE_RESULTS = ARTIFACTS / "22_difference_gmm_results.csv"
SYSTEM_RESULTS = ARTIFACTS / "22_system_gmm_results.csv"
GMM_HEALTH = ARTIFACTS / "22_dynamic_gmm_health_metrics.csv"
GMM_STATUS = ARTIFACTS / "22_dynamic_gmm_parity_status.json"
AUTO_SEARCH = ROOT / "results" / "comparisons" / "auto_gmm_search_results.csv"
AUTO_SEARCH_STATUS = ROOT / "results" / "comparisons" / "auto_gmm_search_status.json"
ML_COMPARISON = ROOT / "results" / "comparisons" / "ml_external_python_comparison.csv"

TABLE_SOURCES = {
    "table_01_application_design.tex": (
        "Author's computation from the processed N-CMAPSS DS01 development panel; "
        "artifacts/joss/tables/01_ncmapss_model_panel_summary.csv and "
        "05_ncmapss_statistical_model_specification.json."
    ),
    "table_02_application_estimates.tex": (
        "Author's computation using statsmodels with HC1 covariance; "
        "artifacts/joss/tables/02_ncmapss_dynamic_ols_results.csv and "
        "03_ncmapss_dynamic_ols_fit_summary.csv."
    ),
    "table_03_holdout_performance.tex": (
        "Author's computation from the cycle-ordered outer holdout and train-only model search; "
        "artifacts/joss/tables/04_ncmapss_holdout_metrics.csv, "
        "06_ncmapss_direct_sensor_model_selection.csv, and "
        "07_ncmapss_direct_sensor_model_status.json."
    ),
    "table_04_controlled_gmm_results.tex": (
        "Author's computation with systemgmmkit 1.0.0 and Universal Output Hub 0.2.4; "
        "artifacts/joss/tables/22_difference_gmm_results.csv, "
        "22_system_gmm_results.csv, and 22_dynamic_gmm_health_metrics.csv."
    ),
    "table_05_xtabond2_parameter_parity.tex": (
        "Author's computation from the signed systemgmmkit 0.5.14 release certificate; "
        "v0.5.14:artifacts/parity/xtabond2/diagnostic_parity_certificate.csv."
    ),
    "table_06_xtabond2_diagnostic_parity.tex": (
        "Author's computation from the signed systemgmmkit 0.5.14 release certificate; "
        "v0.5.14:artifacts/parity/xtabond2/diagnostic_parity_certificate.csv."
    ),
    "table_07_static_reference_checks.tex": (
        "Author's computation from the systemgmmkit 0.5.14 static "
        "cross-software validation artifact (Artifact 27)."
    ),
    "table_08_auto_gmm_search.tex": (
        "Author's computation from the diagnostic-first search executed with "
        "systemgmmkit 1.0.0; results/comparisons/auto_gmm_search_results.csv."
    ),
    "table_09_workflow_layer.tex": (
        "Author's runtime audit of the installed systemgmmkit 1.0.0 public API; "
        "tables exported with Universal Output Hub 0.2.4."
    ),
}

# The publication manifest retains the exact paths above. Captions use concise
# provenance so the official JSS caption layout remains legible in print.
TABLE_CAPTION_SOURCES = {
    "table_01_application_design.tex": (
        "Author's computation from the processed N-CMAPSS DS01 panel (Artifacts 01 and 05)."
    ),
    "table_02_application_estimates.tex": (
        "Author's computation using statsmodels with HC1 covariance (Artifacts 02 and 03)."
    ),
    "table_03_holdout_performance.tex": (
        "Author's computation from the nested cycle-ordered validation (Artifacts 04, 06, and 07)."
    ),
    "table_04_controlled_gmm_results.tex": (
        "Author's computation with systemgmmkit 1.0.0 (Artifact 22)."
    ),
    "table_05_xtabond2_parameter_parity.tex": (
        "Author's computation from the signed v0.5.14 release certificate (Artifact 24)."
    ),
    "table_06_xtabond2_diagnostic_parity.tex": (
        "Author's computation from the signed v0.5.14 release certificate (Artifact 24)."
    ),
    "table_07_static_reference_checks.tex": (
        "Author's computation from the v0.5.14 cross-software checks (Artifact 27)."
    ),
    "table_08_auto_gmm_search.tex": (
        "Author's computation from the executed diagnostic-first search."
    ),
    "table_09_workflow_layer.tex": (
        "Author's runtime audit of the installed systemgmmkit 1.0.0 API."
    ),
}


def _require_release() -> None:
    if sgk.__version__ != TARGET_VERSION:
        raise RuntimeError(
            f"JSS tables require systemgmmkit {TARGET_VERSION}; found {sgk.__version__}."
        )
    installed_hub = importlib.metadata.version("universal-output-hub")
    if installed_hub != OUTPUTHUB_VERSION:
        raise RuntimeError(
            f"JSS tables require universal-output-hub {OUTPUTHUB_VERSION}; found {installed_hub}."
        )


def _git_text(path: str) -> str:
    completed = subprocess.run(
        ["git", "show", f"{EVIDENCE_TAG}:{path}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return completed.stdout


def _git_csv(path: str) -> pd.DataFrame:
    return pd.read_csv(io.StringIO(_git_text(path)))


def _release_commit() -> str:
    return subprocess.run(
        ["git", "rev-parse", f"{TARGET_TAG}^{{commit}}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout.strip()


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_csv(path)


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def _fmt(value: Any, decimals: int = 3) -> str:
    if pd.isna(value):
        return "--"
    return f"{float(value):.{decimals}f}"


def _sci(value: Any) -> str:
    if pd.isna(value):
        return "--"
    return f"{float(value):.2e}"


def _clear_generated_tables() -> None:
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    for pattern in ("*.tex", "*.csv", "*.md"):
        for path in TABLE_DIR.glob(pattern):
            path.unlink()


def _export_ordinary(name: str, frame: pd.DataFrame, *, index: str) -> None:
    hub = OutputHub(
        "systemgmmkit JSS tables",
        metadata={
            "systemgmmkit_version": TARGET_VERSION,
            "universal_output_hub_version": OUTPUTHUB_VERSION,
            "release_tag": TARGET_TAG,
        },
    )
    hub.add_table(name, frame.set_index(index))
    hub.export_tables(TABLE_DIR, formats=("tex", "csv", "md"))


def _export_regression(
    name: str,
    models: list[dict[str, Any]],
    *,
    labels: dict[str, str],
    order: list[str],
    stats_order: list[str],
) -> None:
    hub = OutputHub(
        "systemgmmkit JSS model tables",
        metadata={
            "systemgmmkit_version": TARGET_VERSION,
            "universal_output_hub_version": OUTPUTHUB_VERSION,
            "release_tag": TARGET_TAG,
        },
    )
    for model in models:
        hub.add_model(model)
    kwargs = {
        "labels": labels,
        "order": order,
        "stats_order": stats_order,
        "decimals": 3,
        "stars": True,
        "add_star_note": False,
    }
    for suffix in ("tex", "csv", "md"):
        hub.export_regression_table(TABLE_DIR / f"{name}.{suffix}", **kwargs)


def _application_design_table() -> None:
    panel = _read_csv(APPLICATION_PANEL).iloc[0]
    spec = _read_json(APPLICATION_SPEC)
    note = spec["dynamic_gmm_role_suggestion"]["note"]
    if "Lagged risk is intentionally excluded" not in note:
        raise RuntimeError("Application specification does not contain the leakage guard.")
    rows = pd.DataFrame(
        [
            ("Dataset", panel["dataset"]),
            ("Analysis target", "Risk proxy derived from RUL"),
            ("Observations after lagging", str(int(panel["rows_after_lag"]))),
            ("Units", str(int(panel["n_units"]))),
            ("Cycle range", f"{int(panel['min_cycle'])}--{int(panel['max_cycle'])}"),
            ("OLS regressors", "Lagged sensor summary and operating controls"),
            ("Direct-model regressors", "Train-fitted sensor PCs and dynamics"),
            ("Target-lag rule", "Lagged risk/RUL excluded"),
            ("Validation design", "Nested selection through cycle 70; test 71--100"),
        ],
        columns=["Design item", "Value"],
    )
    _export_ordinary("table_01_application_design", rows, index="Design item")


def _model_dict(
    name: str,
    result_rows: pd.DataFrame,
    *,
    statistics: dict[str, Any],
    diagnostics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "name": name,
        "params": dict(zip(result_rows["term"], result_rows["coefficient"])),
        "std_errors": dict(zip(result_rows["term"], result_rows["std_error"])),
        "pvalues": dict(zip(result_rows["term"], result_rows["p_value"])),
        "statistics": statistics,
        "diagnostics": diagnostics or {},
    }


def _application_estimates_table() -> None:
    results = _read_csv(APPLICATION_RESULTS)
    fit = _read_csv(APPLICATION_FIT).set_index("model")
    keep = ["Intercept", "z_L1_sensor_mean_z", "z_Fc", "z_hs"]
    models = []
    for model_key, label in (
        ("pooled_dynamic_ols", "Pooled OLS"),
        ("unit_fe_dynamic_ols", "Unit FE"),
    ):
        rows = results.loc[(results["model"] == model_key) & results["term"].isin(keep)].copy()
        summary = fit.loc[model_key]
        models.append(
            _model_dict(
                label,
                rows,
                statistics={
                    "N": int(summary["n_obs"]),
                    "R2": float(summary["r2"]),
                    "Adj. R2": float(summary["adj_r2"]),
                },
            )
        )
    _export_regression(
        "table_02_application_estimates",
        models,
        labels={
            "Intercept": "Constant",
            "z_L1_sensor_mean_z": "Lagged sensor state",
            "z_Fc": "Flow control (Fc)",
            "z_hs": "Health setting (hs)",
        },
        order=keep,
        stats_order=["N", "R2", "Adj. R2"],
    )


def _holdout_table() -> None:
    raw = _read_csv(APPLICATION_HOLDOUT)
    rows = pd.DataFrame(
        {
            "Model": raw["model"].map(
                {
                    "pooled_dynamic_ols": "Pooled dyn. OLS",
                    "direct_sensor_random_forest": "Direct sensor RF",
                }
            ),
            "Split": "Cycles 1--70 / 71--100",
            "N eval": raw["n_eval"].astype(int).astype(str),
            "RMSE": raw["rmse"].map(_fmt),
            "MAE": raw["mae"].map(_fmt),
            "SMAPE": raw["smape"].map(_fmt),
            "R2": raw["r2"].map(_fmt),
        }
    )
    _export_ordinary("table_03_holdout_performance", rows, index="Model")


def _controlled_gmm_table() -> None:
    status = _read_json(GMM_STATUS)
    if status.get("systemgmmkit_version") != TARGET_VERSION or status.get("status") != "PASS":
        raise RuntimeError("Controlled GMM artifact is not a passing 1.0.0 run.")
    health = _read_csv(GMM_HEALTH).set_index("model")
    models = []
    for label, path in (
        ("Difference GMM", DIFFERENCE_RESULTS),
        ("System GMM", SYSTEM_RESULTS),
    ):
        rows = _read_csv(path)
        diag = health.loc[label]
        models.append(
            _model_dict(
                label,
                rows,
                statistics={
                    "N": int(diag["nobs"]),
                    "Groups": int(diag["groups"]),
                    "Instruments": int(diag["instruments"]),
                    "I/N": float(diag["instrument_group_ratio"]),
                    "Instrument health": str(diag["instrument_health_status"]),
                },
                diagnostics={
                    "AR(1) p": float(diag["ar1_p"]),
                    "AR(2) p": float(diag["ar2_p"]),
                    "Hansen p": float(diag["hansen_p"]),
                    "Sargan p": float(diag["sargan_p"]),
                },
            )
        )
    _export_regression(
        "table_04_controlled_gmm_results",
        models,
        labels={
            "x_pred": "Predetermined regressor",
            "x_exog": "Exogenous regressor",
            "L1_y": "Lagged dependent variable",
            "const": "Constant",
        },
        order=["L1_y", "x_pred", "x_exog", "const"],
        stats_order=[
            "N",
            "Groups",
            "Instruments",
            "I/N",
            "Instrument health",
            "AR(1) p",
            "AR(2) p",
            "Hansen p",
            "Sargan p",
        ],
    )


SPEC_LABELS = {
    "system_gmm_baseline_controls": "Baseline controls",
    "system_gmm_no_controls": "No controls",
    "system_gmm_three_way_controls": "Three-way controls",
    "system_gmm_decomposition_controls": "Decomposition controls",
    "system_gmm_unbalanced_panel": "Unbalanced panel",
    "system_gmm_variable_missing": "Variable missingness",
}


def _certificate_tables() -> None:
    cert = _git_csv("artifacts/parity/xtabond2/diagnostic_parity_certificate.csv")
    cert = cert.loc[cert["spec"].isin(SPEC_LABELS)].copy()
    if len(cert) != 6 or set(cert["status"]) != {"PASS_XTABOND2_PARITY"}:
        raise RuntimeError("The 0.5.14 six-spec xtabond2 certificate is incomplete.")
    cert["Specification"] = cert["spec"].map(SPEC_LABELS)
    cert["Sample keys"] = cert["sample_status"].map(
        {"NOT_APPLICABLE": "Not required", "PASS_EXACT_SAMPLE_KEYS": "Exact"}
    )
    params = pd.DataFrame(
        {
            "Specification": cert["Specification"],
            "N": cert["native_nobs"].astype(int).astype(str),
            "Groups": cert["native_n_groups"].astype(int).astype(str),
            "Instr.": cert["native_n_instruments"].astype(int).astype(str),
            "Max coef. diff": cert["max_abs_coef_diff"].map(_sci),
            "Max rel. SE diff": cert["max_rel_se_diff"].map(_sci),
            "Keys": cert["Sample keys"],
            "Status": "PASS",
        }
    )
    _export_ordinary("table_05_xtabond2_parameter_parity", params, index="Specification")

    rejected = cert["stata_hansen_reject_005"].astype(bool) | cert[
        "stata_sargan_reject_005"
    ].astype(bool)
    diagnostics = pd.DataFrame(
        {
            "Specification": cert["Specification"],
            "Hansen p": cert["stata_hansen_p"].map(_fmt),
            "Sargan p": cert["stata_sargan_p"].map(_fmt),
            "AR(1) p": cert["stata_ar1_p"].map(_fmt),
            "AR(2) p": cert["stata_ar2_p"].map(_fmt),
            "Over-id (5%)": rejected.map({True: "Reject", False: "Do not reject"}),
            "Status": "PASS",
        }
    )
    _export_ordinary(
        "table_06_xtabond2_diagnostic_parity",
        diagnostics,
        index="Specification",
    )


def _static_reference_table() -> None:
    raw = _git_csv(
        "artifacts/joss/tables/27_static_cross_software_comparison/"
        "27_static_cross_software_pairwise_summary.csv"
    )
    order = ["OLS", "Pooled OLS", "Fixed Effects", "Random Effects", "2SLS"]
    rows = []
    for model in order:
        group = raw.loc[raw["model"] == model]
        if group.empty:
            raise RuntimeError(f"Missing static-reference rows for {model}.")
        rows.append(
            {
                "Estimator": model,
                "Comparators": ", ".join(group["comparison_software"]),
                "Max coef. diff": _sci(group["max_abs_coef_diff"].max()),
                "Max SE diff": _sci(group["max_abs_se_diff"].max()),
            }
        )
    _export_ordinary(
        "table_07_static_reference_checks",
        pd.DataFrame(rows),
        index="Estimator",
    )


def _auto_search_table() -> None:
    raw = _read_csv(AUTO_SEARCH)
    status = _read_json(AUTO_SEARCH_STATUS)
    if status.get("status") != "PASS" or len(raw) != 4:
        raise RuntimeError("The automatic GMM search artifact is incomplete.")
    best_id = int(status["best_candidate_id"])
    labels = (
        raw["estimator"].str.replace(" GMM", "", regex=False) + ", " + raw["lag_window"].astype(str)
    )
    candidate_status = []
    for candidate_id, valid in zip(raw["candidate_id"], raw["valid"], strict=True):
        if int(candidate_id) == best_id:
            candidate_status.append("Selected")
        elif str(valid).strip().lower() == "true":
            candidate_status.append("Admissible")
        else:
            candidate_status.append("Rejected")
    rows = pd.DataFrame(
        {
            "Candidate": labels,
            "Status": candidate_status,
            "RMSE": raw["rmse"].map(_fmt),
            "R2": raw["r2"].map(_fmt),
            "Hansen p": raw["hansen_p"].map(
                lambda value: "Not reported" if pd.isna(value) else _fmt(value)
            ),
            "AR(2) p": raw["ar2_p"].map(_fmt),
            "Instr.": raw["n_instruments"].astype("Int64").astype(str),
        }
    )
    _export_ordinary("table_08_auto_gmm_search", rows, index="Candidate")


def _workflow_table() -> None:
    from systemgmmkit.ml import (
        auto_dynamic_gmm,
        backtest_forecast,
        compare_models,
        dynamic_gmm_candidate_grid,
        forecast,
        panel_train_test_split,
        regression_metrics,
    )

    grid = dynamic_gmm_candidate_grid(
        models=("system", "difference"),
        steps=("twostep",),
        lag_windows=((2, 2), (2, 3)),
        transformations=("fd",),
        collapse_options=(True,),
    )
    sample = pd.DataFrame({"id": [1, 1, 1, 2, 2, 2], "time": [1, 2, 3, 1, 2, 3], "y": range(6)})
    train, test = panel_train_test_split(sample, time="time", test_size=1)
    metrics = regression_metrics([0.0, 1.0], [0.0, 1.0])
    if len(grid) != 4 or train.empty or test.empty or metrics["rmse"] != 0.0:
        raise RuntimeError("The 1.0.0 ML/search runtime audit failed.")
    callables = [auto_dynamic_gmm, forecast, backtest_forecast, compare_models]
    if not all(callable(item) for item in callables):
        raise RuntimeError("A required 1.0.0 workflow API is not callable.")
    rows = pd.DataFrame(
        [
            (
                "Post-estimation",
                "predict, confint, margins",
                "API verified",
                "Estimator-based inference",
            ),
            (
                "Panel validation",
                "split, metrics",
                "Smoke passed",
                "Panel-time order",
            ),
            (
                "Forecasting",
                "forecast, backtest, compare",
                "API verified",
                "No causal claim",
            ),
        ],
        columns=["Layer", "APIs/workflow", "Runtime", "Boundary"],
    )
    _export_ordinary("table_09_workflow_layer", rows, index="Layer")


def _latex_escape(text: str) -> str:
    replacements = {
        "&": r"\&",
        "%": r"\%",
        "_": r"\_",
        "#": r"\#",
    }
    for raw, escaped in replacements.items():
        text = text.replace(raw, escaped)
    return text


def _table(
    *,
    caption: str,
    label: str,
    filename: str,
    note: str,
) -> str:
    caption_text = caption.rstrip(".") + "."
    source_text = _latex_escape(TABLE_CAPTION_SOURCES[filename]).rstrip(".") + "."
    note_text = _latex_escape(note).rstrip(".") + "."
    return (
        r"\begin{table}[t!]"
        "\n"
        r"\centering"
        "\n"
        r"\small"
        "\n"
        r"\setlength{\tabcolsep}{4.5pt}"
        "\n"
        r"\renewcommand{\arraystretch}{1.16}"
        "\n"
        rf"\input{{tables/{filename}}}"
        "\n"
        rf"\caption{{\label{{{label}}} {caption_text} Source: {source_text} Notes: {note_text}}}"
        "\n"
        r"\end{table}"
        "\n"
    )


def _build_main_tex() -> str:
    holdout = _read_csv(APPLICATION_HOLDOUT).set_index("model")
    required_models = {"pooled_dynamic_ols", "direct_sensor_random_forest"}
    if not required_models.issubset(holdout.index):
        raise RuntimeError("Holdout artifact is missing the baseline or direct sensor model.")
    pooled_holdout = holdout.loc["pooled_dynamic_ols"]
    direct_holdout = holdout.loc["direct_sensor_random_forest"]
    ml_comparison = _read_csv(ML_COMPARISON).set_index("package")
    required_comparators = {"systemgmmkit", "statsmodels", "scikit-learn"}
    if not required_comparators.issubset(ml_comparison.index):
        raise RuntimeError("ML comparison is missing a registered package row.")
    statsmodels_ml = ml_comparison.loc["statsmodels"]
    sklearn_ml = ml_comparison.loc["scikit-learn"]
    tables = {
        "design": _table(
            caption="Leakage-controlled N-CMAPSS application design",
            label="tab:application-design",
            filename="table_01_application_design.tex",
            note=(
                "The target is a risk proxy derived from RUL. Lagged risk and lagged RUL are excluded "
                "because they encode a deterministic countdown identity."
            ),
        ),
        "application": _table(
            caption="N-CMAPSS lagged-sensor baseline estimates",
            label="tab:application-estimates",
            filename="table_02_application_estimates.tex",
            note=(
                "HC1 standard errors are in parentheses. Unit fixed effects are included in the second "
                "column but their individual coefficients are omitted from display."
            ),
        ),
        "holdout": _table(
            caption="Late-cycle holdout performance",
            label="tab:holdout",
            filename="table_03_holdout_performance.tex",
            note=(
                "The forest is selected only within cycles 1--70 using expanding windows. The final cycles "
                "71--100 are evaluated once; neither model uses lagged risk, lagged RUL, or cycle."
            ),
        ),
        "gmm": _table(
            caption="Controlled Difference GMM and System GMM results",
            label="tab:controlled-gmm",
            filename="table_04_controlled_gmm_results.tex",
            note=(
                "Two-step collapsed specifications. Standard errors are in parentheses. AR and "
                "over-identification entries are p-values; diagnostic non-rejection is not proof of validity."
            ),
        ),
        "parity_params": _table(
            caption="System GMM parameter and count parity with Stata xtabond2",
            label="tab:parity-parameters",
            filename="table_05_xtabond2_parameter_parity.tex",
            note=(
                "All six release-certified specifications pass their registered tolerances. Exact sample-key "
                "matching is required for the unbalanced and variable-missing designs; Not required means "
                "that gate was not registered for the four balanced fixtures."
            ),
        ),
        "parity_diag": _table(
            caption="System GMM diagnostic parity with Stata xtabond2",
            label="tab:parity-diagnostics",
            filename="table_06_xtabond2_diagnostic_parity.tex",
            note=(
                "PASS denotes cross-software numerical agreement. The over-identification column reports "
                "the Stata-side 5 percent decision and is not a model endorsement."
            ),
        ),
        "static": _table(
            caption="Aligned static-estimator reference checks",
            label="tab:static-reference",
            filename="table_07_static_reference_checks.tex",
            note=(
                "Specifications and samples are aligned. Random-effects and 2SLS claims remain at the "
                "coefficient level because covariance conventions differ across packages."
            ),
        ),
        "auto_search": _table(
            caption="Diagnostic-first automatic GMM search on the controlled panel",
            label="tab:auto-search",
            filename="table_08_auto_gmm_search.tex",
            note=(
                "Cycle-ordered holdout covers the final two periods. The strict gate rejects the Difference "
                "GMM 2:2 candidate because a Hansen test is not reported; the value is not imputed. "
                "Selection ranks only admissible candidates and does not establish causal identification."
            ),
        ),
        "workflow": _table(
            caption="Post-estimation and ML-style workflow coverage",
            label="tab:workflow-layer",
            filename="table_09_workflow_layer.tex",
            note=(
                "This is workflow coverage, not estimator parity. Prediction and validation utilities operate "
                "around fitted econometric results and do not create causal identification."
            ),
        ),
    }
    return rf"""\documentclass[article]{{jss}}

\usepackage{{amsmath,booktabs,graphicx,lmodern,placeins}}

\author{{Oluwajuwon Mayomi Akanbi\\Independent Researcher / Developer}}
\Plainauthor{{Oluwajuwon Mayomi Akanbi}}
\title{{\pkg{{systemgmmkit}}: Reproducible Dynamic-Panel GMM Workflows in \proglang{{Python}}}}
\Plaintitle{{systemgmmkit: Reproducible Dynamic-Panel GMM Workflows in Python}}
\Shorttitle{{\pkg{{systemgmmkit}}: Dynamic-Panel GMM Workflows}}
\Abstract{{
\pkg{{systemgmmkit}} is a \proglang{{Python}} toolkit for static panel estimators, instrumental-variable
estimation, Difference GMM, System GMM, diagnostics, post-estimation, panel-aware validation, forecasting, and
diagnostic-constrained specification search. The package does not introduce a new GMM estimator. Its
contribution is an integrated and auditable workflow in which model specification, instrument construction,
finite-sample covariance choices, diagnostics, predictions, and reporting remain visible. This paper documents
release 1.0.0, including structured instrument-health reporting and the six-specification numerical
certificate established in release 0.5.14 against \proglang{{Stata}}
\code{{xtabond2}}, nested leakage-controlled N-CMAPSS results, an executed automatic GMM search, and Universal Output
Hub table generation. The reported parity is benchmark-specific and must not be read as evidence that every
empirical specification is valid.
}}
\Keywords{{dynamic panel data, generalized method of moments, System GMM, \proglang{{Python}}, reproducibility}}
\Plainkeywords{{dynamic panel data, generalized method of moments, System GMM, Python, reproducibility}}
\Address{{
Oluwajuwon Mayomi Akanbi\\
Independent Researcher / Developer\\
URL: \url{{https://github.com/Akanom/systemgmmkit}}
}}

\begin{{document}}

\section{{Introduction}}
Dynamic-panel models are used when outcomes are persistent, unit-specific effects matter, and one or more
regressors may be predetermined or endogenous \citep{{arellano1991some,blundell1998initial,bond2002dynamic}}.
In practice, applied work requires more than a coefficient vector. Researchers must control the estimation
sample, define instrument roles and lag windows, monitor instrument growth, assess serial-correlation and
over-identification diagnostics, and preserve enough metadata for independent reproduction.

\pkg{{systemgmmkit}} brings these tasks into a common \proglang{{Python}} interface. The package covers OLS, pooled OLS,
fixed effects, random effects, panel IV/2SLS, Difference GMM, and System GMM, with structured result objects and
post-estimation utilities. It complements established software rather than ranking or replacing it
\citep{{roodman2009xtabond2,croissant2008panel,seabold2010statsmodels,sheppard2024linearmodels,pydynpd}}.

\section{{Software design and claim boundaries}}
The public workflow separates model specification, estimation, diagnostics, prediction, and reporting. For
dynamic GMM, users declare the dependent variable, panel indexes, regressor roles, lag windows,
transformation, collapsed or uncollapsed instruments, estimation step, and covariance correction. Results
retain observation and group counts, instrument counts, coefficient and covariance output, Hansen and Sargan
tests, and Arellano--Bond serial-correlation diagnostics.

Version 1.0.0 declares the documented public interface stable and adds a structured instrument-health
assessment to native and \code{{pydynpd}} result summaries. It reports instrument and group counts, their
ratio, and conservative acceptable, approaching, critical, or unavailable states. A critical state means
that instruments outnumber groups and prompts shorter lag windows, collapsed instruments, and sensitivity
checks. This rule is a screening signal rather than proof of bias or automatic invalidation of Hansen/Sargan
inference.

Release 0.5.14 added certified unbalanced-panel and variable-specific missing-data paths to the maintained
\code{{xtabond2}} evidence. The release certificate tests complete parameter sets, Windmeijer-corrected
two-step standard errors, counts, diagnostics, and, where relevant, exact estimation-sample keys. Agreement is
therefore asserted only for the registered benchmark specifications. A passing parity row says that two
implementations agree; it does not say that the instruments are substantively valid or that the specification
answers a particular research question.

\section{{Econometric formulation}}
The package represents the dynamic panel model as
\begin{{equation}}
\label{{eq:dynamic-panel}}
y_{{it}}
= \rho y_{{i,t-1}}
+ \mathbf{{x}}_{{it}}^\top \boldsymbol{{\beta}}
+ \alpha_i + \tau_t + \varepsilon_{{it}},
\end{{equation}}
where $i=1,\ldots,N$ indexes units, $t=1,\ldots,T_i$ indexes time,
$\alpha_i$ is an unobserved unit effect, and $\tau_t$ is an optional time effect.
The regressor vector $\mathbf{{x}}_{{it}}$ is partitioned by the user's endogenous,
predetermined, and exogenous declarations. Setting $\rho=0$ yields the static-panel
core; the role declarations and lag windows determine the dynamic-GMM instrument design.

First differencing removes the time-invariant unit effect:
\begin{{equation}}
\label{{eq:first-difference}}
\Delta y_{{it}}
= \rho\,\Delta y_{{i,t-1}}
+ \Delta\mathbf{{x}}_{{it}}^\top\boldsymbol{{\beta}}
+ \Delta\tau_t + \Delta\varepsilon_{{it}}.
\end{{equation}}
For a variable $z$ assigned a GMM-style role, Difference GMM uses level instruments
whose admissible lags are recorded explicitly by the role- or variable-specific set
$\mathcal{{L}}_z^D$:
\begin{{equation}}
\label{{eq:difference-moments}}
\operatorname{{E}}\!\left[z_{{i,t-s}}\,\Delta\varepsilon_{{it}}\right]=0,
\qquad s\in\mathcal{{L}}_z^D.
\end{{equation}}
For the lagged dependent variable, the conventional lower bound is two. System GMM
stacks Equation~\ref{{eq:first-difference}} with the level equation and, under the
additional initial-condition restrictions of \citet{{blundell1998initial}}, admits
level-equation moments of the form
\begin{{equation}}
\label{{eq:system-moments}}
\operatorname{{E}}\!\left[\Delta z_{{i,t-1}}
  \left(\alpha_i+\varepsilon_{{it}}\right)\right]=0.
\end{{equation}}
Thus the implementation constructs $Z_i$ from declared roles and lag windows rather
than silently selecting instruments. With $\boldsymbol{{\theta}}=(\rho,\boldsymbol{{\beta}}^\top)^\top$,
the one- or two-step estimator minimizes
\begin{{equation}}
\label{{eq:gmm-objective}}
\begin{{aligned}}
\mathbf{{g}}_N(\boldsymbol{{\theta}})
  &= \frac{{1}}{{N}}\sum_{{i=1}}^N Z_i^\top
     \mathbf{{u}}_i(\boldsymbol{{\theta}}), \\
\widehat{{\boldsymbol{{\theta}}}}
  &= \underset{{\boldsymbol{{\theta}}}}{{\operatorname{{arg\,min}}}}\;
     \mathbf{{g}}_N(\boldsymbol{{\theta}})^\top
     \widehat{{W}}_N
     \mathbf{{g}}_N(\boldsymbol{{\theta}}).
\end{{aligned}}
\end{{equation}}
For two-step estimation, $\widehat{{W}}_N$ is updated from first-step residual moments;
the Windmeijer adjustment changes the reported finite-sample covariance, not the point
estimate. For an overidentified model with $q$ instruments and $k$ estimated parameters,
the robust Hansen statistic is
\begin{{equation}}
\label{{eq:hansen}}
J_N
= N\,\mathbf{{g}}_N(\widehat{{\boldsymbol{{\theta}}}})^\top
  \widehat{{W}}_N
  \mathbf{{g}}_N(\widehat{{\boldsymbol{{\theta}}}})
\;\overset{{a}}{{\sim}}\;\chi^2_{{q-k}}.
\end{{equation}}
This reference distribution requires valid moment conditions and regularity conditions.
Accordingly, Hansen non-rejection and AR(2) non-rejection are reported as diagnostics,
not treated as proofs of identification.

\section{{Reproducible output workflow}}
All tables and figures in this manuscript are generated from machine-readable artifacts. \pkg{{Universal Output
Hub}} 0.2.4 is the single manuscript table exporter. The numerical chain is raw or controlled data, executable
model code, normalized CSV or release certificate, OutputHub LaTeX fragment or scripted figure, and finally
this document. All stochastic procedures use the fixed seed 20260724. Debug output,
row-level panel previews, API snapshots, smoke-test status tables, duplicate manual renderings, and stale
deterministic target-lag results are retained outside the manuscript or excluded entirely.

\section{{Leakage-controlled N-CMAPSS application}}
The N-CMAPSS DS01 development data are used as a compact application of panel preparation and late-cycle
validation. Remaining useful life decreases deterministically with cycle, so including lagged RUL---or the
derived lagged risk proxy---creates a tautological prediction problem. The revised design removes those target
lags. It retains a lagged-sensor OLS baseline and adds a nonlinear direct sensor model whose scaler, principal
components, and tuning are fitted only on training windows (Table~\ref{{tab:application-design}}).

Let $\mathbf{{s}}_{{it}}$ denote the raw sensor vector and let $\mathcal{{P}}_\mathcal{{T}}$
denote scaling followed by principal-component analysis fitted only on training window
$\mathcal{{T}}$. The nonlinear predictor used in the final holdout comparison is
\begin{{equation}}
\label{{eq:ncmapss-predictor}}
\begin{{aligned}}
\mathbf{{q}}_{{it}} &= \mathcal{{P}}_\mathcal{{T}}(\mathbf{{s}}_{{it}}), \\
\widehat{{r}}_{{it}}
  &= f_{{\widehat{{\eta}}}}\!\left(
     \mathbf{{q}}_{{it}},\mathbf{{q}}_{{i,t-1}},
     \Delta\mathbf{{q}}_{{it}},\overline{{\mathbf{{q}}}}_{{it}}^{{(3)}}
     \right),
\end{{aligned}}
\end{{equation}}
where $r_{{it}}$ is the risk proxy and $f_{{\widehat{{\eta}}}}$ is the selected random
forest. Equation~\ref{{eq:ncmapss-predictor}} contains no cycle, lagged RUL, or lagged
risk term and is a predictive mapping rather than a structural or causal equation.

{tables["design"]}

Table~\ref{{tab:application-estimates}} reports pooled and unit fixed-effects baselines. The lagged sensor-state
coefficient is positive in both models (0.032 and 0.028) and is distinguishable from zero at the 5 percent level.
The health-setting coefficient is negative and stable across specifications. By contrast, the flow-control
coefficient is positive in pooled OLS but becomes small and statistically indistinguishable from zero after unit
effects are introduced. In-sample fit rises only modestly, from 0.584 to 0.604, which is consistent with some
unit heterogeneity but does not establish predictive generalization.

{tables["application"]}

\FloatBarrier

The late-cycle comparison withholds cycles 71--100 (Table~\ref{{tab:holdout}}). The pooled lagged-sensor baseline
has RMSE {pooled_holdout["rmse"]:.3f} and out-of-sample $R^2$ {pooled_holdout["r2"]:.3f}; its squared error exceeds
that of a constant benchmark equal to the observed holdout mean. The direct random forest instead attains RMSE
{direct_holdout["rmse"]:.3f}, MAE {direct_holdout["mae"]:.3f}, SMAPE {direct_holdout["smape"]:.3f}, and $R^2$
{direct_holdout["r2"]:.3f}. Candidate selection uses three expanding windows entirely within cycles 1--70, and
the scaler and PCA are refitted in every training window before the final outer evaluation. The improvement is
predictive evidence for this split, not a causal claim or proof that late-life distribution shift is absent.

{tables["holdout"]}

\FloatBarrier

\section{{Controlled dynamic-GMM results}}
The controlled panel contains 120 units observed over ten periods. The data-generating coefficients are 0.55
for persistence, 0.35 for the predetermined regressor, and 0.25 for the exogenous regressor. Both estimators use
collapsed instruments and two-step covariance calculations. Instrument counts (five and eight) remain well
below the number of groups.

The exact controlled data-generating process is
\begin{{equation}}
\label{{eq:controlled-dgp}}
y_{{it}}
= 0.55y_{{i,t-1}} + 0.35x_{{it}}^{{\mathrm{{pred}}}}
+ 0.25x_{{it}}^{{\mathrm{{exog}}}}
+ \alpha_i + \tau_t + \varepsilon_{{it}}.
\end{{equation}}
The predetermined regressor depends on the previous-period disturbance but not the
current disturbance; the exogenous regressor is generated independently.

Difference GMM estimates the exogenous effect at 0.251, close to its generating value, while its persistence
estimate is 0.711 with a comparatively large standard error. System GMM estimates the exogenous effect at 0.242
but produces a higher persistence estimate (0.929) and a weak predetermined-regressor estimate (0.056). These
differences show why estimator choice cannot be reduced to in-sample precision. In this controlled realization,
System GMM is not uniformly closer to the generating parameters.

Both models show the expected first-order serial correlation after differencing and do not reject AR(2) at
conventional levels. Hansen p-values are 0.503 and 0.794. These diagnostics are compatible with the maintained
instrument design, but non-rejection is not proof of instrument exogeneity and a high Hansen p-value can be
uninformative when instruments proliferate \citep{{roodman2009xtabond2}}.

{tables["gmm"]}

\section{{Cross-software validation}}
The formal System GMM evidence in release 0.5.14 comprises six collapsed two-step specifications. Across them,
native and \proglang{{Stata}} results have identical observation, group, instrument, and over-identification counts. Maximum
absolute coefficient differences are below the registered $10^{{-6}}$ tolerances, and relative standard-error
differences remain within each specification's registered tolerance (Table~\ref{{tab:parity-parameters}}).
The unbalanced and variable-missing fixtures also match exact panel-time estimation-sample keys.

{tables["parity_params"]}

Table~\ref{{tab:parity-diagnostics}} separates numerical agreement from empirical adequacy. Baseline and
unbalanced designs do not reject the over-identifying restrictions at 5 percent, whereas several deliberately
maintained fixtures do. Those rejections are preserved because a parity test must reproduce the comparator's
result even when the specification would not be selected for substantive use. AR(2) is not rejected in any of
the six registered specifications.

{tables["parity_diag"]}

Static reference checks tell a similarly qualified story. OLS, pooled OLS, and fixed-effects results agree
numerically with aligned \proglang{{Python}}/\proglang{{R}} references and closely with \proglang{{Stata}} exports. Random-effects and 2SLS
coefficients also agree, but standard errors vary modestly under package-specific covariance conventions.
Table~\ref{{tab:static-reference}} therefore labels those rows as coefficient agreement rather than overstating
full covariance parity.

{tables["static"]}

\section{{Post-estimation, ML-style workflows, and automatic GMM search}}
The ML namespace is an orchestration layer around fitted econometric results. It supplies panel-aware splitting,
prediction metrics, model comparison, forecasting, and expanding-window backtesting. These tools help distinguish
estimation fit from predictive performance, but predictive accuracy does not create causal identification
\citep{{roberts2017crossvalidation,bergmeir2018note,cerqueira2019evaluating}}.

The automatic GMM search layer explores user-declared Difference/System GMM candidates over lag windows,
transformation, estimation step, collapse choice, and related options. Candidate ranking occurs only after
diagnostic gates for convergence, AR(2), Hansen behavior, and instrument proliferation. This design reduces
mechanical specification shopping, but it cannot supply substantive exclusion restrictions or decide which
moment conditions are credible. The final specification remains a research decision.

For the executed strict-policy search, the diagnostic filter and predictive selection
can be summarized as
\begin{{equation}}
\label{{eq:auto-search}}
\begin{{aligned}}
\mathcal{{A}}
  &= \left\{{m\in\mathcal{{M}}:\,
     \mathrm{{fit}}_m=\mathrm{{ok}},\,
     0.05<p_{{H,m}}<0.99,\,
     p_{{\mathrm{{AR}}(2),m}}>0.05,\,
     j_m\le n_m\right\}}, \\
\widehat{{m}}
  &= \underset{{m\in\mathcal{{A}}}}{{\operatorname{{arg\,min}}}}\;
     \operatorname{{RMSE}}_m.
\end{{aligned}}
\end{{equation}}
Here $j_m$ and $n_m$ are the instrument and group counts. Missing required diagnostics
exclude a candidate under the strict policy. These thresholds are configurable API
defaults and should not be interpreted as universal statistical decision rules.

{tables["auto_search"]}

The executed four-candidate search selects the System GMM 2:2 lag window. Its cycle-ordered holdout RMSE is
0.602 and its out-of-sample $R^2$ is 0.923. The System GMM 2:3 candidate is also admissible and performs
similarly, while the admissible Difference GMM 2:3 candidate has a markedly larger RMSE of 1.382. The
Difference GMM 2:2 candidate is rejected by the strict gate because its exactly identified design does not
provide a Hansen test. This is a policy choice for comparable diagnostic screening, not evidence that every
exactly identified model is intrinsically invalid.

A repository-only comparison artifact places this selected candidate beside external \proglang{{Python}}
predictive baselines on the identical final-two-period holdout. The \pkg{{statsmodels}} OLS baseline records
RMSE {statsmodels_ml["rmse"]:.3f} and $R^2$ {statsmodels_ml["r2"]:.3f}; the
\pkg{{scikit-learn}} random forest records RMSE {sklearn_ml["rmse"]:.3f} and $R^2$
{sklearn_ml["r2"]:.3f}. The artifact is not reproduced as a manuscript table. It checks temporal-split and
predictive-metric behavior only, not estimator parity, Hansen/AR agreement, or causal identification.

\begin{{figure}}[t!]
\centering
\includegraphics[width=0.88\textwidth]{{figures/01_auto_gmm_search_holdout.pdf}}
\caption{{\label{{fig:auto-search}} Cycle-ordered holdout error for the four automatic GMM-search candidates.
Source: Author's computation from the executed search in Table~\ref{{tab:auto-search}}. The gray candidate
failed the strict diagnostic-availability gate; lower RMSE is
better, and predictive ranking does not establish causal identification.}}
\end{{figure}}

{tables["workflow"]}

\section{{Limitations}}
The N-CMAPSS illustration has only six units after processing and is too small to serve as a formal dynamic-GMM
application. It is retained to demonstrate leakage control and honest temporal validation. The controlled GMM
exercise is synthetic and establishes workflow behavior, not external validity. Cross-software certificates are
specification-specific, and their tolerances, samples, comparator versions, and provenance must accompany any
parity claim. Finally, no diagnostic or automated search rule can replace an argument for identification.

% AUTHOR-LED SECTION: add the field-specific literature synthesis, substantive application
% motivation, broader interpretation, and final conclusion here after independent reading.

\section{{Availability and reproducibility}}
The source code and release evidence are available from the project repository under the MIT license. The
separate JOSS paper remains in \code{{paper/paper.md}}. This JSS manuscript and its OutputHub-generated tables
live only in \code{{paper\_jss/}}. Running \code{{run\_all.py}} in open mode
recreates data products, model outputs, comparisons, all nine tables, the figure, the manuscript PDF, logs,
checksums, and the reproducibility manifest. The build refuses to run unless the installed package is exactly
version 1.0.0 and the table exporter is exactly \pkg{{Universal Output Hub}} 0.2.4. The six-specification parity
tables are read from the signed \code{{v0.5.14}} Git tag rather than from mutable development artifacts.
The portable manual Stata script and the repository-only external Python comparison are retained under
\code{{replication/scripts/}} with machine-readable outputs for future independent review.

\section*{{AI assistance disclosure}}
Generative AI tools assisted with software workflow planning, code review, table-pipeline construction, and
drafting/editing of technical prose. The author is responsible for verifying every result, revising the text,
completing the literature-led discussion, and ensuring that the submitted manuscript satisfies journal policy.

\bibliography{{../paper/paper}}

\end{{document}}
"""


def main() -> int:
    _require_release()
    _clear_generated_tables()
    _application_design_table()
    _application_estimates_table()
    _holdout_table()
    _controlled_gmm_table()
    _certificate_tables()
    _static_reference_table()
    _auto_search_table()
    _workflow_table()

    if TABLE_CAPTION_SOURCES.keys() != TABLE_SOURCES.keys():
        raise RuntimeError("Every table source needs matching print-caption provenance.")
    expected = sorted(TABLE_SOURCES)
    missing = [name for name in expected if not (TABLE_DIR / name).exists()]
    if missing:
        raise RuntimeError(f"OutputHub did not generate required LaTeX tables: {missing}")

    PAPER_DIR.mkdir(parents=True, exist_ok=True)
    (PAPER_DIR / "main.tex").write_text(_build_main_tex(), encoding="utf-8")
    manifest = {
        "status": "ok",
        "generated_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "systemgmmkit_version": sgk.__version__,
        "systemgmmkit_release_tag": TARGET_TAG,
        "systemgmmkit_release_commit": _release_commit(),
        "universal_output_hub_version": importlib.metadata.version("universal-output-hub"),
        "manuscript": "paper_jss/main.tex",
        "table_exporter": "Universal Output Hub",
        "tables": expected,
        "figures": ["paper_jss/figures/01_auto_gmm_search_holdout.pdf"],
        "equations": [
            "eq:dynamic-panel",
            "eq:first-difference",
            "eq:difference-moments",
            "eq:system-moments",
            "eq:gmm-objective",
            "eq:hansen",
            "eq:ncmapss-predictor",
            "eq:controlled-dgp",
            "eq:auto-search",
        ],
        "table_sources": TABLE_SOURCES,
        "excluded_from_manuscript": [
            "authors table",
            "API snapshot",
            "row-level N-CMAPSS panel dump",
            "stale lagged-risk perfect-prediction tables",
            "manual duplicate of OutputHub tables",
            "raw Stata coefficient dumps",
            "debug and smoke-status tables",
            "instrument-matrix probe tables",
        ],
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
