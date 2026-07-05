version 17.0
capture log close _all
clear all
set more off

********************************************************************************
* systemgmmkit JOSS Artifact 22
* Stata xtabond2 Dynamic GMM parity reference
*
* Run this file from the project root:
* C:/Users/omoko/OneDrive/Papers/Dynamic_Panel_Econometrics
********************************************************************************

capture mkdir "Results"
capture mkdir "Results/stata"
capture mkdir "Artifacts"
capture mkdir "Artifacts/Joss"
capture mkdir "Artifacts/Joss/tables"

log using "Results/stata/22_stata_xtabond2_parity_reference.log", replace text

********************************************************************************
* 1. Load controlled dynamic-panel benchmark
********************************************************************************

import delimited using "Data/Processed/22_dynamic_gmm_controlled_panel.csv", clear varnames(1)

describe
summarize y x_pred x_exog id time

xtset id time

* Stata-side lag check; xtabond2 uses L.y directly after xtset.
capture drop l1_y
gen l1_y = L.y
summarize y l1_y x_pred x_exog id time

********************************************************************************
* 2. Ensure xtabond2 is available
********************************************************************************

capture which xtabond2
if _rc {
    ssc install xtabond2, replace
}

capture which ranktest
if _rc {
    ssc install ranktest, replace
}

********************************************************************************
* 3. Prepare export containers
********************************************************************************

tempname coeffpost diagpost

postfile `coeffpost' ///
    str30 model ///
    str80 term ///
    double coefficient ///
    double std_error ///
    double z_value ///
    double p_value ///
    using "Results/stata/22_stata_xtabond2_coefficients.dta", replace

postfile `diagpost' ///
    str30 model ///
    double N ///
    double groups ///
    double instruments ///
    double hansen_stat ///
    double hansen_p ///
    double sargan_stat ///
    double sargan_p ///
    double ar1_stat ///
    double ar1_p ///
    double ar2_stat ///
    double ar2_p ///
    using "Results/stata/22_stata_xtabond2_diagnostics.dta", replace

********************************************************************************
* Helper block is repeated after each model because Stata programs can be fragile
* across user installations and xtabond2 versions.
********************************************************************************

********************************************************************************
* 4. Difference GMM reference
********************************************************************************

display "======================================================================"
display "Difference GMM: xtabond2 reference"
display "======================================================================"

xtabond2 y x_pred x_exog l1_y, ///
    gmmstyle(l1_y, lag(2 3) collapse) ///
    gmmstyle(x_pred, lag(2 3) collapse) ///
    ivstyle(x_exog) ///
    noleveleq ///
    twostep robust small

ereturn list

matrix b = e(b)
matrix V = e(V)
local cn : colfullnames b
local k = colsof(b)

forvalues j = 1/`k' {
    local term : word `j' of `cn'

    scalar coef = b[1, `j']
    scalar se = sqrt(V[`j', `j'])

    if se == 0 {
        scalar z = .
        scalar p = .
    }
    else {
        scalar z = coef / se
        scalar p = 2 * normal(-abs(z))
    }

    post `coeffpost' ("Difference GMM") ("`term'") (coef) (se) (z) (p)
}

scalar N_val = .
capture scalar N_val = e(N)

scalar groups_val = .
capture scalar groups_val = e(N_g)

scalar inst_val = .
capture scalar inst_val = e(k_instr)
capture scalar inst_val = e(k_inst)

scalar hansen_val = .
capture scalar hansen_val = e(hansen)
capture scalar hansen_val = e(j)

scalar hansen_p_val = .
capture scalar hansen_p_val = e(hansenp)
capture scalar hansen_p_val = e(jp)

scalar sargan_val = .
capture scalar sargan_val = e(sargan)

scalar sargan_p_val = .
capture scalar sargan_p_val = e(sarganp)

scalar ar1_val = .
capture scalar ar1_val = e(ar1)

scalar ar1_p_val = .
capture scalar ar1_p_val = e(ar1p)

scalar ar2_val = .
capture scalar ar2_val = e(ar2)

scalar ar2_p_val = .
capture scalar ar2_p_val = e(ar2p)

post `diagpost' ///
    ("Difference GMM") ///
    (N_val) ///
    (groups_val) ///
    (inst_val) ///
    (hansen_val) ///
    (hansen_p_val) ///
    (sargan_val) ///
    (sargan_p_val) ///
    (ar1_val) ///
    (ar1_p_val) ///
    (ar2_val) ///
    (ar2_p_val)

********************************************************************************
* 5. System GMM reference
********************************************************************************

display "======================================================================"
display "System GMM: xtabond2 reference"
display "======================================================================"

xtabond2 y x_pred x_exog l1_y, ///
    gmmstyle(l1_y, lag(2 3) collapse) ///
    gmmstyle(x_pred, lag(2 3) collapse) ///
    ivstyle(x_exog) ///
    noleveleq ///
    twostep robust small

ereturn list

matrix b = e(b)
matrix V = e(V)
local cn : colfullnames b
local k = colsof(b)

forvalues j = 1/`k' {
    local term : word `j' of `cn'

    scalar coef = b[1, `j']
    scalar se = sqrt(V[`j', `j'])

    if se == 0 {
        scalar z = .
        scalar p = .
    }
    else {
        scalar z = coef / se
        scalar p = 2 * normal(-abs(z))
    }

    post `coeffpost' ("System GMM") ("`term'") (coef) (se) (z) (p)
}

scalar N_val = .
capture scalar N_val = e(N)

scalar groups_val = .
capture scalar groups_val = e(N_g)

scalar inst_val = .
capture scalar inst_val = e(k_instr)
capture scalar inst_val = e(k_inst)

scalar hansen_val = .
capture scalar hansen_val = e(hansen)
capture scalar hansen_val = e(j)

scalar hansen_p_val = .
capture scalar hansen_p_val = e(hansenp)
capture scalar hansen_p_val = e(jp)

scalar sargan_val = .
capture scalar sargan_val = e(sargan)

scalar sargan_p_val = .
capture scalar sargan_p_val = e(sarganp)

scalar ar1_val = .
capture scalar ar1_val = e(ar1)

scalar ar1_p_val = .
capture scalar ar1_p_val = e(ar1p)

scalar ar2_val = .
capture scalar ar2_val = e(ar2)

scalar ar2_p_val = .
capture scalar ar2_p_val = e(ar2p)

post `diagpost' ///
    ("System GMM") ///
    (N_val) ///
    (groups_val) ///
    (inst_val) ///
    (hansen_val) ///
    (hansen_p_val) ///
    (sargan_val) ///
    (sargan_p_val) ///
    (ar1_val) ///
    (ar1_p_val) ///
    (ar2_val) ///
    (ar2_p_val)

********************************************************************************
* 6. Export Stata coefficient and diagnostic outputs
********************************************************************************

postclose `coeffpost'
postclose `diagpost'

use "Results/stata/22_stata_xtabond2_coefficients.dta", clear
export delimited using "Results/stata/22_stata_xtabond2_coefficients.csv", replace

preserve
keep if model == "Difference GMM"
export delimited using "Results/stata/22_stata_difference_gmm_coefficients.csv", replace
restore

preserve
keep if model == "System GMM"
export delimited using "Results/stata/22_stata_system_gmm_coefficients.csv", replace
restore

copy "Results/stata/22_stata_xtabond2_coefficients.csv" ///
     "Artifacts/Joss/tables/22_stata_xtabond2_coefficients.csv", replace

copy "Results/stata/22_stata_difference_gmm_coefficients.csv" ///
     "Artifacts/Joss/tables/22_stata_difference_gmm_coefficients.csv", replace

copy "Results/stata/22_stata_system_gmm_coefficients.csv" ///
     "Artifacts/Joss/tables/22_stata_system_gmm_coefficients.csv", replace

use "Results/stata/22_stata_xtabond2_diagnostics.dta", clear
export delimited using "Results/stata/22_stata_xtabond2_diagnostics.csv", replace

copy "Results/stata/22_stata_xtabond2_diagnostics.csv" ///
     "Artifacts/Joss/tables/22_stata_xtabond2_diagnostics.csv", replace

********************************************************************************
* 7. Finish
********************************************************************************

display "======================================================================"
display "Stata xtabond2 parity reference complete."
display "Outputs:"
display "  Results/stata/22_stata_xtabond2_coefficients.csv"
display "  Results/stata/22_stata_difference_gmm_coefficients.csv"
display "  Results/stata/22_stata_system_gmm_coefficients.csv"
display "  Results/stata/22_stata_xtabond2_diagnostics.csv"
display "  Artifacts/Joss/tables/22_stata_xtabond2_coefficients.csv"
display "  Artifacts/Joss/tables/22_stata_xtabond2_diagnostics.csv"
display "======================================================================"

log close





