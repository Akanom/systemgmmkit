from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from systemgmmkit import DynamicPanelSpec, GMMStyle, IVStyle
from systemgmmkit.native_gmm import run_native_dynamic_panel_gmm


OUT = Path("artifacts/parity/xtabond2")
DATA = OUT / "system_gmm_benchmark.csv"


def read_stata_matrix_csv(path: Path) -> np.ndarray | None:
    if not path.exists():
        return None
    df = pd.read_csv(path)
    return df.to_numpy(dtype=float)


def main() -> None:
    df = pd.read_csv(DATA)

    spec = DynamicPanelSpec(
        dependent="y",
        regressors=["L1.y", "x", "w"],
        gmm=[
            GMMStyle(variable="y", min_lag=2, max_lag=3),
            GMMStyle(variable="x", min_lag=2, max_lag=3),
        ],
        iv=[IVStyle(variable="w")],
        time_dummies=False,
        system=True,
        collapse=True,
        transformation="fod",
        steps="twostep",
        name="system_gmm_baseline_controls",
    )

    res = run_native_dynamic_panel_gmm(spec, df, entity="id", time="t")

    A1 = read_stata_matrix_csv(OUT / "stata_A1.csv")
    A2 = read_stata_matrix_csv(OUT / "stata_A2.csv")
    b = read_stata_matrix_csv(OUT / "stata_b.csv")
    V = read_stata_matrix_csv(OUT / "stata_V.csv")
    Ze = read_stata_matrix_csv(OUT / "stata_Ze.csv")

    rows = []

    rows.append(
        {
            "object": "native_result",
            "native_nobs": res.nobs,
            "native_n_instruments": res.n_instruments,
            "native_n_params": len(res.params),
            "native_params": ";".join(res.params.index),
            "native_instruments": ";".join(res.instrument_names or []),
        }
    )

    for name, mat in [
        ("stata_A1", A1),
        ("stata_A2", A2),
        ("stata_b", b),
        ("stata_V", V),
        ("stata_Ze", Ze),
    ]:
        if mat is None:
            rows.append(
                {
                    "object": name,
                    "status": "missing",
                    "shape": None,
                    "frobenius_norm": None,
                    "min": None,
                    "max": None,
                }
            )
        else:
            rows.append(
                {
                    "object": name,
                    "status": "loaded",
                    "shape": str(mat.shape),
                    "frobenius_norm": float(np.linalg.norm(mat)),
                    "min": float(np.nanmin(mat)),
                    "max": float(np.nanmax(mat)),
                }
            )

    out = pd.DataFrame(rows)
    out.to_csv(OUT / "native_stata_matrix_comparison.csv", index=False)

    md = []
    md.append("# Native vs Stata Matrix Comparison")
    md.append("")
    md.append("This report checks whether Stata matrix exports are available and summarizes their dimensions/norms.")
    md.append("")
    md.append(out.to_markdown(index=False))
    md.append("")
    md.append("## Interpretation")
    md.append("")
    md.append("- `stata_A2` is the key matrix for two-step weighting comparison.")
    md.append("- `stata_Ze` is useful for checking moment aggregation scale.")
    md.append("- Native does not yet expose its full W/Z matrices, so direct matrix parity is pending.")
    md.append("- Next patch should expose native W, Z shape, and optionally Z matrix under a debug flag.")

    (OUT / "native_stata_matrix_comparison.md").write_text("\n".join(md), encoding="utf-8")

    print(out.to_string(index=False))
    print(f"Wrote {OUT / 'native_stata_matrix_comparison.csv'}")
    print(f"Wrote {OUT / 'native_stata_matrix_comparison.md'}")


if __name__ == "__main__":
    main()