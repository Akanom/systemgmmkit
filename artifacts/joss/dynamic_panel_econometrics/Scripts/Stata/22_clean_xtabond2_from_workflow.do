capture log close _all
clear all
set more off
version 17.0

cd "C:/Users/omoko/OneDrive/Papers/Dynamic_Panel_Econometrics"

log using "Results/stata/22_clean_xtabond2_from_workflow.log", replace text

capture which xtabond2
if _rc {
    ssc install xtabond2, replace
}

********************************************************************************
* Difference GMM
********************************************************************************

clear
import delimited "Artifacts/Joss/tables/22_debug_workflow/difference_gmm_data.csv", clear varnames(1)

capture confirm variable l1_y
if _rc {
    capture confirm variable L1_y
    if !_rc rename L1_y l1_y
}

xtset id time

display "======================================================================"
display "Difference GMM: noleveleq, default IV scope"
display "======================================================================"

xtabond2 y x_pred x_exog l1_y if time >= 4, ///
    gmmstyle(l1_y, lag(2 3) collapse) ///
    gmmstyle(x_pred, lag(2 3) collapse) ///
    ivstyle(x_exog) ///
    noleveleq ///
    twostep robust small

tempfile diffcoef
tempname dh

postfile `dh' str30 model str30 term double coefficient double std_error double z_value double p_value using "`diffcoef'", replace

foreach v in x_pred x_exog l1_y {
    capture scalar b = _b[`v']
    if !_rc {
        scalar se = _se[`v']
        scalar z = b / se
        scalar p = 2 * normal(-abs(z))
        post `dh' ("Difference GMM") ("`v'") (b) (se) (z) (p)
    }
}

postclose `dh'

use "`diffcoef'", clear
export delimited using "Results/stata/22_clean_stata_difference_gmm_coefficients.csv", replace
copy "Results/stata/22_clean_stata_difference_gmm_coefficients.csv" "Artifacts/Joss/tables/22_stata_difference_gmm_coefficients.csv", replace
copy "Results/stata/22_clean_stata_difference_gmm_coefficients.csv" "Artifacts/Joss/tables/22_clean_stata_difference_gmm_coefficients.csv", replace

********************************************************************************
* System GMM
********************************************************************************

clear
import delimited "Artifacts/Joss/tables/22_debug_workflow/system_gmm_data.csv", clear varnames(1)

capture confirm variable l1_y
if _rc {
    capture confirm variable L1_y
    if !_rc rename L1_y l1_y
}

xtset id time

display "======================================================================"
display "System GMM: level equation included, x_exog as level-equation IV"
display "======================================================================"

xtabond2 y x_pred x_exog l1_y if time >= 3, ///
    gmmstyle(l1_y, lag(2 3) collapse) ///
    gmmstyle(x_pred, lag(2 3) collapse) ///
    ivstyle(x_exog, equation(level)) ///
    twostep robust small

tempfile syscoef
tempname sh

postfile `sh' str30 model str30 term double coefficient double std_error double z_value double p_value using "`syscoef'", replace

foreach v in x_pred x_exog l1_y {
    capture scalar b = _b[`v']
    if !_rc {
        scalar se = _se[`v']
        scalar z = b / se
        scalar p = 2 * normal(-abs(z))
        post `sh' ("System GMM") ("`v'") (b) (se) (z) (p)
    }
}

capture scalar b = _b[_cons]
if !_rc {
    scalar se = _se[_cons]
    scalar z = b / se
    scalar p = 2 * normal(-abs(z))
    post `sh' ("System GMM") ("const") (b) (se) (z) (p)
}

postclose `sh'

use "`syscoef'", clear
export delimited using "Results/stata/22_clean_stata_system_gmm_coefficients.csv", replace
copy "Results/stata/22_clean_stata_system_gmm_coefficients.csv" "Artifacts/Joss/tables/22_stata_system_gmm_coefficients.csv", replace
copy "Results/stata/22_clean_stata_system_gmm_coefficients.csv" "Artifacts/Joss/tables/22_clean_stata_system_gmm_coefficients.csv", replace

log close

