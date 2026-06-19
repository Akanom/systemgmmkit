from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

BASE = Path("artifacts/parity/xtabond2")

SPECS = {
    "system_gmm_baseline_controls": {
        "data": BASE / "system_gmm_benchmark.csv",
        "params": BASE
        / "specs"
        / "system_gmm_baseline_controls"
        / "windmeijer"
        / "native_params.csv",
        "stata": BASE / "xtabond2_system_gmm_diagnostics.csv",
        "y": "y",
        "regressors": ["L1.y", "x", "w", "_con"],
    },
    "system_gmm_no_controls": {
        "data": BASE / "specs" / "system_gmm_no_controls" / "system_gmm_no_controls_benchmark.csv",
        "params": BASE / "specs" / "system_gmm_no_controls" / "native_params.csv",
        "stata": BASE / "specs" / "system_gmm_no_controls" / "stata_diagnostics.csv",
        "y": "y",
        "regressors": ["L1.y", "x", "_con"],
    },
    "system_gmm_three_way_controls": {
        "data": BASE
        / "specs"
        / "system_gmm_three_way_controls"
        / "system_gmm_three_way_controls_benchmark.csv",
        "params": BASE / "specs" / "system_gmm_three_way_controls" / "native_params.csv",
        "stata": BASE / "specs" / "system_gmm_three_way_controls" / "stata_diagnostics.csv",
        "y": "y",
        "regressors": [
            "L1.y",
            "x",
            "frag",
            "polity",
            "x_frag",
            "x_polity",
            "frag_polity",
            "x_frag_polity",
            "w",
            "_con",
        ],
    },
    "system_gmm_decomposition_controls": {
        "data": BASE
        / "specs"
        / "system_gmm_decomposition_controls"
        / "system_gmm_decomposition_controls_benchmark.csv",
        "params": BASE / "specs" / "system_gmm_decomposition_controls" / "native_params.csv",
        "stata": BASE / "specs" / "system_gmm_decomposition_controls" / "stata_diagnostics.csv",
        "y": "y",
        "regressors": ["L1.y", "x_long", "x_short", "w", "c1", "_con"],
    },
}


def _two_sided_p_from_z(z: float) -> float:
    return float(2.0 * stats.norm.sf(abs(float(z))))


def _abs_z_from_p(p: float) -> float:
    return float(stats.norm.isf(float(p) / 2.0))


def _load_beta(path: Path) -> dict[str, float]:
    df = pd.read_csv(path)
    return dict(zip(df["param"].astype(str), df["native_coef"].astype(float), strict=False))


def _level_residuals(
    df: pd.DataFrame, beta: dict[str, float], y: str, regressors: list[str]
) -> pd.DataFrame:
    d = df.sort_values(["id", "t"]).copy()
    d["L1.y"] = d.groupby("id")[y].shift(1)

    xb = np.zeros(len(d), dtype=float)

    for reg in regressors:
        if reg == "_con":
            xb += beta.get("_con", 0.0)
        else:
            if reg not in d.columns:
                raise KeyError(f"Missing regressor column {reg}")
            xb += beta.get(reg, 0.0) * d[reg].to_numpy(dtype=float)

    d["_level_resid"] = d[y].to_numpy(dtype=float) - xb
    d = d.dropna(subset=["_level_resid", "L1.y"]).copy()
    return d


def _fd_residuals(level_resid: pd.DataFrame) -> pd.DataFrame:
    d = level_resid.sort_values(["id", "t"]).copy()
    d["_fd_resid"] = d.groupby("id")["_level_resid"].diff()
    return d.dropna(subset=["_fd_resid"]).copy()


def _corr_z(d: pd.DataFrame, resid_col: str, lag: int) -> tuple[float | None, float | None, int]:
    x = d.sort_values(["id", "t"]).copy()
    x["_lag"] = x.groupby("id")[resid_col].shift(lag)
    x = x.dropna(subset=[resid_col, "_lag"])

    n = len(x)
    if n < 5:
        return None, None, n

    a = x[resid_col].to_numpy(dtype=float)
    b = x["_lag"].to_numpy(dtype=float)

    denom = float(np.sqrt(np.sum(a * a) * np.sum(b * b)))
    if denom <= 0:
        return None, None, n

    corr = float(np.sum(a * b) / denom)
    z = corr * np.sqrt(n)
    return z, _two_sided_p_from_z(z), n


def _raw_inner_z(
    d: pd.DataFrame, resid_col: str, lag: int
) -> tuple[float | None, float | None, int]:
    x = d.sort_values(["id", "t"]).copy()
    x["_lag"] = x.groupby("id")[resid_col].shift(lag)
    x = x.dropna(subset=[resid_col, "_lag"])

    n = len(x)
    if n < 5:
        return None, None, n

    a = x[resid_col].to_numpy(dtype=float)
    b = x["_lag"].to_numpy(dtype=float)

    numer = float(np.sum(a * b))
    # Alternative simple variance proxy. This is not claimed as correct; it is a probe.
    denom = float(np.sqrt(np.sum((a * b - np.mean(a * b)) ** 2)))
    if denom <= 0:
        return None, None, n

    z = numer / denom
    return z, _two_sided_p_from_z(z), n


def _stata_p_values(path: Path) -> tuple[float, float]:
    df = pd.read_csv(path)
    row = df.iloc[0]
    return float(row["stata_ar1_p"]), float(row["stata_ar2_p"])


rows: list[dict[str, object]] = []

for spec, cfg in SPECS.items():
    data_path = cfg["data"]
    params_path = cfg["params"]
    stata_path = cfg["stata"]

    if not data_path.exists() or not params_path.exists() or not stata_path.exists():
        rows.append(
            {
                "spec": spec,
                "candidate": "missing_artifacts",
                "data_exists": data_path.exists(),
                "params_exists": params_path.exists(),
                "stata_exists": stata_path.exists(),
            }
        )
        continue

    df = pd.read_csv(data_path)
    beta = _load_beta(params_path)
    stata_ar1_p, stata_ar2_p = _stata_p_values(stata_path)
    stata_ar1_abs_z = _abs_z_from_p(stata_ar1_p)
    stata_ar2_abs_z = _abs_z_from_p(stata_ar2_p)

    level = _level_residuals(df, beta, y=str(cfg["y"]), regressors=list(cfg["regressors"]))
    fd = _fd_residuals(level)

    candidates = [
        ("level_corr", level, "_level_resid", _corr_z),
        ("fd_corr", fd, "_fd_resid", _corr_z),
        ("level_inner", level, "_level_resid", _raw_inner_z),
        ("fd_inner", fd, "_fd_resid", _raw_inner_z),
    ]

    for candidate_name, candidate_df, resid_col, fn in candidates:
        for lag, stata_p, stata_abs_z in [
            (1, stata_ar1_p, stata_ar1_abs_z),
            (2, stata_ar2_p, stata_ar2_abs_z),
        ]:
            z, p, n_pairs = fn(candidate_df, resid_col, lag)
            abs_z = None if z is None else abs(float(z))

            rows.append(
                {
                    "spec": spec,
                    "candidate": candidate_name,
                    "lag": lag,
                    "n_pairs": n_pairs,
                    "candidate_z": z,
                    "candidate_abs_z": abs_z,
                    "candidate_p": p,
                    "stata_p": stata_p,
                    "stata_abs_z": stata_abs_z,
                    "abs_z_diff": None if abs_z is None else abs(abs_z - stata_abs_z),
                    "abs_p_diff": None if p is None else abs(float(p) - stata_p),
                }
            )

out = BASE / "ar_candidate_probe.csv"
result = pd.DataFrame(rows)
result.to_csv(out, index=False)

print(result.to_string(index=False))
print(f"\nWrote {out}")
