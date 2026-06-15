from __future__ import annotations

from pathlib import Path

import pandas as pd

ART = Path("artifacts/parity/xtabond2")

NATIVE_PARAMS = ART / "specs" / "system_gmm_baseline_controls" / "uncorrected" / "native_params.csv"
NATIVE_DIAG = ART / "specs" / "system_gmm_baseline_controls" / "uncorrected" / "native_diagnostics.csv"

STATA_PARAMS = ART / "system_gmm_fd_onestep_params.csv"
STATA_DIAG = ART / "system_gmm_fd_onestep_diagnostics.csv"

OUT = ART / "system_gmm_fd_onestep_native_vs_xtabond2_coef_comparison.csv"
OUT_DIAG = ART / "system_gmm_fd_onestep_native_vs_xtabond2_diagnostics_comparison.csv"


def first_col(df: pd.DataFrame, names: list[str]) -> str:
    lower = {c.lower(): c for c in df.columns}
    for name in names:
        if name.lower() in lower:
            return lower[name.lower()]
    raise KeyError(f"None of {names} found in {list(df.columns)}")


def normalize_param(x: object) -> str:
    s = str(x).strip()
    return {
        "L.y": "L1.y",
        "L1.y": "L1.y",
        "_cons": "_con",
        "_con": "_con",
        "x": "x",
        "w": "w",
    }.get(s, s)


def read_native(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    return pd.DataFrame({
        "param": df[first_col(df, ["param"])].map(normalize_param),
        "native_coef": pd.to_numeric(df[first_col(df, ["native_coef", "coef", "estimate"])], errors="coerce"),
        "native_std_err": pd.to_numeric(df[first_col(df, ["native_std_err", "std_err", "stderr", "se"])], errors="coerce"),
    })


def read_stata(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    return pd.DataFrame({
        "param": df[first_col(df, ["parm", "param", "term"])].map(normalize_param),
        "stata_coef": pd.to_numeric(df[first_col(df, ["estimate", "coef", "b"])], errors="coerce"),
        "stata_std_err": pd.to_numeric(df[first_col(df, ["stderr", "std_err", "se"])], errors="coerce"),
    })


def diag_value(df: pd.DataFrame, names: list[str]) -> float | None:
    lower = {c.lower(): c for c in df.columns}
    for name in names:
        col = lower.get(name.lower())
        if col:
            value = pd.to_numeric(df.loc[0, col], errors="coerce")
            if pd.notna(value):
                return float(value)
    return None


def main() -> None:
    for p in [NATIVE_PARAMS, NATIVE_DIAG, STATA_PARAMS, STATA_DIAG]:
        if not p.exists():
            raise FileNotFoundError(p)

    native = read_native(NATIVE_PARAMS)
    stata = read_stata(STATA_PARAMS)

    merged = native.merge(stata, on="param", how="outer", indicator=True)
    merged["coef_abs_diff"] = (merged["native_coef"] - merged["stata_coef"]).abs()
    merged["se_abs_diff"] = (merged["native_std_err"] - merged["stata_std_err"]).abs()
    merged["coef_rel_diff"] = merged["coef_abs_diff"] / merged["stata_coef"].abs().clip(lower=1e-15)
    merged["se_rel_diff"] = merged["se_abs_diff"] / merged["stata_std_err"].abs().clip(lower=1e-15)

    merged.to_csv(OUT, index=False)

    nd = pd.read_csv(NATIVE_DIAG)
    sd = pd.read_csv(STATA_DIAG)

    diag = pd.DataFrame([
        {
            "metric": "nobs",
            "native": diag_value(nd, ["native_nobs", "nobs"]),
            "stata": diag_value(sd, ["stata_nobs", "nobs"]),
        },
        {
            "metric": "n_instruments",
            "native": diag_value(nd, ["native_n_instruments", "n_instruments"]),
            "stata": diag_value(sd, ["stata_n_instruments", "n_instruments"]),
        },
        {
            "metric": "hansen_p",
            "native": diag_value(nd, ["native_hansen_p", "hansen_p"]),
            "stata": diag_value(sd, ["stata_hansen_p", "hansen_p"]),
        },
        {
            "metric": "ar1_p",
            "native": diag_value(nd, ["native_ar1_p", "ar1_p"]),
            "stata": diag_value(sd, ["stata_ar1_p", "ar1_p"]),
        },
        {
            "metric": "ar2_p",
            "native": diag_value(nd, ["native_ar2_p", "ar2_p"]),
            "stata": diag_value(sd, ["stata_ar2_p", "ar2_p"]),
        },
    ])

    diag["abs_diff"] = (diag["native"] - diag["stata"]).abs()
    diag.to_csv(OUT_DIAG, index=False)

    print(merged.to_string(index=False))
    print()
    print(diag.to_string(index=False))
    print()
    print(f"Wrote {OUT}")
    print(f"Wrote {OUT_DIAG}")


if __name__ == "__main__":
    main()
