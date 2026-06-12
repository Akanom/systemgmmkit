from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path("artifacts/parity/xtabond2/specs/system_gmm_decomposition_controls")


def _find_col(df: pd.DataFrame, candidates: list[str]) -> str:
    lower = {c.lower(): c for c in df.columns}
    for candidate in candidates:
        if candidate.lower() in lower:
            return lower[candidate.lower()]
    raise KeyError(f"None of these columns found: {candidates}. Available: {list(df.columns)}")


def _normalise_param_name(value: object) -> str:
    text = str(value).strip()
    mapping = {
        "L.y": "L1.y",
        "L1.y": "L1.y",
        "_cons": "_con",
        "_con": "_con",
    }
    return mapping.get(text, text)


def _load_stata_params(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)

    param_col = _find_col(df, ["parm", "param", "variable"])
    coef_col = _find_col(df, ["estimate", "coef", "coefficient", "b"])
    se_col = _find_col(df, ["stderr", "std_err", "se"])

    return pd.DataFrame(
        {
            "param": df[param_col].map(_normalise_param_name),
            "stata_coef": pd.to_numeric(df[coef_col], errors="coerce"),
            "stata_std_err": pd.to_numeric(df[se_col], errors="coerce"),
        }
    )


def main() -> None:
    native_params_path = OUT / "native_params.csv"
    native_diag_path = OUT / "native_diagnostics.csv"
    stata_params_path = OUT / "stata_params.csv"
    stata_diag_path = OUT / "stata_diagnostics.csv"

    if not native_params_path.exists():
        raise FileNotFoundError(
            f"Missing native params: {native_params_path}. "
            "Run scripts/parity/run_native_system_gmm_decomposition_controls.py first."
        )

    native = pd.read_csv(native_params_path)

    if not stata_params_path.exists():
        summary = pd.DataFrame(
            [
                {
                    "spec": "system_gmm_decomposition_controls",
                    "status": "STATA_ARTIFACTS_PENDING",
                    "message": "Run the generated Stata do-file before strict comparison.",
                }
            ]
        )
        summary.to_csv(OUT / "summary.csv", index=False)
        print(summary.to_string(index=False))
        return

    stata = _load_stata_params(stata_params_path)

    merged = native.merge(stata, on="param", how="outer")
    merged["coef_abs_diff"] = (merged["native_coef"] - merged["stata_coef"]).abs()
    merged["se_abs_diff"] = (merged["native_std_err"] - merged["stata_std_err"]).abs()
    merged["se_rel_diff"] = merged["se_abs_diff"] / np.maximum(merged["stata_std_err"].abs(), 1e-15)

    merged.to_csv(OUT / "native_vs_stata_params.csv", index=False)

    summary_row = {
        "spec": "system_gmm_decomposition_controls",
        "status": "COMPARISON_GENERATED",
        "n_params_native": int(native["param"].nunique()),
        "n_params_stata": int(stata["param"].nunique()),
        "max_abs_coef_diff": float(merged["coef_abs_diff"].max(skipna=True)),
        "mean_abs_coef_diff": float(merged["coef_abs_diff"].mean(skipna=True)),
        "max_rel_se_diff": float(merged["se_rel_diff"].max(skipna=True)),
        "mean_rel_se_diff": float(merged["se_rel_diff"].mean(skipna=True)),
    }

    if native_diag_path.exists() and stata_diag_path.exists():
        native_diag = pd.read_csv(native_diag_path)
        stata_diag = pd.read_csv(stata_diag_path)
        diag = pd.concat(
            [
                native_diag.add_prefix("native_file_"),
                stata_diag.add_prefix("stata_file_"),
            ],
            axis=1,
        )
        diag.to_csv(OUT / "native_vs_stata_diagnostics.csv", index=False)

    summary = pd.DataFrame([summary_row])
    summary.to_csv(OUT / "summary.csv", index=False)

    print(summary.to_string(index=False))
    print(f"Wrote {OUT / 'native_vs_stata_params.csv'}")


if __name__ == "__main__":
    main()
