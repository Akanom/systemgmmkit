from pathlib import Path

repo = Path.cwd().as_posix()
out = Path("artifacts/parity/gmm_lag_windows_realdata_notime")
out.mkdir(parents=True, exist_ok=True)

data = Path("artifacts/parity/xtabond2/system_gmm_benchmark.csv").as_posix()

do = f'''
clear all
set more off

cd "{repo}"

capture mkdir "artifacts"
capture mkdir "artifacts/parity"
capture mkdir "artifacts/parity/gmm_lag_windows_realdata_notime"

capture log close
log using "artifacts/parity/gmm_lag_windows_realdata_notime/xtabond2_notime.log", replace text

import delimited "{data}", clear varnames(1)

confirm variable id
confirm variable t
confirm variable y
confirm variable x
confirm variable w

xtset id t

capture which xtabond2
if _rc {{
    display as error "BLOCKED: xtabond2 not installed."
    exit 499
}}

capture program drop export_model
program define export_model
    syntax, MODEL(name)

    estimates store `model'

    scalar __overid_df = .
    scalar __overid_source = 0

    capture scalar __overid_df = e(j_df)
    if !missing(__overid_df) {{
        scalar __overid_source = 1
    }}

    if missing(__overid_df) {{
        capture scalar __overid_df = e(hansen_df)
        if !_rc & !missing(__overid_df) {{
            scalar __overid_source = 2
        }}
    }}

    if missing(__overid_df) {{
        capture scalar __overid_df = e(df_hansen)
        if !_rc & !missing(__overid_df) {{
            scalar __overid_source = 3
        }}
    }}

    if missing(__overid_df) {{
        capture scalar __overid_df = e(j) - colsof(e(b))
        if !_rc & !missing(__overid_df) {{
            scalar __overid_source = 4
        }}
    }}

    if missing(__overid_df) | __overid_df < 0 {{
        display as error "BLOCKED: overidentification df could not be recovered."
        ereturn list
        exit 459
    }}

    display "MODEL=`model'"
    display "N=" e(N)
    display "N_g=" e(N_g)
    display "j=" e(j)
    display "j_df_effective=" __overid_df
    display "j_df_source=" __overid_source
    display "hansenp=" e(hansenp)
    display "sarganp=" e(sarganp)
    display "ar1p=" e(ar1p)
    display "ar2p=" e(ar2p)

    matrix b = e(b)
    matrix V = e(V)
    local names : colnames b
    local k = colsof(b)

    preserve
        clear
        set obs `k'
        gen str32 model = "`model'"
        gen str32 param = ""
        gen coef = .
        gen std_err = .

        local i = 1
        foreach nm of local names {{
            replace param = "`nm'" in `i'
            replace coef = b[1, `i'] in `i'
            replace std_err = sqrt(V[`i', `i']) in `i'
            local ++i
        }}

        export delimited using "artifacts/parity/gmm_lag_windows_realdata_notime/`model'_params.csv", replace
    restore

    preserve
        clear
        set obs 1
        gen str32 model = "`model'"
        gen N = e(N)
        gen N_g = e(N_g)
        gen k_instruments = e(j)
        gen k_params = colsof(e(b))
        gen overid_df = __overid_df
        gen overid_df_source = __overid_source
        gen hansen_p = e(hansenp)
        gen sargan_p = e(sarganp)
        gen ar1_p = e(ar1p)
        gen ar2_p = e(ar2p)

        export delimited using "artifacts/parity/gmm_lag_windows_realdata_notime/`model'_diagnostics.csv", replace
    restore
end

********************************************************************************
* m_base: backward-compatible default
********************************************************************************

xtabond2 y L1.y x w, ///
    gmmstyle(y, lag(2 3) collapse) ///
    gmmstyle(x, lag(2 2) collapse) ///
    ivstyle(w, equation(level)) ///
    twostep robust small orthogonal

export_model, model(m_base)

********************************************************************************
* m_role: role-specific lag windows
********************************************************************************

xtabond2 y L1.y x w, ///
    gmmstyle(y, lag(2 5) collapse) ///
    gmmstyle(x, lag(2 5) collapse) ///
    gmmstyle(w, lag(1 3) collapse) ///
    twostep robust small orthogonal

export_model, model(m_role)

********************************************************************************
* m_var: variable-specific overrides
********************************************************************************

xtabond2 y L1.y x w, ///
    gmmstyle(y, lag(2 4) collapse) ///
    gmmstyle(x, lag(3 5) collapse) ///
    gmmstyle(w, lag(1 2) collapse) ///
    twostep robust small orthogonal

export_model, model(m_var)

log close
'''

path = out / "xtabond2_notime.do"
path.write_text(do, encoding="utf-8")

print(path)
