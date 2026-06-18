
********************************************************************************
* systemgmmkit real-data manual Stata parity check
* Feature: role-specific and variable-specific GMM lag windows
*
* Run manually in Stata.
********************************************************************************

clear all
set more off

cd "C:/Users/omoko/OneDrive/Python packages/systemgmmkit"

capture mkdir "artifacts"
capture mkdir "artifacts/parity"
capture mkdir "artifacts/parity/gmm_lag_windows_realdata"

capture log close
log using "artifacts/parity/gmm_lag_windows_realdata/gmm_lag_windows_realdata_xtabond2.log", replace text

import delimited "artifacts/parity/xtabond2/system_gmm_benchmark.csv", clear varnames(1)

describe
summarize y x w id t

confirm variable id
confirm variable t
confirm variable y
confirm variable x
confirm variable w

xtset id t

capture which xtabond2
if _rc {
    display as error "BLOCKED: xtabond2 is not installed or not visible to Stata."
    exit 499
}

capture program drop sgmmkit_export_xtabond2
program define sgmmkit_export_xtabond2
    syntax, MODEL(name)

    estimates store `model'

    display "MODEL=`model'"
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
        ereturn list
        exit 459
    }

    scalar __sgmmkit_hansen_p = .
    scalar __sgmmkit_sargan_p = .
    scalar __sgmmkit_ar1_p = .
    scalar __sgmmkit_ar2_p = .

    capture scalar __sgmmkit_hansen_p = e(hansenp)
    capture scalar __sgmmkit_sargan_p = e(sarganp)
    capture scalar __sgmmkit_ar1_p = e(ar1p)
    capture scalar __sgmmkit_ar2_p = e(ar2p)

    display "j_df_effective=" __sgmmkit_overid_df
    display "j_df_source=" __sgmmkit_overid_df_source
    display "k_instruments_ej=" e(j)
    display "k_params_colsof_eb=" colsof(e(b))
    display "hansenp=" __sgmmkit_hansen_p
    display "sarganp=" __sgmmkit_sargan_p
    display "ar1p=" __sgmmkit_ar1_p
    display "ar2p=" __sgmmkit_ar2_p

    matrix __b = e(b)
    matrix __V = e(V)
    local names : colnames __b
    local k = colsof(__b)

    preserve
        clear
        set obs `k'
        gen str64 model = "`model'"
        gen str64 param = ""
        gen coef = .
        gen std_err = .
        gen z = .
        gen p_value = .

        local i = 1
        foreach nm of local names {
            replace param = "`nm'" in `i'
            replace coef = __b[1, `i'] in `i'
            replace std_err = sqrt(__V[`i', `i']) in `i'
            replace z = coef / std_err in `i'
            replace p_value = 2 * normal(-abs(z)) in `i'
            local ++i
        }

        export delimited using "artifacts/parity/gmm_lag_windows_realdata/`model'_params.csv", replace
    restore

    preserve
        clear
        set obs 1
        gen str64 model = "`model'"
        gen N = e(N)
        gen N_g = e(N_g)
        gen k_instruments = e(j)
        gen k_params = colsof(e(b))
        gen overid_df = __sgmmkit_overid_df
        gen overid_df_source = __sgmmkit_overid_df_source
        gen hansen_p = __sgmmkit_hansen_p
        gen sargan_p = __sgmmkit_sargan_p
        gen ar1_p = __sgmmkit_ar1_p
        gen ar2_p = __sgmmkit_ar2_p

        export delimited using "artifacts/parity/gmm_lag_windows_realdata/`model'_diagnostics.csv", replace
    restore
end

********************************************************************************
* 1. Baseline backward compatibility
* Expected:
*   y -> lag(2 3)
*   x -> lag(2 2)
*   w -> IV-style
********************************************************************************

xtabond2 y L1.y x w, ///
    gmmstyle(y, lag(2 3) collapse) ///
    gmmstyle(x, lag(2 2) collapse) ///
    ivstyle(w, equation(level)) ///
    ivstyle(i.t, equation(level)) ///
    twostep robust small orthogonal

sgmmkit_export_xtabond2, model(m_base)

********************************************************************************
* 2. Role-specific lag windows
* Expected:
*   y -> lag(2 5)
*   x -> lag(2 5)
*   w -> lag(1 3)
********************************************************************************

xtabond2 y L1.y x w, ///
    gmmstyle(y, lag(2 5) collapse) ///
    gmmstyle(x, lag(2 5) collapse) ///
    gmmstyle(w, lag(1 3) collapse) ///
    ivstyle(i.t, equation(level)) ///
    twostep robust small orthogonal

sgmmkit_export_xtabond2, model(m_role)

********************************************************************************
* 3. Variable-specific overrides
* Expected:
*   y -> lag(2 4)
*   x -> lag(3 5)
*   w -> lag(1 2)
********************************************************************************

xtabond2 y L1.y x w, ///
    gmmstyle(y, lag(2 4) collapse) ///
    gmmstyle(x, lag(3 5) collapse) ///
    gmmstyle(w, lag(1 2) collapse) ///
    ivstyle(i.t, equation(level)) ///
    twostep robust small orthogonal

sgmmkit_export_xtabond2, model(m_var)

log close

********************************************************************************
* End
********************************************************************************
