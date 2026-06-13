from __future__ import annotations

from pathlib import Path

import pandas as pd

OUT = Path("artifacts/parity/xtabond2")

NATIVE_PARAMS = (
    OUT / "specs" / "system_gmm_baseline_controls" / "windmeijer" / "native_params.csv"
)
NATIVE_DIAGNOSTICS = (
    OUT
    / "specs"
    / "system_gmm_baseline_controls"
    / "windmeijer"
    / "native_diagnostics.csv"
)
STATA_PARAMS = OUT / "xtabond2_system_gmm_params.csv"
STATA_DIAGNOSTICS = OUT / "xtabond2_system_gmm_diagnostics.csv"

COEF_OUT = OUT / "xtabond2_native_system_gmm_coef_comparison.csv"
DIAG_OUT = OUT / "xtabond2_native_system_gmm_diagnostics_comparison.csv"
REPORT_OUT = OUT / "xtabond2_native_system_gmm_parity.md"


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_csv(path)


def _normalize_param(name: object) -> str:
    value = str(name)
    aliases = {
        "L.y": "L1.y",
        "_cons": "_con",
    }
    return aliases.get(value, value)


def _native_params(path: Path) -> pd.DataFrame:
    df = _read_csv(path).copy()
    if "param" not in df.columns:
        raise ValueError(f"Native params missing 'param' column: {path}")

    df["param_norm"] = df["param"].map(_normalize_param)

    keep = [
        "param_norm",
        "param",
        "native_coef",
        "native_std_err",
        "native_z",
        "native_p_value",
        "covariance_type",
    ]
    return df[[c for c in keep if c in df.columns]]


def _stata_params(path: Path) -> pd.DataFrame:
    df = _read_csv(path).copy()

    if "parm" in df.columns:
        df = df.rename(columns={"parm": "param"})
    if "estimate" in df.columns:
        df = df.rename(columns={"estimate": "stata_coef"})
    if "stderr" in df.columns:
        df = df.rename(columns={"stderr": "stata_std_err"})

    if "param" not in df.columns:
        raise ValueError(f"Stata params missing parameter column: {path}")

    df["param_norm"] = df["param"].map(_normalize_param)

    keep = [
        "param_norm",
        "param",
        "stata_coef",
        "stata_std_err",
        "dof",
        "t",
        "p",
        "min95",
        "max95",
    ]
    return df[[c for c in keep if c in df.columns]]


def _compare_params() -> pd.DataFrame:
    native = _native_params(NATIVE_PARAMS)
    stata = _stata_params(STATA_PARAMS)

    compare = native.merge(
        stata,
        on="param_norm",
        how="outer",
        suffixes=("_native_name", "_stata_name"),
    )

    compare["param"] = compare["param_norm"]
    compare = compare.drop(columns=["param_norm"])

    if "native_coef" in compare.columns and "stata_coef" in compare.columns:
        compare["abs_coef_diff"] = (
            pd.to_numeric(compare["native_coef"], errors="coerce")
            - pd.to_numeric(compare["stata_coef"], errors="coerce")
        ).abs()

    if "native_std_err" in compare.columns and "stata_std_err" in compare.columns:
        native_se = pd.to_numeric(compare["native_std_err"], errors="coerce")
        stata_se = pd.to_numeric(compare["stata_std_err"], errors="coerce")
        compare["abs_se_diff"] = (native_se - stata_se).abs()
        compare["rel_se_diff"] = compare["abs_se_diff"] / stata_se.abs()

    preferred_order = [
        "param",
        "param_native_name",
        "param_stata_name",
        "native_coef",
        "stata_coef",
        "abs_coef_diff",
        "native_std_err",
        "stata_std_err",
        "abs_se_diff",
        "rel_se_diff",
        "native_z",
        "native_p_value",
        "dof",
        "t",
        "p",
        "min95",
        "max95",
        "covariance_type",
    ]

    cols = [c for c in preferred_order if c in compare.columns]
    rest = [c for c in compare.columns if c not in cols]
    return compare[cols + rest].sort_values("param").reset_index(drop=True)


def _compare_diagnostics() -> pd.DataFrame:
    native = _read_csv(NATIVE_DIAGNOSTICS).add_prefix("native_file_")
    stata = _read_csv(STATA_DIAGNOSTICS).add_prefix("stata_file_")
    return pd.concat([native.reset_index(drop=True), stata.reset_index(drop=True)], axis=1)


def _as_float(value: object) -> float:
    return float(pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0])


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    compare = _compare_params()
    diag = _compare_diagnostics()

    compare.to_csv(COEF_OUT, index=False)
    diag.to_csv(DIAG_OUT, index=False)

    matched_coef = compare.dropna(subset=["native_coef", "stata_coef"]).copy()
    matched_se = compare.dropna(subset=["native_std_err", "stata_std_err"]).copy()

    coef_max_abs_diff = _as_float(matched_coef["abs_coef_diff"].max())
    se_max_abs_diff = _as_float(matched_se["abs_se_diff"].max())

    coef_pass = coef_max_abs_diff <= 1e-5
    se_pass = se_max_abs_diff <= 1e-5

    diag_row = diag.iloc[0].to_dict()

    same_nobs = (
        diag_row.get("native_file_native_nobs")
        == diag_row.get("stata_file_stata_nobs")
    )
    same_instruments = (
        diag_row.get("native_file_native_n_instruments")
        == diag_row.get("stata_file_stata_n_instruments")
    )

    hansen_diff = abs(
        _as_float(diag_row.get("native_file_native_hansen_p"))
        - _as_float(diag_row.get("stata_file_stata_hansen_p"))
    )
    ar1_diff = abs(
        _as_float(diag_row.get("native_file_native_ar1"))
        - _as_float(diag_row.get("stata_file_stata_ar1"))
    )
    ar1_p_diff = abs(
        _as_float(diag_row.get("native_file_native_ar1_p"))
        - _as_float(diag_row.get("stata_file_stata_ar1_p"))
    )
    ar2_diff = abs(
        _as_float(diag_row.get("native_file_native_ar2"))
        - _as_float(diag_row.get("stata_file_stata_ar2"))
    )
    ar2_p_diff = abs(
        _as_float(diag_row.get("native_file_native_ar2_p"))
        - _as_float(diag_row.get("stata_file_stata_ar2_p"))
    )

    hansen_pass = hansen_diff <= 1e-5
    ar_pass = (
        ar1_diff <= 0.10
        and ar1_p_diff <= 0.03
        and ar2_diff <= 0.10
        and ar2_p_diff <= 0.03
    )

    strict_pass = bool(
        coef_pass
        and se_pass
        and same_nobs
        and same_instruments
        and hansen_pass
        and ar_pass
    )

    status = (
        "PASS_STRICT_XTABOND2_SYSTEM_GMM_BASELINE"
        if strict_pass
        else "REVIEW_XTABOND2_SYSTEM_GMM_BASELINE"
    )

    certification = pd.DataFrame(
        [
            {
                "check": "Sample size",
                "native": diag_row.get("native_file_native_nobs"),
                "stata": diag_row.get("stata_file_stata_nobs"),
                "abs_diff": 0 if same_nobs else "mismatch",
                "status": "PASS" if same_nobs else "REVIEW",
            },
            {
                "check": "Instrument count",
                "native": diag_row.get("native_file_native_n_instruments"),
                "stata": diag_row.get("stata_file_stata_n_instruments"),
                "abs_diff": 0 if same_instruments else "mismatch",
                "status": "PASS" if same_instruments else "REVIEW",
            },
            {
                "check": "Max coefficient difference",
                "native": "",
                "stata": "",
                "abs_diff": coef_max_abs_diff,
                "status": "PASS" if coef_pass else "REVIEW",
            },
            {
                "check": "Max Windmeijer SE difference",
                "native": "",
                "stata": "",
                "abs_diff": se_max_abs_diff,
                "status": "PASS" if se_pass else "REVIEW",
            },
            {
                "check": "Hansen p-value",
                "native": diag_row.get("native_file_native_hansen_p"),
                "stata": diag_row.get("stata_file_stata_hansen_p"),
                "abs_diff": hansen_diff,
                "status": "PASS" if hansen_pass else "REVIEW",
            },
            {
                "check": "AR(1) statistic",
                "native": diag_row.get("native_file_native_ar1"),
                "stata": diag_row.get("stata_file_stata_ar1"),
                "abs_diff": ar1_diff,
                "status": "PASS" if ar1_diff <= 0.10 else "REVIEW",
            },
            {
                "check": "AR(1) p-value",
                "native": diag_row.get("native_file_native_ar1_p"),
                "stata": diag_row.get("stata_file_stata_ar1_p"),
                "abs_diff": ar1_p_diff,
                "status": "PASS" if ar1_p_diff <= 0.03 else "REVIEW",
            },
            {
                "check": "AR(2) statistic",
                "native": diag_row.get("native_file_native_ar2"),
                "stata": diag_row.get("stata_file_stata_ar2"),
                "abs_diff": ar2_diff,
                "status": "PASS" if ar2_diff <= 0.10 else "REVIEW",
            },
            {
                "check": "AR(2) p-value",
                "native": diag_row.get("native_file_native_ar2_p"),
                "stata": diag_row.get("stata_file_stata_ar2_p"),
                "abs_diff": ar2_p_diff,
                "status": "PASS" if ar2_p_diff <= 0.03 else "REVIEW",
            },
        ]
    )

    md = [
        "# xtabond2 vs Native System GMM Parity",
        "",
        "## Status",
        "",
        f"`{status}`",
        "",
        "## Certification Summary",
        "",
        certification.to_markdown(index=False),
        "",
        "## Coefficient Comparison",
        "",
        compare.to_markdown(index=False),
        "",
        "## Diagnostics Comparison",
        "",
        diag.to_markdown(index=False),
        "",
        "## Artifact Sources",
        "",
        f"- Native parameters: `{NATIVE_PARAMS}`",
        f"- Native diagnostics: `{NATIVE_DIAGNOSTICS}`",
        f"- Stata parameters: `{STATA_PARAMS}`",
        f"- Stata diagnostics: `{STATA_DIAGNOSTICS}`",
        "",
        "## Generated Files",
        "",
        "- `system_gmm_benchmark.csv`",
        "- `system_gmm_xtabond2_parity.do`",
        "- `xtabond2_native_system_gmm_coef_comparison.csv`",
        "- `xtabond2_native_system_gmm_diagnostics_comparison.csv`",
        "- `xtabond2_native_system_gmm_parity.md`",
        "",
        "## Notes",
        "",
        "Stata parameter aliases are normalized before comparison: `L.y` maps to `L1.y`, and `_cons` maps to `_con`.",
        "The signed AR statistics are treated as the primary AR parity object; AR p-values are checked as derived diagnostics.",
        "",
    ]

    REPORT_OUT.write_text("\n".join(md), encoding="utf-8")

    print(f"Status: {status}")
    print(certification.to_string(index=False))
    print(f"\nWrote {COEF_OUT}")
    print(f"Wrote {DIAG_OUT}")
    print(f"Wrote {REPORT_OUT}")


if __name__ == "__main__":
    main()