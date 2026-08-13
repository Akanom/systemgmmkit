from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_PATH = PROJECT_ROOT / "data" / "external" / "ncmapss" / "ncmapss_ds01_dev_unit_cycle_panel.csv"
OUT_DIR = PROJECT_ROOT / "results" / "raw" / "systemgmmkit" / "ncmapss"
ARTIFACT_TABLES = PROJECT_ROOT / "artifacts" / "joss" / "tables"

ENTITY = "unit"
TIME = "cycle"
TARGET = "risk"
HOLDOUT_TEST_UNITS = 2
RANDOM_SEED = 20260724
INNER_FOLDS = ((40, 41, 50), (50, 51, 60), (60, 61, 70))

OUT_DIR.mkdir(parents=True, exist_ok=True)
ARTIFACT_TABLES.mkdir(parents=True, exist_ok=True)


def smape(y_true, y_pred) -> float:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    denom = np.abs(y_true) + np.abs(y_pred)
    mask = denom != 0
    if not mask.any():
        return float("nan")
    return float(np.mean(2.0 * np.abs(y_pred[mask] - y_true[mask]) / denom[mask]))


def tidy_statsmodels_result(result, model_name: str) -> pd.DataFrame:
    out = pd.DataFrame(
        {
            "term": result.params.index,
            "coefficient": result.params.values,
            "std_error": result.bse.values,
            "t_value": result.tvalues.values,
            "p_value": result.pvalues.values,
        }
    )
    out.insert(0, "model", model_name)
    return out


def model_metrics(y_true, y_pred, model_name: str, validation_design: str) -> dict:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    rmse = float(mean_squared_error(y_true, y_pred) ** 0.5)
    mae = float(mean_absolute_error(y_true, y_pred))
    r2 = float(r2_score(y_true, y_pred))

    return {
        "model": model_name,
        "validation_design": validation_design,
        "n_eval": int(len(y_true)),
        "rmse": float(rmse),
        "mae": float(mae),
        "smape": smape(y_true, y_pred),
        "r2": float(r2),
    }


def prepare_ncmapss_gmm_spec(
    df: pd.DataFrame,
    target_col: str = "RUL",
    is_dynamic_target: bool = False,
) -> tuple[pd.DataFrame, list[str]]:
    df = df.sort_values([ENTITY, TIME]).copy()

    deterministic_cols = [
        TIME,
        "max_cycle",
        "total_cycles",
        "unit_lifetime",
    ]
    drop_list = [c for c in deterministic_cols if c in df.columns]

    if is_dynamic_target and target_col == "RUL":
        raise ValueError(
            "Lagged RUL (RUL_{t-1}) forms an exact deterministic identity: "
            "RUL_t = RUL_{t-1} - 1. "
            "To test dynamic models on this workflow, use a sensor-stochastic proxy "
            "such as degradation_index or sensor features instead."
        )

    if target_col not in df.columns:
        raise KeyError(f"Missing target column: {target_col}")

    # Prefer sensor-like raw channels when available; otherwise use all numeric
    # non-identifier columns.
    # Keep the interpretable OLS baseline compact. The nonlinear direct model
    # below uses the raw physical sensor aggregates through a train-fitted PCA.
    sensor_cols = ["sensor_mean_z"] if "sensor_mean_z" in df.columns else []

    if not sensor_cols:
        sensor_cols = [c for c in df.columns if c.startswith(("s_", "w_", "sensor"))]

    if not sensor_cols:
        sensor_cols = [
            c
            for c in df.columns
            if c not in {ENTITY, TIME, target_col, "rul", "RUL", *drop_list}
            and pd.api.types.is_numeric_dtype(df[c])
        ]

    if not sensor_cols:
        raise ValueError(
            "No dynamic numeric features found to build lag matrix for ds01 smoke workflow."
        )

    for col in sensor_cols:
        df[f"L1_{col}"] = df.groupby(ENTITY)[col].shift(1)

    lag_cols = [f"L1_{c}" for c in sensor_cols]
    return df, lag_cols


def prepare_data() -> tuple[pd.DataFrame, list[str]]:
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Missing processed panel file: {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)

    required = [
        ENTITY,
        TIME,
        TARGET,
        "degradation_index",
        "sensor_mean_z",
        "pc2",
        "op_setting1",
        "op_setting2",
        "op_setting3",
        "op_setting4",
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise KeyError(f"Missing required columns: {missing}")

    df, lag_cols = prepare_ncmapss_gmm_spec(df, target_col=TARGET, is_dynamic_target=True)

    # Standardize lagged predictors for numerical stability.
    model_terms: list[str] = []
    for c in lag_cols:
        if c not in df.columns:
            continue
        std = df[c].std(ddof=0)
        if std == 0 or np.isnan(std):
            df[f"z_{c}"] = 0.0
        else:
            df[f"z_{c}"] = (df[c] - df[c].mean()) / std
        model_terms.append(f"z_{c}")

    # Include Fc and hs as additional standardized controls.
    for raw_col in ["Fc", "hs"]:
        if raw_col not in df.columns:
            df[raw_col] = 0
        std_raw = df[raw_col].std(ddof=0)
        df[f"z_{raw_col}"] = (
            0.0
            if (std_raw == 0 or np.isnan(std_raw))
            else (df[raw_col] - df[raw_col].mean()) / std_raw
        )
        model_terms.append(f"z_{raw_col}")

    df = df.dropna(subset=[TARGET] + [c for c in model_terms]).copy()
    return df, model_terms


def write_panel_summary(df: pd.DataFrame) -> None:
    summary = {
        "dataset": "N-CMAPSS DS01 dev unit-cycle panel",
        "rows_after_lag": int(len(df)),
        "n_units": int(df[ENTITY].nunique()),
        "min_cycle": int(df[TIME].min()),
        "max_cycle": int(df[TIME].max()),
        "duplicate_unit_cycle_rows": int(df.duplicated([ENTITY, TIME]).sum()),
        "dependent_variable": TARGET,
        "entity_index": ENTITY,
        "time_index": TIME,
    }

    summary_path = OUT_DIR / "ncmapss_model_panel_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    pd.DataFrame([summary]).to_csv(
        ARTIFACT_TABLES / "01_ncmapss_model_panel_summary.csv",
        index=False,
    )

    print(json.dumps(summary, indent=2))


def run_models(df: pd.DataFrame, model_terms: list[str]) -> None:
    if not model_terms:
        raise ValueError("No lag-based model terms available for model fit.")

    base_rhs = " + ".join(model_terms)
    pooled_formula = f"{TARGET} ~ {base_rhs}"
    fe_formula = f"{TARGET} ~ {base_rhs} + C(unit)"

    print("[INFO] Running pooled dynamic OLS (lag-based features)")
    pooled = smf.ols(pooled_formula, data=df).fit(cov_type="HC1")

    print("[INFO] Running unit fixed-effects dynamic OLS")
    fe = smf.ols(fe_formula, data=df).fit(cov_type="HC1")

    pooled_tidy = tidy_statsmodels_result(pooled, "pooled_dynamic_ols")
    fe_tidy = tidy_statsmodels_result(fe, "unit_fe_dynamic_ols")

    model_table = pd.concat([pooled_tidy, fe_tidy], ignore_index=True)

    model_table.to_csv(OUT_DIR / "ncmapss_dynamic_ols_results.csv", index=False)
    model_table.to_csv(ARTIFACT_TABLES / "02_ncmapss_dynamic_ols_results.csv", index=False)

    fit_summary = pd.DataFrame(
        [
            {
                "model": "pooled_dynamic_ols",
                "n_obs": int(pooled.nobs),
                "r2": float(pooled.rsquared),
                "adj_r2": float(pooled.rsquared_adj),
                "aic": float(pooled.aic),
                "bic": float(pooled.bic),
            },
            {
                "model": "unit_fe_dynamic_ols",
                "n_obs": int(fe.nobs),
                "r2": float(fe.rsquared),
                "adj_r2": float(fe.rsquared_adj),
                "aic": float(fe.aic),
                "bic": float(fe.bic),
            },
        ]
    )

    fit_summary.to_csv(OUT_DIR / "ncmapss_dynamic_ols_fit_summary.csv", index=False)
    fit_summary.to_csv(ARTIFACT_TABLES / "03_ncmapss_dynamic_ols_fit_summary.csv", index=False)

    print("[INFO] Wrote OLS model outputs")


def _unit_holdout_split(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, list[int]]:
    units = sorted(df[ENTITY].dropna().astype(int).unique())
    if len(units) < 2:
        raise ValueError("Need at least two units for a unit-level holdout check.")

    n_test = min(max(1, HOLDOUT_TEST_UNITS), max(1, len(units) - 1))
    test_units = [int(u) for u in units[-n_test:]]
    test_mask = df[ENTITY].isin(test_units)
    train = df.loc[~test_mask].copy()
    test = df.loc[test_mask].copy()

    if train.empty or test.empty:
        raise ValueError("Unit holdout split produced empty train or test frame.")

    return train, test, test_units


def _cycle_holdout_split(df: pd.DataFrame, cutoff: int = 70) -> tuple[pd.DataFrame, pd.DataFrame]:
    train = df.loc[df[TIME] <= cutoff].copy()
    test = df.loc[df[TIME] > cutoff].copy()

    if train.empty or test.empty:
        raise ValueError("Cycle holdout split produced empty train or test frame.")

    return train, test


def _raw_sensor_columns(df: pd.DataFrame) -> list[str]:
    columns = [
        column
        for column in df.columns
        if column.startswith("sensor_") and column != "sensor_mean_z"
    ]
    if len(columns) < 4:
        raise ValueError(
            "The direct sensor model requires at least four raw N-CMAPSS sensor aggregates."
        )
    return columns


def _pca_dynamic_features(
    df: pd.DataFrame,
    *,
    fit_cutoff: int,
    n_components: int,
    design: str,
) -> tuple[pd.DataFrame, list[str], float]:
    """Build sensor-state features without fitting preprocessing on future cycles."""
    sensors = _raw_sensor_columns(df)
    fit_mask = df[TIME] <= fit_cutoff
    if not fit_mask.any():
        raise ValueError(f"No rows available at or before cycle {fit_cutoff}.")

    raw = df[sensors].replace([np.inf, -np.inf], np.nan)
    if raw.isna().any().any():
        raise ValueError("Raw sensor aggregates contain missing or non-finite values.")

    scaler = StandardScaler().fit(raw.loc[fit_mask])
    scaled = scaler.transform(raw)
    pca = PCA(n_components=n_components, random_state=RANDOM_SEED).fit(scaled[fit_mask])
    scores = pca.transform(scaled)

    engineered = df[[ENTITY, TIME, TARGET]].copy()
    current: list[str] = []
    lagged: list[str] = []
    changes: list[str] = []
    rolling: list[str] = []
    for component in range(n_components):
        name = f"sensor_pc{component + 1}"
        engineered[name] = scores[:, component]
        engineered[f"L1_{name}"] = engineered.groupby(ENTITY)[name].shift(1)
        engineered[f"D1_{name}"] = engineered[name] - engineered[f"L1_{name}"]
        engineered[f"R3_{name}"] = engineered.groupby(ENTITY)[name].transform(
            lambda values: values.rolling(3, min_periods=2).mean()
        )
        current.append(name)
        lagged.append(f"L1_{name}")
        changes.append(f"D1_{name}")
        rolling.append(f"R3_{name}")

    if design == "current":
        features = current
    elif design == "dynamic":
        features = current + lagged + changes + rolling
    else:
        raise ValueError(f"Unknown direct-model feature design: {design}")

    engineered = engineered.dropna(subset=features + [TARGET]).copy()
    explained_variance = float(pca.explained_variance_ratio_.sum())
    return engineered, features, explained_variance


def _select_direct_sensor_model(df: pd.DataFrame) -> tuple[dict, pd.DataFrame]:
    """Select the nonlinear direct model using expanding windows inside cycles 1--70."""
    scores: dict[tuple[int, str, int, float], list[float]] = {}
    pca_variance: dict[tuple[int, str, int, float], list[float]] = {}
    for train_end, validation_start, validation_end in INNER_FOLDS:
        for n_components in (2, 3, 4, 5, 6, 8):
            for design in ("current", "dynamic"):
                frame, features, explained = _pca_dynamic_features(
                    df,
                    fit_cutoff=train_end,
                    n_components=n_components,
                    design=design,
                )
                train = frame.loc[frame[TIME] <= train_end]
                validation = frame.loc[
                    (frame[TIME] >= validation_start) & (frame[TIME] <= validation_end)
                ]
                for min_leaf in (2, 4, 8):
                    for max_features in (0.8, 1.0):
                        key = (n_components, design, min_leaf, max_features)
                        model = RandomForestRegressor(
                            n_estimators=150,
                            min_samples_leaf=min_leaf,
                            max_features=max_features,
                            random_state=RANDOM_SEED,
                            n_jobs=-1,
                        )
                        model.fit(train[features], train[TARGET])
                        prediction = model.predict(validation[features])
                        fold_rmse = float(mean_squared_error(validation[TARGET], prediction) ** 0.5)
                        scores.setdefault(key, []).append(fold_rmse)
                        pca_variance.setdefault(key, []).append(explained)

    rows = []
    for candidate_id, (key, fold_scores) in enumerate(sorted(scores.items()), start=1):
        n_components, design, min_leaf, max_features = key
        rows.append(
            {
                "candidate_id": candidate_id,
                "n_components": n_components,
                "feature_design": design,
                "min_samples_leaf": min_leaf,
                "max_features": max_features,
                "fold_1_rmse": fold_scores[0],
                "fold_2_rmse": fold_scores[1],
                "fold_3_rmse": fold_scores[2],
                "mean_rmse": float(np.mean(fold_scores)),
                "max_rmse": float(np.max(fold_scores)),
                "mean_pca_variance": float(np.mean(pca_variance[key])),
            }
        )
    selection = pd.DataFrame(rows).sort_values(
        ["mean_rmse", "max_rmse", "n_components", "candidate_id"],
        kind="mergesort",
    )
    selection["selected"] = False
    selection.loc[selection.index[0], "selected"] = True
    best = selection.iloc[0].to_dict()
    return best, selection.sort_values("candidate_id").reset_index(drop=True)


def run_holdout_forecast(df: pd.DataFrame, model_terms: list[str]) -> None:
    base_rhs = " + ".join(model_terms)
    formula = f"{TARGET} ~ {base_rhs}"

    # Use cycle-based holdout for this smoke regression diagnostic to avoid
    # leaking future-cycle information while keeping a stable publication-ready
    # train/test partition used by the manuscript workflow.
    train, test = _cycle_holdout_split(df, cutoff=70)
    validation_design = "time_holdout_train_cycle_le_70"

    print(
        f"[INFO] Running cycle-ordered holdout forecast: train_n={len(train)}, test_n={len(test)}"
    )

    model = smf.ols(formula, data=train).fit(cov_type="HC1")
    ols_prediction = model.predict(test)

    ols_metrics = model_metrics(
        y_true=test[TARGET],
        y_pred=ols_prediction,
        model_name="pooled_dynamic_ols",
        validation_design=validation_design,
    )
    for key, value in {
        "train_rows": int(len(train)),
        "test_rows": int(len(test)),
        "train_max_cycle": int(train[TIME].max()),
        "test_min_cycle": int(test[TIME].min()),
        "test_max_cycle": int(test[TIME].max()),
    }.items():
        ols_metrics[key] = value

    direct_source = pd.read_csv(DATA_PATH).sort_values([ENTITY, TIME]).reset_index(drop=True)
    best, selection = _select_direct_sensor_model(direct_source)
    n_components = int(best["n_components"])
    design = str(best["feature_design"])
    min_leaf = int(best["min_samples_leaf"])
    max_features = float(best["max_features"])
    direct_frame, direct_features, explained = _pca_dynamic_features(
        direct_source,
        fit_cutoff=70,
        n_components=n_components,
        design=design,
    )
    direct_train, direct_test = _cycle_holdout_split(direct_frame, cutoff=70)
    direct_model = RandomForestRegressor(
        n_estimators=600,
        min_samples_leaf=min_leaf,
        max_features=max_features,
        random_state=RANDOM_SEED,
        n_jobs=-1,
    )
    direct_model.fit(direct_train[direct_features], direct_train[TARGET])
    direct_prediction = direct_model.predict(direct_test[direct_features])
    direct_metrics = model_metrics(
        y_true=direct_test[TARGET],
        y_pred=direct_prediction,
        model_name="direct_sensor_random_forest",
        validation_design=("expanding_window_selection_within_cycles_1_70_then_test_71_100"),
    )
    for key, value in {
        "train_rows": int(len(direct_train)),
        "test_rows": int(len(direct_test)),
        "train_max_cycle": int(direct_train[TIME].max()),
        "test_min_cycle": int(direct_test[TIME].min()),
        "test_max_cycle": int(direct_test[TIME].max()),
    }.items():
        direct_metrics[key] = value

    metrics_df = pd.DataFrame([ols_metrics, direct_metrics])

    ols_predictions = test[[ENTITY, TIME, TARGET]].copy()
    ols_predictions.insert(0, "model", "pooled_dynamic_ols")
    ols_predictions["prediction"] = ols_prediction
    ols_predictions["error"] = ols_predictions["prediction"] - ols_predictions[TARGET]
    direct_predictions = direct_test[[ENTITY, TIME, TARGET]].copy()
    direct_predictions.insert(0, "model", "direct_sensor_random_forest")
    direct_predictions["prediction"] = direct_prediction
    direct_predictions["error"] = direct_predictions["prediction"] - direct_predictions[TARGET]
    pred_df = pd.concat([ols_predictions, direct_predictions], ignore_index=True)

    metrics_df.to_csv(OUT_DIR / "ncmapss_holdout_metrics.csv", index=False)
    metrics_df.to_csv(ARTIFACT_TABLES / "04_ncmapss_holdout_metrics.csv", index=False)

    pred_df.to_csv(OUT_DIR / "ncmapss_holdout_predictions.csv", index=False)

    selection.to_csv(OUT_DIR / "ncmapss_direct_sensor_model_selection.csv", index=False)
    selection.to_csv(ARTIFACT_TABLES / "06_ncmapss_direct_sensor_model_selection.csv", index=False)
    status = {
        "status": "PASS",
        "selection_boundary": "cycles 1--70 only",
        "outer_test_boundary": "cycles 71--100",
        "inner_folds": [list(fold) for fold in INNER_FOLDS],
        "random_seed": RANDOM_SEED,
        "raw_sensor_columns": _raw_sensor_columns(direct_source),
        "selected_candidate": {
            "candidate_id": int(best["candidate_id"]),
            "n_components": n_components,
            "feature_design": design,
            "min_samples_leaf": min_leaf,
            "max_features": max_features,
            "mean_inner_rmse": float(best["mean_rmse"]),
            "max_inner_rmse": float(best["max_rmse"]),
            "outer_train_pca_variance": explained,
        },
        "outer_metrics": direct_metrics,
    }
    status_text = json.dumps(status, indent=2)
    (OUT_DIR / "ncmapss_direct_sensor_model_status.json").write_text(status_text, encoding="utf-8")
    (ARTIFACT_TABLES / "07_ncmapss_direct_sensor_model_status.json").write_text(
        status_text, encoding="utf-8"
    )

    print("[INFO] Wrote holdout metrics, predictions, and train-only model selection")
    print(metrics_df.to_string(index=False))


def write_model_specification() -> None:
    spec = {
        "dataset": "N-CMAPSS DS01 dev unit-cycle panel",
        "entity": ENTITY,
        "time": TIME,
        "dependent": TARGET,
        "structural_model": "risk_it = beta' * (state features)_i,t-1 + unit_effect_i + error_it",
        "dynamic_gmm_role_suggestion": {
            "endogenous": ["lagged state features"],
            "predetermined": [
                "degradation_index",
                "sensor_mean_z",
                "pc2",
                "op_setting1",
                "op_setting2",
                "op_setting3",
                "op_setting4",
                "Fc",
                "hs",
            ],
            "exogenous": ["unit", "time"],
            "recommended_gmm_lags": {
                "state_features": "1",
            },
            "collapse_instruments": True,
            "note": (
                "Risk in this DS01 workflow is derived from RUL and highly deterministic by cycle. "
                "Lagged risk is intentionally excluded from dynamic OLS smoke testing."
            ),
        },
        "direct_sensor_model": {
            "purpose": "non-causal direct risk prediction from observed sensor state",
            "preprocessing": ("StandardScaler and PCA fitted only inside each training window"),
            "features": (
                "current sensor PCs, one-cycle lags, first differences, and three-cycle means"
            ),
            "selection": "expanding-window RMSE within cycles 1--70",
            "outer_test": "cycles 71--100 used once after selection",
            "estimator": "RandomForestRegressor",
            "seed": RANDOM_SEED,
        },
    }

    out = OUT_DIR / "ncmapss_statistical_model_specification.json"
    out.write_text(json.dumps(spec, indent=2), encoding="utf-8")

    artifact = ARTIFACT_TABLES / "05_ncmapss_statistical_model_specification.json"
    artifact.write_text(json.dumps(spec, indent=2), encoding="utf-8")

    print("[INFO] Wrote statistical model specification")


def main() -> None:
    df, model_terms = prepare_data()

    write_panel_summary(df)
    write_model_specification()
    run_models(df, model_terms)
    run_holdout_forecast(df, model_terms)

    print("[DONE] N-CMAPSS DS01 smoke modelling complete.")


if __name__ == "__main__":
    main()
