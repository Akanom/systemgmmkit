from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
ART = ROOT / "artifacts" / "parity" / "xtabond2"

STATA_V = ART / "stata_V.csv"

# Expected coefficient order from current benchmark:
# 1 L1.y
# 2 x
# 3 w
# 4 _con
EXPECTED_PARAMS = ["L1.y", "x", "w", "_con"]


def read_matrix(path: Path) -> np.ndarray:
    if not path.exists():
        raise FileNotFoundError(path)

    df = pd.read_csv(path)

    drop_cols = [c for c in df.columns if c.lower() in {"index", "row", "row_id"}]
    if drop_cols:
        df = df.drop(columns=drop_cols)

    return df.to_numpy(dtype=float)


def find_native_params_file() -> Path:
    candidates = [
        ART / "native_params.csv",
        ART / "native_system_gmm_params.csv",
        ART / "native_results.csv",
        ART / "native_system_gmm_results.csv",
    ]

    for path in candidates:
        if path.exists():
            return path

    raise FileNotFoundError(
        "Could not find native params file. Existing native CSV files are: "
        + ", ".join(p.name for p in sorted(ART.glob("native*.csv")))
    )


def main() -> None:
    stata_v = read_matrix(STATA_V)
    stata_se = np.sqrt(np.maximum(np.diag(stata_v), 0.0))

    native_params_path = find_native_params_file()
    native = pd.read_csv(native_params_path)

    print(f"Using native params file: {native_params_path}")

    # Try common column names.
    if "param" in native.columns:
        param_col = "param"
    elif "variable" in native.columns:
        param_col = "variable"
    elif native.columns[0].lower() in {"", "index"}:
        param_col = native.columns[0]
    else:
        param_col = native.columns[0]

    se_candidates = [
        "std_err",
        "std_error",
        "native_std_err",
        "se",
    ]

    se_col = next((c for c in se_candidates if c in native.columns), None)

    if se_col is None:
        raise ValueError(
            f"Could not find native standard-error column in {native_params_path}. "
            f"Columns: {list(native.columns)}"
        )

    native = native.copy()
    native[param_col] = native[param_col].astype(str)

    rows = []

    for i, param in enumerate(EXPECTED_PARAMS):
        m = native[native[param_col].eq(param)]

        if m.empty:
            raise ValueError(
                f"Native params file does not contain parameter {param!r}. "
                f"Available params: {native[param_col].tolist()}"
            )

        native_se = float(m.iloc[0][se_col])
        s_se = float(stata_se[i])

        rows.append({
            "param": param,
            "native_se": native_se,
            "stata_se": s_se,
            "diff": native_se - s_se,
            "abs_diff": abs(native_se - s_se),
            "rel_diff": abs(native_se - s_se) / abs(s_se) if s_se != 0 else np.nan,
        })

    out = pd.DataFrame(rows)

    summary = pd.DataFrame([{
        "native_params_file": str(native_params_path),
        "n_params": len(out),
        "max_abs_diff": float(out["abs_diff"].max()),
        "mean_abs_diff": float(out["abs_diff"].mean()),
        "max_rel_diff": float(out["rel_diff"].max()),
        "mean_rel_diff": float(out["rel_diff"].mean()),
    }])

    out_path = ART / "native_se_vs_stata_v.csv"
    summary_path = ART / "native_se_vs_stata_v_summary.csv"

    out.to_csv(out_path, index=False)
    summary.to_csv(summary_path, index=False)

    print("=" * 100)
    print("NATIVE STANDARD ERRORS VS STATA e(V)")
    print("=" * 100)
    print(summary.to_string(index=False))
    print()
    print(out.to_string(index=False))
    print()
    print(f"Wrote: {out_path}")
    print(f"Wrote: {summary_path}")


if __name__ == "__main__":
    main()