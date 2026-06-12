from __future__ import annotations

import argparse
from collections.abc import Iterable
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ART = ROOT / "artifacts" / "parity" / "xtabond2"
DEFAULT_STATA_V = DEFAULT_ART / "stata_V.csv"

DEFAULT_EXPECTED_PARAMS = ["L1.y", "x", "w", "_con"]

DEFAULT_NATIVE_PARAM_CANDIDATES = [
    "native_windmeijer_params.csv",
    "native_system_gmm_windmeijer_params.csv",
    "native_params_windmeijer.csv",
    "native_params.csv",
    "native_system_gmm_params.csv",
    "native_results.csv",
    "native_system_gmm_results.csv",
]


def _fail(message: str) -> None:
    raise RuntimeError(message)


def read_numeric_matrix(path: Path) -> np.ndarray:
    """Read a Stata-exported matrix CSV robustly.

    Handles common Stata/Pandas matrix exports where the first column contains
    row labels and the remaining columns are numeric.
    """
    if not path.exists():
        raise FileNotFoundError(f"Missing matrix file: {path}")

    raw = pd.read_csv(path)

    if raw.empty:
        _fail(f"Matrix file is empty: {path}")

    numeric = raw.apply(pd.to_numeric, errors="coerce")

    # Drop nonnumeric label columns and empty rows.
    numeric = numeric.dropna(axis=1, how="all")
    numeric = numeric.dropna(axis=0, how="all")

    if numeric.empty:
        _fail(f"No numeric matrix content found in: {path}")

    matrix = numeric.to_numpy(dtype=float)

    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        _fail(
            f"Expected a square covariance matrix in {path}, "
            f"but got shape {matrix.shape}."
        )

    if not np.all(np.isfinite(matrix)):
        _fail(f"Covariance matrix contains non-finite values: {path}")

    return matrix


def find_native_params_file(artifact_dir: Path, explicit_path: Path | None = None) -> Path:
    if explicit_path is not None:
        if not explicit_path.exists():
            raise FileNotFoundError(f"Explicit native params file not found: {explicit_path}")
        return explicit_path

    for name in DEFAULT_NATIVE_PARAM_CANDIDATES:
        candidate = artifact_dir / name
        if candidate.exists():
            return candidate

    native_csvs = sorted(artifact_dir.glob("native*.csv"))

    if native_csvs:
        listed = "\n  - ".join(str(p) for p in native_csvs)
        _fail(
            "Could not find a recognized native params file name, but found native CSVs:\n"
            f"  - {listed}\n\n"
            "Pass one explicitly with --native-params <path>."
        )

    _fail(
        "Could not find native params file. Expected one of:\n"
        + "\n".join(f"  - {artifact_dir / name}" for name in DEFAULT_NATIVE_PARAM_CANDIDATES)
    )


def pick_column(df: pd.DataFrame, candidates: Iterable[str], purpose: str) -> str:
    lower_to_actual = {c.lower(): c for c in df.columns}

    for candidate in candidates:
        if candidate.lower() in lower_to_actual:
            return lower_to_actual[candidate.lower()]

    _fail(
        f"Could not find {purpose} column. "
        f"Tried: {list(candidates)}. Available columns: {list(df.columns)}"
    )


def pick_param_column(df: pd.DataFrame) -> str:
    candidates = [
        "param",
        "parameter",
        "variable",
        "term",
        "coef_name",
        "name",
        "index",
    ]

    lower_to_actual = {c.lower(): c for c in df.columns}

    for candidate in candidates:
        if candidate.lower() in lower_to_actual:
            return lower_to_actual[candidate.lower()]

    # Fallback: first column, matching the old script behavior.
    return df.columns[0]


def pick_se_column(df: pd.DataFrame) -> str:
    return pick_column(
        df,
        candidates=[
            "std_err",
            "std_error",
            "native_std_err",
            "standard_error",
            "se",
        ],
        purpose="native standard-error",
    )


def pick_coef_column(df: pd.DataFrame) -> str | None:
    candidates = [
        "coef",
        "coefficient",
        "native_coef",
        "estimate",
        "beta",
    ]
    lower_to_actual = {c.lower(): c for c in df.columns}

    for candidate in candidates:
        if candidate.lower() in lower_to_actual:
            return lower_to_actual[candidate.lower()]

    return None


def covariance_type_values(df: pd.DataFrame) -> list[str]:
    cov_cols = [
        c for c in df.columns
        if c.lower() == "covariance_type"
        or ("cov" in c.lower() and "type" in c.lower())
    ]

    if not cov_cols:
        return []

    values: set[str] = set()

    for col in cov_cols:
        for value in df[col].dropna().astype(str):
            clean = value.strip()
            if clean:
                values.add(clean)

    return sorted(values)


def validate_windmeijer_export(
    native: pd.DataFrame,
    *,
    require_windmeijer: bool,
) -> list[str]:
    cov_values = covariance_type_values(native)

    if not cov_values:
        message = (
            "Native params file has no covariance_type column. "
            "Cannot verify whether the exported SEs are Windmeijer-corrected. "
            "Regenerate the native params export after calling "
            "run_native_dynamic_panel_gmm(..., windmeijer=True), and export "
            "native.covariance_type into the CSV."
        )

        if require_windmeijer:
            _fail(message)

        print(f"WARNING: {message}")
        return []

    has_windmeijer = any("windmeijer" in value.lower() for value in cov_values)

    if require_windmeijer and not has_windmeijer:
        _fail(
            "Native params file is not Windmeijer-certified.\n"
            f"Detected covariance_type values: {cov_values}\n\n"
            "Expected a value containing 'windmeijer', for example:\n"
            "  robust-clustered-two-step-windmeijer\n\n"
            "Fix the native exporter script, not this comparator, by calling:\n"
            "  run_native_dynamic_panel_gmm(..., windmeijer=True)\n"
            "and exporting native.covariance_type."
        )

    return cov_values


def build_comparison(
    *,
    native: pd.DataFrame,
    stata_v: np.ndarray,
    expected_params: list[str],
) -> pd.DataFrame:
    if len(expected_params) != stata_v.shape[0]:
        _fail(
            "Expected parameter list length does not match Stata covariance matrix size. "
            f"len(expected_params)={len(expected_params)}, stata_v.shape={stata_v.shape}."
        )

    stata_se = np.sqrt(np.maximum(np.diag(stata_v), 0.0))

    param_col = pick_param_column(native)
    se_col = pick_se_column(native)
    coef_col = pick_coef_column(native)

    native = native.copy()
    native[param_col] = native[param_col].astype(str)

    rows: list[dict[str, object]] = []

    for i, param in enumerate(expected_params):
        matches = native[native[param_col].eq(param)]

        if matches.empty:
            _fail(
                f"Native params file does not contain parameter {param!r}. "
                f"Available params: {native[param_col].tolist()}"
            )

        if len(matches) > 1:
            _fail(f"Native params file contains duplicate rows for parameter {param!r}.")

        row = matches.iloc[0]

        native_se = float(row[se_col])
        stata_se_i = float(stata_se[i])

        if not np.isfinite(native_se):
            _fail(f"Native SE for {param!r} is non-finite: {native_se}")

        if not np.isfinite(stata_se_i):
            _fail(f"Stata SE for {param!r} is non-finite: {stata_se_i}")

        out_row: dict[str, object] = {
            "param": param,
            "native_se": native_se,
            "stata_se": stata_se_i,
            "diff": native_se - stata_se_i,
            "abs_diff": abs(native_se - stata_se_i),
            "rel_diff": (
                abs(native_se - stata_se_i) / abs(stata_se_i)
                if stata_se_i != 0
                else np.nan
            ),
        }

        if coef_col is not None:
            out_row["native_coef"] = float(row[coef_col])

        rows.append(out_row)

    return pd.DataFrame(rows)


def write_outputs(
    *,
    artifact_dir: Path,
    native_params_path: Path,
    cov_values: list[str],
    comparison: pd.DataFrame,
    max_rel_tol: float,
    max_abs_tol: float | None,
    output_prefix: str,
) -> pd.DataFrame:
    max_abs_diff = float(comparison["abs_diff"].max())
    mean_abs_diff = float(comparison["abs_diff"].mean())
    max_rel_diff = float(comparison["rel_diff"].max())
    mean_rel_diff = float(comparison["rel_diff"].mean())

    pass_rel_tol = bool(max_rel_diff <= max_rel_tol)

    pass_abs_tol = True if max_abs_tol is None else bool(max_abs_diff <= max_abs_tol)

    passed = bool(pass_rel_tol and pass_abs_tol)

    summary = pd.DataFrame(
        [
            {
                "native_params_file": str(native_params_path),
                "covariance_type_values": "; ".join(cov_values) if cov_values else "",
                "n_params": int(len(comparison)),
                "max_abs_diff": max_abs_diff,
                "mean_abs_diff": mean_abs_diff,
                "max_rel_diff": max_rel_diff,
                "mean_rel_diff": mean_rel_diff,
                "max_rel_tol": float(max_rel_tol),
                "max_abs_tol": np.nan if max_abs_tol is None else float(max_abs_tol),
                "pass_rel_tol": pass_rel_tol,
                "pass_abs_tol": pass_abs_tol,
                "passed": passed,
            }
        ]
    )

    out_path = artifact_dir / f"{output_prefix}.csv"
    summary_path = artifact_dir / f"{output_prefix}_summary.csv"

    comparison.to_csv(out_path, index=False)
    summary.to_csv(summary_path, index=False)

    print("=" * 100)
    print("NATIVE WINDMEIJER STANDARD ERRORS VS STATA e(V)")
    print("=" * 100)
    print(summary.to_string(index=False))
    print()
    print(comparison.to_string(index=False))
    print()
    print(f"Wrote: {out_path}")
    print(f"Wrote: {summary_path}")

    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Compare native dynamic-panel GMM standard errors against Stata xtabond2 e(V). "
            "By default, this is a strict Windmeijer validation gate."
        )
    )

    parser.add_argument(
        "--artifact-dir",
        type=Path,
        default=DEFAULT_ART,
        help=f"Artifact directory. Default: {DEFAULT_ART}",
    )
    parser.add_argument(
        "--stata-v",
        type=Path,
        default=None,
        help="Path to Stata e(V) CSV. Default: <artifact-dir>/stata_V.csv",
    )
    parser.add_argument(
        "--native-params",
        type=Path,
        default=None,
        help="Explicit native params CSV. Default: search known native params names.",
    )
    parser.add_argument(
        "--expected-params",
        default=",".join(DEFAULT_EXPECTED_PARAMS),
        help=(
            "Comma-separated parameter order matching Stata e(V). "
            f"Default: {','.join(DEFAULT_EXPECTED_PARAMS)}"
        ),
    )
    parser.add_argument(
        "--max-rel-tol",
        type=float,
        default=0.03,
        help="Maximum allowed relative SE gap. Default: 0.03 = 3%%.",
    )
    parser.add_argument(
        "--max-abs-tol",
        type=float,
        default=None,
        help="Optional maximum allowed absolute SE gap.",
    )
    parser.add_argument(
        "--allow-non-windmeijer",
        action="store_true",
        help=(
            "Allow comparison even if covariance_type is missing or not Windmeijer. "
            "Use only for debugging old exports."
        ),
    )
    parser.add_argument(
        "--output-prefix",
        default="native_windmeijer_se_vs_stata_v",
        help="Output CSV prefix. Default: native_windmeijer_se_vs_stata_v.",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    artifact_dir: Path = args.artifact_dir
    stata_v_path: Path = args.stata_v if args.stata_v is not None else artifact_dir / "stata_V.csv"
    expected_params = [p.strip() for p in str(args.expected_params).split(",") if p.strip()]

    if not artifact_dir.exists():
        raise FileNotFoundError(f"Artifact directory does not exist: {artifact_dir}")

    stata_v = read_numeric_matrix(stata_v_path)
    native_params_path = find_native_params_file(artifact_dir, args.native_params)

    native = pd.read_csv(native_params_path)

    if native.empty:
        _fail(f"Native params file is empty: {native_params_path}")

    print(f"Using Stata V file: {stata_v_path}")
    print(f"Using native params file: {native_params_path}")

    cov_values = validate_windmeijer_export(
        native,
        require_windmeijer=not args.allow_non_windmeijer,
    )

    if cov_values:
        print(f"Native covariance_type values: {cov_values}")

    comparison = build_comparison(
        native=native,
        stata_v=stata_v,
        expected_params=expected_params,
    )

    summary = write_outputs(
        artifact_dir=artifact_dir,
        native_params_path=native_params_path,
        cov_values=cov_values,
        comparison=comparison,
        max_rel_tol=args.max_rel_tol,
        max_abs_tol=args.max_abs_tol,
        output_prefix=args.output_prefix,
    )

    passed = bool(summary.iloc[0]["passed"])

    if not passed:
        print()
        print("FAILED: Native SEs are outside the configured tolerance.")
        print("Interpretation:")
        print("  - If all rel_diff values are almost equal, this is likely a scalar scaling issue.")
        print("  - If rel_diff varies materially by coefficient, inspect the Windmeijer derivative term.")
        return 1

    print()
    print("PASSED: Native Windmeijer SEs are within tolerance.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print()
        print("=" * 100)
        print("ERROR")
        print("=" * 100)
        print(str(exc))
        raise
