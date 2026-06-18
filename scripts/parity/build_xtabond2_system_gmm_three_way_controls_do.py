from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path("artifacts/parity/xtabond2/specs/system_gmm_three_way_controls")
DATA = OUT / "system_gmm_three_way_controls_benchmark.csv"
DOFILE = OUT / "system_gmm_three_way_controls.do"


def make_dynamic_panel(seed: int = 5050, n_entities: int = 96, n_periods: int = 14) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []

    for i in range(n_entities):
        y_prev = rng.normal()
        alpha = rng.normal()

        frag_base = rng.normal()
        polity_base = rng.normal()

        for t in range(n_periods):
            x = rng.normal()
            w = rng.normal()
            frag = 0.75 * frag_base + 0.25 * rng.normal()
            polity = 0.75 * polity_base + 0.25 * rng.normal()

            x_frag = x * frag
            x_polity = x * polity
            frag_polity = frag * polity
            x_frag_polity = x * frag * polity

            y = (
                0.42 * y_prev
                + 0.65 * x
                - 0.25 * w
                + 0.18 * frag
                + 0.12 * polity
                + 0.08 * x_frag
                - 0.06 * x_polity
                + 0.04 * frag_polity
                + 0.05 * x_frag_polity
                + alpha
                + 0.02 * t
                + rng.normal(scale=0.4)
            )

            rows.append(
                {
                    "id": i,
                    "t": t,
                    "y": y,
                    "x": x,
                    "w": w,
                    "frag": frag,
                    "polity": polity,
                    "x_frag": x_frag,
                    "x_polity": x_polity,
                    "frag_polity": frag_polity,
                    "x_frag_polity": x_frag_polity,
                }
            )
            y_prev = y

    return pd.DataFrame(rows)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    df = make_dynamic_panel()
    df.to_csv(DATA, index=False)

    do = f"""
clear all
set more off

import delimited using "{DATA.as_posix()}", clear

xtset id t

capture which xtabond2
if _rc {{
    ssc install xtabond2, replace
}}

capture which parmest
if _rc {{
    ssc install parmest, replace
}}

xtabond2 y L.y x frag polity x_frag x_polity frag_polity x_frag_polity w, ///
    gmm(L.y x x_frag_polity, lag(2 3) collapse) ///
    iv(w frag polity x_frag x_polity frag_polity, eq(level)) ///
    twostep robust small

matrix b = e(b)
matrix V = e(V)

ereturn list

preserve
clear
set obs 1

gen spec = "system_gmm_three_way_controls"
gen stata_nobs = e(N)
gen stata_n_groups = e(N_g)
gen stata_n_instruments = e(j)
gen stata_hansen = e(hansen)
gen stata_hansen_p = e(hansenp)
gen stata_hansen_df = e(hansen_df)
gen stata_sargan = e(sargan)
gen stata_sargan_p = e(sarganp)
gen stata_sargan_df = e(sar_df)
gen stata_ar1_z = e(ar1)
gen stata_ar1_p = e(ar1p)
gen stata_ar2_z = e(ar2)
gen stata_ar2_p = e(ar2p)

export delimited using "{(OUT / "stata_diagnostics.csv").as_posix()}", replace
restore

preserve
clear
svmat double b, names(b)
gen row_id = _n
export delimited using "{(OUT / "stata_b.csv").as_posix()}", replace
restore

preserve
clear
svmat double V, names(v)
gen row_id = _n
export delimited using "{(OUT / "stata_V.csv").as_posix()}", replace
restore

parmest, saving("{(OUT / "stata_params.dta").as_posix()}", replace)

use "{(OUT / "stata_params.dta").as_posix()}", clear
export delimited using "{(OUT / "stata_params.csv").as_posix()}", replace
"""

    DOFILE.write_text(do.strip() + "\n", encoding="utf-8")
    print(f"Wrote {DATA}")
    print(f"Wrote {DOFILE}")


if __name__ == "__main__":
    main()
