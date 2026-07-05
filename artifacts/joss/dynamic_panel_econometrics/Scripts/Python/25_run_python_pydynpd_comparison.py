from __future__ import annotations

import json
import traceback
from pathlib import Path

import pandas as pd

ROOT = Path(".")
DATA = ROOT / "Data/Processed/22_dynamic_gmm_controlled_panel.csv"
OUT = ROOT / "Artifacts/Joss/tables/25_cross_software_comparison"
OUT.mkdir(parents=True, exist_ok=True)


COMMANDS = {
    "Difference GMM": (
        "y L(1:1).y x_pred x_exog | "
        "gmm(y, 2:3) gmm(x_pred, 2:3) iv(x_exog) | "
        "collapse nolevel"
    ),
    "System GMM": (
        "y L(1:1).y x_pred x_exog | "
        "gmm(y, 2:3) gmm(x_pred, 2:3) iv(x_exog) | "
        "collapse"
    ),
}


TERM_MAP = {
    "L1.y": "L1_y",
    "L.y": "L1_y",
    "L1_y": "L1_y",
    "_con": "const",
    "_cons": "const",
    "const": "const",
    "x_pred": "x_pred",
    "x_exog": "x_exog",
}


def norm_term(x: object) -> str:
    s = str(x).strip()
    return TERM_MAP.get(s, s)


def standardize_pydynpd_table(table: pd.DataFrame, model: str, command: str) -> pd.DataFrame:
    df = table.copy()

    rename = {
        "variable": "term",
        "coefficient": "coefficient",
        "std_err": "std_error",
        "z_value": "statistic",
        "p_value": "p_value",
    }

    df = df.rename(columns=rename)

    required = {"term", "coefficient", "std_error", "p_value"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"pydynpd regression table missing columns: {sorted(missing)}")

    out = pd.DataFrame(
        {
            "model": model,
            "package": "pydynpd",
            "term": df["term"],
            "term_norm": df["term"].map(norm_term),
            "coefficient": pd.to_numeric(df["coefficient"], errors="coerce"),
            "std_error": pd.to_numeric(df["std_error"], errors="coerce"),
            "statistic": pd.to_numeric(df.get("statistic", pd.NA), errors="coerce"),
            "p_value": pd.to_numeric(df["p_value"], errors="coerce"),
            "command": command,
        }
    )

    return out


def main() -> None:
    run_log = []

    if not DATA.exists():
        raise FileNotFoundError(DATA)

    df = pd.read_csv(DATA)

    required_cols = {"id", "time", "y", "x_pred", "x_exog"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Input data missing columns: {sorted(missing)}")

    df["id"] = df["id"].astype(int)
    df["time"] = df["time"].astype(int)

    # Compatibility shim for older pydynpd releases under newer NumPy versions.
    # pydynpd may call np.in1d, which is unavailable in some active NumPy builds.
    import numpy as np

    if not hasattr(np, "in1d"):
        np.in1d = np.isin

    if not hasattr(np, "NaN"):
        np.NaN = np.nan

    try:
        from pydynpd import regression
    except Exception as exc:
        log = {
            "package": "pydynpd",
            "status": "MISSING_OR_IMPORT_ERROR",
            "message": repr(exc),
        }
        (OUT / "25_python_pydynpd_run_log.json").write_text(
            json.dumps(log, indent=2),
            encoding="utf-8",
        )
        print("[ERROR] pydynpd could not be imported.")
        print("Install with: python -m pip install pydynpd")
        return

    for model, command in COMMANDS.items():
        try:
            result = regression.abond(command, df, ["id", "time"])
            table = result.models[0].regression_table

            tidy = standardize_pydynpd_table(table, model, command)

            if model == "Difference GMM":
                out_path = OUT / "25_python_pydynpd_difference_gmm_results.csv"
            else:
                out_path = OUT / "25_python_pydynpd_system_gmm_results.csv"

            tidy.to_csv(out_path, index=False)

            run_log.append(
                {
                    "model": model,
                    "status": "OK",
                    "command": command,
                    "output": str(out_path),
                    "message": "pydynpd run completed",
                }
            )

            print(f"[OK] {model}: wrote {out_path}")

        except Exception as exc:
            run_log.append(
                {
                    "model": model,
                    "status": "ERROR",
                    "command": command,
                    "message": repr(exc),
                    "traceback": traceback.format_exc(),
                }
            )
            print(f"[ERROR] {model}: {exc}")

    log_path = OUT / "25_python_pydynpd_run_log.json"
    log_path.write_text(json.dumps(run_log, indent=2), encoding="utf-8")
    print(f"[DONE] Wrote {log_path}")


if __name__ == "__main__":
    main()
