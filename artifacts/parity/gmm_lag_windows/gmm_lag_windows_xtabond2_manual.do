********************************************************************************
* systemgmmkit manual Stata parity check
* Run this file manually in Stata.
*
* IMPORTANT:
* 1. Load the existing parity dataset before running these commands, OR
* 2. Add the dataset import/use command below before xtset.
*
* Required variables for this generated check:
*   id, t, y, x, cashflow
********************************************************************************

cd "C:/Users/omoko/OneDrive/Python packages/systemgmmkit"

capture mkdir "artifacts"
capture mkdir "artifacts/parity"
capture mkdir "artifacts/parity/gmm_lag_windows"

capture log close
log using "artifacts/parity/gmm_lag_windows/gmm_lag_windows_xtabond2_manual.log", replace text

* Example if using a Stata dataset:
* use "path/to/your/parity_dataset.dta", clear

clear all
set more off
set seed 12345

set obs 960
gen id = ceil(_n / 10)
bysort id: gen t = _n

gen x = rnormal()
gen cashflow = rnormal()
gen firm_size = rnormal()

gen y = .
bysort id (t): replace y = rnormal() if t == 1
bysort id (t): replace y = 0.55 * y[_n-1] + 0.80 * x + 0.35 * cashflow + rnormal() if t > 1

drop if missing(y, x, cashflow)



********************************************************************************
* m_base
********************************************************************************
xtset id t
xtabond2 y L1.y x, gmmstyle(y, lag(2 3) collapse) gmmstyle(x, lag(2 2) collapse) ivstyle(i.t, equation(level)) twostep robust small orthogonal
estimates store m_base

matrix b_m_base = e(b)
matrix V_m_base = e(V)

display "MODEL=m_base"
display "N=" e(N)
display "N_g=" e(N_g)
display "j=" e(j)
display "j_df_raw=" e(j_df)

scalar __sgmmkit_overid_df = .
scalar __sgmmkit_overid_df_source = 0

capture scalar __sgmmkit_overid_df = e(j_df)
if !missing(__sgmmkit_overid_df) {
    scalar __sgmmkit_overid_df_source = 1
}

if missing(__sgmmkit_overid_df) {
    capture scalar __sgmmkit_overid_df = e(hansen_df)
    if !_rc & !missing(__sgmmkit_overid_df) {
        scalar __sgmmkit_overid_df_source = 2
    }
}

if missing(__sgmmkit_overid_df) {
    capture scalar __sgmmkit_overid_df = e(df_hansen)
    if !_rc & !missing(__sgmmkit_overid_df) {
        scalar __sgmmkit_overid_df_source = 3
    }
}

if missing(__sgmmkit_overid_df) {
    capture scalar __sgmmkit_overid_df = e(j) - colsof(e(b))
    if !_rc & !missing(__sgmmkit_overid_df) {
        scalar __sgmmkit_overid_df_source = 4
    }
}

if missing(__sgmmkit_overid_df) | __sgmmkit_overid_df < 0 {
    display as error "BLOCKED: could not recover Hansen/Sargan overidentification degrees of freedom."
    display as error "Run ereturn list after xtabond2 and inspect stored diagnostics."
    ereturn list
    exit 459
}

display "j_df_effective=" __sgmmkit_overid_df
display "j_df_source=" __sgmmkit_overid_df_source
display "k_instruments_ej=" e(j)
display "k_params_colsof_eb=" colsof(e(b))
display "hansenp=" e(hansenp)
display "sarganp=" e(sarganp)
display "ar1p=" e(ar1p)
display "ar2p=" e(ar2p)

********************************************************************************
* m_role
********************************************************************************
xtset id t
xtabond2 y L1.y x cashflow, gmmstyle(y, lag(2 5) collapse) gmmstyle(x, lag(2 5) collapse) gmmstyle(cashflow, lag(1 3) collapse) ivstyle(i.t, equation(level)) twostep robust small orthogonal
estimates store m_role

matrix b_m_role = e(b)
matrix V_m_role = e(V)

display "MODEL=m_role"
display "N=" e(N)
display "N_g=" e(N_g)
display "j=" e(j)
display "j_df_raw=" e(j_df)

scalar __sgmmkit_overid_df = .
scalar __sgmmkit_overid_df_source = 0

capture scalar __sgmmkit_overid_df = e(j_df)
if !missing(__sgmmkit_overid_df) {
    scalar __sgmmkit_overid_df_source = 1
}

if missing(__sgmmkit_overid_df) {
    capture scalar __sgmmkit_overid_df = e(hansen_df)
    if !_rc & !missing(__sgmmkit_overid_df) {
        scalar __sgmmkit_overid_df_source = 2
    }
}

if missing(__sgmmkit_overid_df) {
    capture scalar __sgmmkit_overid_df = e(df_hansen)
    if !_rc & !missing(__sgmmkit_overid_df) {
        scalar __sgmmkit_overid_df_source = 3
    }
}

if missing(__sgmmkit_overid_df) {
    capture scalar __sgmmkit_overid_df = e(j) - colsof(e(b))
    if !_rc & !missing(__sgmmkit_overid_df) {
        scalar __sgmmkit_overid_df_source = 4
    }
}

if missing(__sgmmkit_overid_df) | __sgmmkit_overid_df < 0 {
    display as error "BLOCKED: could not recover Hansen/Sargan overidentification degrees of freedom."
    display as error "Run ereturn list after xtabond2 and inspect stored diagnostics."
    ereturn list
    exit 459
}

display "j_df_effective=" __sgmmkit_overid_df
display "j_df_source=" __sgmmkit_overid_df_source
display "k_instruments_ej=" e(j)
display "k_params_colsof_eb=" colsof(e(b))
display "hansenp=" e(hansenp)
display "sarganp=" e(sarganp)
display "ar1p=" e(ar1p)
display "ar2p=" e(ar2p)

********************************************************************************
* m_var
********************************************************************************
xtset id t
xtabond2 y L1.y x cashflow, gmmstyle(y, lag(2 4) collapse) gmmstyle(x, lag(3 5) collapse) gmmstyle(cashflow, lag(1 2) collapse) ivstyle(i.t, equation(level)) twostep robust small orthogonal
estimates store m_var

matrix b_m_var = e(b)
matrix V_m_var = e(V)

display "MODEL=m_var"
display "N=" e(N)
display "N_g=" e(N_g)
display "j=" e(j)
display "j_df_raw=" e(j_df)

scalar __sgmmkit_overid_df = .
scalar __sgmmkit_overid_df_source = 0

capture scalar __sgmmkit_overid_df = e(j_df)
if !missing(__sgmmkit_overid_df) {
    scalar __sgmmkit_overid_df_source = 1
}

if missing(__sgmmkit_overid_df) {
    capture scalar __sgmmkit_overid_df = e(hansen_df)
    if !_rc & !missing(__sgmmkit_overid_df) {
        scalar __sgmmkit_overid_df_source = 2
    }
}

if missing(__sgmmkit_overid_df) {
    capture scalar __sgmmkit_overid_df = e(df_hansen)
    if !_rc & !missing(__sgmmkit_overid_df) {
        scalar __sgmmkit_overid_df_source = 3
    }
}

if missing(__sgmmkit_overid_df) {
    capture scalar __sgmmkit_overid_df = e(j) - colsof(e(b))
    if !_rc & !missing(__sgmmkit_overid_df) {
        scalar __sgmmkit_overid_df_source = 4
    }
}

if missing(__sgmmkit_overid_df) | __sgmmkit_overid_df < 0 {
    display as error "BLOCKED: could not recover Hansen/Sargan overidentification degrees of freedom."
    display as error "Run ereturn list after xtabond2 and inspect stored diagnostics."
    ereturn list
    exit 459
}

display "j_df_effective=" __sgmmkit_overid_df
display "j_df_source=" __sgmmkit_overid_df_source
display "k_instruments_ej=" e(j)
display "k_params_colsof_eb=" colsof(e(b))
display "hansenp=" e(hansenp)
display "sarganp=" e(sarganp)
display "ar1p=" e(ar1p)
display "ar2p=" e(ar2p)

log close

********************************************************************************
* End of manual parity file
********************************************************************************


