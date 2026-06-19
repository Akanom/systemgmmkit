from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
ART = ROOT / "artifacts" / "parity" / "xtabond2"

STATA_V = ART / "stata_V.csv"
NATIVE_X = ART / "native_X.csv"
NATIVE_Z = ART / "native_Z.csv"
NATIVE_U = ART / "native_u_stack.csv"
NATIVE_W = ART / "native_A2.csv"
ROW_META = ART / "native_row_meta.csv"
PARAMS = ART / "native_system_gmm_params.csv"


def read_matrix(path: Path) -> np.ndarray:
    if not path.exists():
        raise FileNotFoundError(path)

    df = pd.read_csv(path)
    drop_cols = [c for c in df.columns if c.lower() in {"index", "row", "row_id"}]
    if drop_cols:
        df = df.drop(columns=drop_cols)

    return df.to_numpy(dtype=float)


def read_vector(path: Path) -> np.ndarray:
    arr = read_matrix(path)

    if arr.shape[1] == 1:
        return arr.reshape(-1, 1)

    if arr.shape[0] == 1:
        return arr.reshape(-1, 1)

    raise ValueError(f"Expected vector-like matrix from {path}, got {arr.shape}")


def group_indices_from_meta(meta: pd.DataFrame) -> list[np.ndarray]:
    if "entity" not in meta.columns:
        raise ValueError("native_row_meta.csv must contain an entity column.")

    out: list[np.ndarray] = []

    for _, g in meta.reset_index().groupby("entity", sort=False):
        out.append(g["index"].to_numpy(dtype=int))

    return out


def cov_from_s(
    *,
    X: np.ndarray,
    Z: np.ndarray,
    W: np.ndarray,
    S: np.ndarray,
    multiplier: float,
) -> np.ndarray:
    D = X.T @ Z
    bread = np.linalg.pinv(D @ W @ D.T)
    meat = D @ W @ S @ W @ D.T
    return multiplier * bread @ meat @ bread


def compare_v(name: str, V: np.ndarray, stata_v: np.ndarray) -> dict[str, float | str]:
    diag_v = np.maximum(np.diag(V), 0.0)
    diag_s = np.maximum(np.diag(stata_v), 0.0)

    se = np.sqrt(diag_v)
    stata_se = np.sqrt(diag_s)

    se_diff = se - stata_se
    rel = np.abs(se_diff) / np.maximum(np.abs(stata_se), 1e-15)

    v_diff = V - stata_v

    alpha = float(np.sum(V * stata_v) / max(np.sum(V * V), 1e-30))
    v_scaled = alpha * V
    scaled_diff = v_scaled - stata_v

    return {
        "variant": name,
        "v_norm": float(np.linalg.norm(V)),
        "stata_v_norm": float(np.linalg.norm(stata_v)),
        "v_max_abs_diff": float(np.max(np.abs(v_diff))),
        "v_mean_abs_diff": float(np.mean(np.abs(v_diff))),
        "se_max_abs_diff": float(np.max(np.abs(se_diff))),
        "se_mean_abs_diff": float(np.mean(np.abs(se_diff))),
        "se_max_rel_diff": float(np.max(rel)),
        "se_mean_rel_diff": float(np.mean(rel)),
        "best_scalar_alpha_v_to_stata": alpha,
        "scaled_v_max_abs_diff": float(np.max(np.abs(scaled_diff))),
        "scaled_v_mean_abs_diff": float(np.mean(np.abs(scaled_diff))),
    }


def main() -> None:
    X = read_matrix(NATIVE_X)
    Z = read_matrix(NATIVE_Z)
    u = read_vector(NATIVE_U)
    W_native = read_matrix(NATIVE_W)
    stata_v = read_matrix(STATA_V)
    meta = pd.read_csv(ROW_META)

    n, k = X.shape
    group_indices = group_indices_from_meta(meta)
    g = len(group_indices)

    if len(meta) != len(u):
        raise ValueError(f"row_meta/u length mismatch: {len(meta)} != {len(u)}")

    S_row_sum = Z.T @ ((u.reshape(-1) ** 2)[:, None] * Z)

    S_group_sum = np.zeros((Z.shape[1], Z.shape[1]), dtype=float)

    for idx in group_indices:
        Zi = Z[idx, :]
        ui = u[idx, :]
        gi = Zi.T @ ui
        S_group_sum += gi @ gi.T

    S_variants = {
        "row_sum": S_row_sum,
        "row_avg_by_n": S_row_sum / n,
        "row_avg_by_groups": S_row_sum / g,
        "group_sum": S_group_sum,
        "group_avg": S_group_sum / g,
    }

    W_variants = {
        "W_native": W_native,
        "W_native_div_groups": W_native / g,
    }

    multipliers = {
        "none": 1.0,
        "n_over_n_minus_k": n / max(n - k, 1),
        "groups_over_groups_minus_1": g / max(g - 1, 1),
        "cluster_small": (g / max(g - 1, 1)) * ((n - 1) / max(n - k, 1)),
        "one_over_n": 1.0 / n,
        "one_over_groups": 1.0 / g,
        "groups": float(g),
        "n": float(n),
    }

    rows = []

    for s_name, S in S_variants.items():
        for w_name, W in W_variants.items():
            for m_name, mult in multipliers.items():
                try:
                    V = cov_from_s(X=X, Z=Z, W=W, S=S, multiplier=mult)
                    rows.append(compare_v(f"{s_name}__{w_name}__{m_name}", V, stata_v))
                except Exception as exc:
                    rows.append(
                        {
                            "variant": f"{s_name}__{w_name}__{m_name}",
                            "error": repr(exc),
                        }
                    )

    out = pd.DataFrame(rows)

    sort_cols = [
        c for c in ["se_max_rel_diff", "se_mean_rel_diff", "v_max_abs_diff"] if c in out.columns
    ]

    out = out.sort_values(sort_cols, na_position="last").reset_index(drop=True)

    out_path = ART / "native_covariance_variants_vs_stata_v.csv"
    summary_path = ART / "native_covariance_variants_vs_stata_v_top10.csv"

    out.to_csv(out_path, index=False)
    out.head(10).to_csv(summary_path, index=False)

    print("=" * 100)
    print("TOP COVARIANCE VARIANTS VS STATA e(V)")
    print("=" * 100)

    display_cols = [
        "variant",
        "se_max_abs_diff",
        "se_mean_abs_diff",
        "se_max_rel_diff",
        "se_mean_rel_diff",
        "v_max_abs_diff",
        "v_mean_abs_diff",
        "best_scalar_alpha_v_to_stata",
        "scaled_v_max_abs_diff",
    ]

    display_cols = [c for c in display_cols if c in out.columns]
    print(out.head(20)[display_cols].to_string(index=False))

    print()
    print(f"n={n}, k={k}, groups={g}")
    print(f"Wrote: {out_path}")
    print(f"Wrote: {summary_path}")


if __name__ == "__main__":
    main()
