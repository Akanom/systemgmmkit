"""Fail the replication run when manuscript outputs or claim gates are incomplete."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[3]
EXPECTED = ROOT / "replication" / "expected_outputs.yml"
REPORT = ROOT / "artifacts" / "jss" / "reproducibility" / "verification_report.json"


def _row_count(path: Path) -> int | None:
    if path.suffix.lower() in {".csv", ".txt"}:
        try:
            return int(len(pd.read_csv(path)))
        except Exception:
            return None
    if path.suffix.lower() == ".json":
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            return len(payload) if isinstance(payload, list) else 1
        except Exception:
            return None
    return int(path.stat().st_size > 0)


def _check_expected(item: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    relative = str(item["path"])
    path = ROOT / relative
    if not path.exists():
        return [f"missing: {relative}"]
    if path.is_dir():
        return [f"expected file but found directory: {relative}"]

    minimum_size = item.get("minimum_size_bytes")
    if minimum_size is not None and path.stat().st_size < int(minimum_size):
        failures.append(f"too small: {relative} ({path.stat().st_size} < {minimum_size} bytes)")

    minimum_rows = item.get("minimum_rows")
    rows = _row_count(path)
    if minimum_rows is not None and (rows is None or rows < int(minimum_rows)):
        failures.append(f"too few rows: {relative} ({rows} < {minimum_rows})")

    required_columns = list(item.get("required_columns") or [])
    if required_columns:
        try:
            frame = pd.read_csv(path)
        except Exception as exc:
            failures.append(f"cannot read columns: {relative} ({exc})")
        else:
            missing = sorted(set(required_columns).difference(frame.columns))
            if missing:
                failures.append(f"missing columns: {relative} ({', '.join(missing)})")
            present = [column for column in required_columns if column in frame]
            null_columns = [column for column in present if frame[column].isna().any()]
            if null_columns:
                failures.append(
                    f"null values in required columns: {relative} ({', '.join(null_columns)})"
                )
    return failures


def _semantic_checks() -> list[str]:
    failures: list[str] = []
    publication = json.loads(
        (ROOT / "paper_jss" / "publication_manifest.json").read_text(encoding="utf-8")
    )
    if publication.get("systemgmmkit_version") != "1.0.0":
        failures.append("publication manifest is not pinned to systemgmmkit 1.0.0")
    if publication.get("universal_output_hub_version") != "0.2.4":
        failures.append("publication manifest is not pinned to Universal Output Hub 0.2.4")

    controlled = json.loads(
        (ROOT / "artifacts" / "joss" / "tables" / "22_dynamic_gmm_parity_status.json").read_text(
            encoding="utf-8"
        )
    )
    if controlled.get("status") != "PASS" or controlled.get("systemgmmkit_version") != "1.0.0":
        failures.append("controlled Dynamic GMM status is not a passing 1.0.0 run")

    holdout = pd.read_csv(ROOT / "artifacts" / "joss" / "tables" / "04_ncmapss_holdout_metrics.csv")
    if holdout.empty or (holdout["rmse"] <= 0).any() or (holdout["r2"] >= 0.999999).any():
        failures.append("N-CMAPSS holdout still exhibits a perfect-prediction artifact")
    holdout = holdout.set_index("model")
    expected_models = {"pooled_dynamic_ols", "direct_sensor_random_forest"}
    if not expected_models.issubset(holdout.index):
        failures.append("N-CMAPSS holdout is missing the OLS baseline or direct sensor forest")
    else:
        pooled = holdout.loc["pooled_dynamic_ols"]
        direct = holdout.loc["direct_sensor_random_forest"]
        if float(direct["rmse"]) >= float(pooled["rmse"]):
            failures.append("direct sensor forest does not improve late-cycle RMSE")
        if float(direct["r2"]) <= 0:
            failures.append("direct sensor forest does not beat the outer-test mean benchmark")

    selection = pd.read_csv(
        ROOT / "artifacts" / "joss" / "tables" / "06_ncmapss_direct_sensor_model_selection.csv"
    )
    selected = selection.loc[selection["selected"].astype(str).str.lower().eq("true")]
    if len(selection) != 72 or len(selected) != 1:
        failures.append("direct sensor search must contain 72 candidates and one selected row")
    direct_status = json.loads(
        (
            ROOT / "artifacts" / "joss" / "tables" / "07_ncmapss_direct_sensor_model_status.json"
        ).read_text(encoding="utf-8")
    )
    if (
        direct_status.get("status") != "PASS"
        or direct_status.get("selection_boundary") != "cycles 1--70 only"
        or direct_status.get("outer_test_boundary") != "cycles 71--100"
    ):
        failures.append(
            "direct sensor model does not preserve the registered nested-validation boundary"
        )
    if len(direct_status.get("raw_sensor_columns", [])) < 4:
        failures.append("direct sensor model does not record its raw physical sensor inputs")

    search = pd.read_csv(ROOT / "results" / "comparisons" / "auto_gmm_search_results.csv")
    if len(search) != 4 or not search["valid"].astype(bool).any():
        failures.append("automatic GMM search lacks four candidates or a valid candidate")
    if search[["rmse", "r2", "ar2_p"]].isna().any().any():
        failures.append("automatic GMM search has missing required evaluation/AR(2) values")

    ml_comparison = pd.read_csv(
        ROOT / "results" / "comparisons" / "ml_external_python_comparison.csv"
    )
    required_packages = {"systemgmmkit", "statsmodels", "scikit-learn"}
    if len(ml_comparison) != 3 or set(ml_comparison["package"]) != required_packages:
        failures.append("external Python comparison lacks the three registered package rows")
    if ml_comparison[["rmse", "r2"]].isna().any().any():
        failures.append("external Python comparison has missing required predictive metrics")
    external = ml_comparison.loc[ml_comparison["package"].ne("systemgmmkit")]
    if external["diagnostics_applicable"].astype(bool).any():
        failures.append("predictive baselines incorrectly claim Dynamic GMM diagnostics")

    if (ROOT / "paper" / "main.tex").exists() or (ROOT / "paper" / "main.pdf").exists():
        failures.append("JOSS directory contains a LaTeX/PDF manuscript artifact")
    main_text = (ROOT / "paper_jss" / "main.tex").read_text(encoding="utf-8")
    if "\\documentclass[article]{jss}" not in main_text:
        failures.append("paper_jss/main.tex is not using the official JSS article class")
    if "\\begin{landscape}" in main_text or "\\begin{sidewaystable}" in main_text:
        failures.append("manuscript contains a landscape table")
    if main_text.count("\\input{tables/") != 9:
        failures.append("manuscript does not include exactly nine generated tables")
    required_equations = {
        "eq:dynamic-panel",
        "eq:first-difference",
        "eq:difference-moments",
        "eq:system-moments",
        "eq:gmm-objective",
        "eq:hansen",
        "eq:ncmapss-predictor",
        "eq:controlled-dgp",
        "eq:auto-search",
    }
    missing_equations = sorted(
        label for label in required_equations if f"\\label{{{label}}}" not in main_text
    )
    if missing_equations:
        failures.append(
            "paper_jss/main.tex is missing required equation labels: "
            + ", ".join(missing_equations)
        )
    manifest = json.loads(
        (ROOT / "paper_jss" / "publication_manifest.json").read_text(encoding="utf-8")
    )
    if set(manifest.get("equations", [])) != required_equations:
        failures.append("publication manifest does not register every manuscript equation")
    if "figures/01_auto_gmm_search_holdout.pdf" not in main_text:
        failures.append("automatic-search figure is not included in the manuscript")
    return failures


def main() -> int:
    config = yaml.safe_load(EXPECTED.read_text(encoding="utf-8"))
    failures: list[str] = []
    for item in config.get("required_outputs", []):
        failures.extend(_check_expected(item))
    failures.extend(_semantic_checks())

    payload = {
        "status": "PASS" if not failures else "FAIL",
        "checked_outputs": len(config.get("required_outputs", [])),
        "failures": failures,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
