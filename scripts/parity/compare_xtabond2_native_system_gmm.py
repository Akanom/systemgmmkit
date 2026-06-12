from __future__ import annotations

from pathlib import Path

import pandas as pd

OUT = Path("artifacts/parity/xtabond2")
BASELINE_WINDMEIJER = OUT / "specs" / "system_gmm_baseline_controls" / "windmeijer"


def _first_existing(paths: list[Path]) -> Path | None:
    for path in paths:
        if path.exists():
            return path
    return None


def _require_existing(paths: list[Path], label: str) -> Path:
    path = _first_existing(paths)
    if path is None:
        candidates = "\n".join(f"  - {p}" for p in paths)
        raise FileNotFoundError(f"Missing {label}. Tried:\n{candidates}")
    return path


def _read_csv_if_exists(path: Path | None) -> pd.DataFrame | None:
    if path is None or not path.exists():
        return None
    return pd.read_csv(path)


def _normalise_stata_params(stata_params: pd.DataFrame) -> pd.DataFrame:
    """Return Stata parameters with stable column names for comparison."""
    if stata_params.empty:
        return stata_params

    renamed = stata_params.copy()

    rename_map = {}
    if "parm" in renamed.columns:
        rename_map["parm"] = "param"
    if "estimate" in renamed.columns:
        rename_map["estimate"] = "stata_coef"
    if "stderr" in renamed.columns:
        rename_map["stderr"] = "stata_std_err"
    if "std_err" in renamed.columns:
        rename_map["std_err"] = "stata_std_err"

    renamed = renamed.rename(columns=rename_map)

    if "param" not in renamed.columns:
        raise KeyError(f"Could not find Stata parameter-name column in {list(stata_params.columns)}")

    if "stata_coef" not in renamed.columns:
        possible_coef_cols = [c for c in renamed.columns if c.lower() in {"coef", "b", "estimate"}]
        if possible_coef_cols:
            renamed = renamed.rename(columns={possible_coef_cols[0]: "stata_coef"})

    return renamed


def main() -> None:
    native_params_path = _require_existing(
        [
            BASELINE_WINDMEIJER / "native_params.csv",
            OUT / "native_system_gmm_params.csv",
        ],
        "native System GMM parameter artifact",
    )
    native_diag_path = _require_existing(
        [
            BASELINE_WINDMEIJER / "native_diagnostics.csv",
            OUT / "native_system_gmm_diagnostics.csv",
        ],
        "native System GMM diagnostics artifact",
    )

    stata_params_path = _first_existing(
        [
            OUT / "xtabond2_system_gmm_params.csv",
        ]
    )
    stata_diag_path = _first_existing(
        [
            OUT / "xtabond2_system_gmm_diagnostics.csv",
            OUT / "xtabond2_internal_diagnostics.csv",
        ]
    )

    native_params = pd.read_csv(native_params_path)
    stata_params = _read_csv_if_exists(stata_params_path)

    if stata_params is not None and not stata_params.empty:
        stata_params = _normalise_stata_params(stata_params)

        compare = native_params.merge(
            stata_params,
            on="param",
            how="outer",
            suffixes=("_native_file", "_stata_file"),
        )

        if {"native_coef", "stata_coef"}.issubset(compare.columns):
            compare["abs_coef_diff"] = (compare["native_coef"] - compare["stata_coef"]).abs()

        if {"native_std_err", "stata_std_err"}.issubset(compare.columns):
            compare["abs_se_diff"] = (compare["native_std_err"] - compare["stata_std_err"]).abs()
            compare["rel_se_diff"] = compare["abs_se_diff"] / compare["stata_std_err"].abs()
    else:
        compare = native_params.copy()
        compare["stata_status"] = "PENDING_RUN_STATA_DOFILE"
        compare["stata_coef"] = pd.NA
        compare["abs_coef_diff"] = pd.NA

    compare.to_csv(OUT / "xtabond2_native_system_gmm_coef_comparison.csv", index=False)

    native_diag = pd.read_csv(native_diag_path)
    stata_diag = _read_csv_if_exists(stata_diag_path)

    if stata_diag is not None and not stata_diag.empty:
        diag = pd.concat(
            [
                native_diag.add_prefix("native_file_"),
                stata_diag.add_prefix("stata_file_"),
            ],
            axis=1,
        )
    else:
        diag = native_diag.copy()
        diag["stata_status"] = "PENDING_RUN_STATA_DOFILE"

    diag.to_csv(OUT / "xtabond2_native_system_gmm_diagnostics_comparison.csv", index=False)

    md = [
        "# xtabond2 vs Native System GMM Parity",
        "",
        "## Status",
        "",
    ]

    if stata_diag_path is not None and stata_params_path is not None:
        md.append("Stata xtabond2 outputs detected. Comparison generated.")
    else:
        md.append("Native outputs generated. Stata xtabond2 outputs pending. Run the generated `.do` file in Stata.")

    md.extend(
        [
            "",
            "## Artifact Sources",
            "",
            f"- Native parameters: `{native_params_path.as_posix()}`",
            f"- Native diagnostics: `{native_diag_path.as_posix()}`",
            f"- Stata parameters: `{stata_params_path.as_posix() if stata_params_path else 'PENDING'}`",
            f"- Stata diagnostics: `{stata_diag_path.as_posix() if stata_diag_path else 'PENDING'}`",
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
            "This comparator prefers the isolated baseline Windmeijer native artifacts and falls back to the legacy top-level native artifacts only when required.",
            "",
        ]
    )

    (OUT / "xtabond2_native_system_gmm_parity.md").write_text("\n".join(md), encoding="utf-8")

    print(f"Wrote comparison outputs to {OUT}")
    print(f"Native params: {native_params_path}")
    print(f"Native diagnostics: {native_diag_path}")
    print(f"Stata params: {stata_params_path if stata_params_path else 'PENDING'}")
    print(f"Stata diagnostics: {stata_diag_path if stata_diag_path else 'PENDING'}")


if __name__ == "__main__":
    main()