clear all
set more off

cd "C:/Users/omoko/OneDrive/Papers/Dynamic_Panel_Econometrics"

capture mkdir "Artifacts/Joss/tables/27_static_cross_software_comparison"

import delimited "Data/Processed/22_dynamic_gmm_controlled_panel.csv", clear varnames(1)

sort id time
xtset id time

capture confirm variable L1_y
if _rc {
    by id: gen L1_y = y[_n-1]
}

by id: gen L2_x_pred = x_pred[_n-2]

tempfile static ivdata
preserve
keep if !missing(y, L1_y, x_pred, x_exog)
save `static'
restore

preserve
keep if !missing(y, L1_y, x_pred, x_exog, L2_x_pred)
save `ivdata'
restore

program define export_current_model
    syntax, Modelname(string) Outfile(string)

    preserve
    matrix b = e(b)
    matrix V = e(V)

    local cn : colnames b
    clear
    set obs `: word count `cn''

    gen str40 model = "`modelname'"
    gen str40 software = "Stata"
    gen str40 language = "Stata"
    gen str40 term = ""
    gen coefficient = .
    gen std_error = .
    gen statistic = .
    gen p_value = .

    local i = 1
    foreach v of local cn {
        replace term = "`v'" in `i'
        replace coefficient = b[1, `i'] in `i'
        replace std_error = sqrt(V[`i', `i']) in `i'
        replace statistic = coefficient / std_error in `i'
        replace p_value = 2 * normal(-abs(statistic)) in `i'
        local ++i
    }

    gen str40 term_norm = term
    replace term_norm = "const" if term == "_cons"
    replace term_norm = "L1_y" if term == "L1_y"
    replace term_norm = "x_pred" if term == "x_pred"
    replace term_norm = "x_exog" if term == "x_exog"

    export delimited using "`outfile'", replace
    restore
end

use `static', clear
regress y L1_y x_pred x_exog
export_current_model, modelname("OLS") outfile("Artifacts/Joss/tables/27_static_cross_software_comparison/27_stata_ols_results.csv")

use `static', clear
xtset id time
regress y L1_y x_pred x_exog
export_current_model, modelname("Pooled OLS") outfile("Artifacts/Joss/tables/27_static_cross_software_comparison/27_stata_pooled_ols_results.csv")

use `static', clear
xtset id time
xtreg y L1_y x_pred x_exog, fe
export_current_model, modelname("Fixed Effects") outfile("Artifacts/Joss/tables/27_static_cross_software_comparison/27_stata_fe_results.csv")

use `static', clear
xtset id time
xtreg y L1_y x_pred x_exog, re
export_current_model, modelname("Random Effects") outfile("Artifacts/Joss/tables/27_static_cross_software_comparison/27_stata_re_results.csv")

use `ivdata', clear
ivregress 2sls y L1_y x_exog (x_pred = L2_x_pred)
export_current_model, modelname("2SLS") outfile("Artifacts/Joss/tables/27_static_cross_software_comparison/27_stata_2sls_results.csv")

display "Artifact 27 Stata static comparison completed."
