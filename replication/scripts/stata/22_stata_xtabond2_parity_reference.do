version 14
clear all
set more off

* Manual Stata reference run for the JSS controlled Dynamic GMM example.
* Run from the repository root, or pass the repository root as the first argument:
*   do replication/scripts/stata/jss_dynamic_gmm_manual.do "C:/path/to/systemgmmkit"
*
* The execution date is provenance only. It is not a parity condition because
* local Stata installations can format dates differently.

args project_root
if `"`project_root'"' == "" {
    local project_root `"`c(pwd)'"'
}

local data_file `"`project_root'/data/synthetic/22_dynamic_gmm_controlled_panel.csv"'
local output_dir `"`project_root'/artifacts/jss/stata_manual"'

capture confirm file `"`data_file'"'
if _rc {
    display as error "Missing prepared fixture: `data_file'"
    display as error "Run: py -3.14 replication/scripts/python/10_controlled_dynamic_gmm.py"
    exit 601
}

capture which xtabond2
if _rc {
    display as error "xtabond2 is required. Install it once with: ssc install xtabond2"
    exit 199
}

capture which parmest
if _rc {
    display as error "parmest is required for tidy coefficient export. Install it once with: ssc install parmest"
    exit 199
}

capture mkdir `"`project_root'/artifacts"'
capture mkdir `"`project_root'/artifacts/jss"'
capture mkdir `"`output_dir'"'

capture log close _all
log using `"`output_dir'/jss_dynamic_gmm_manual.log"', text replace name(jss_gmm)

display as text "Stata version: `c(stata_version)'"
display as text "Run date (provenance only): `c(current_date)'"
display as text "Run time (provenance only): `c(current_time)'"
display as text "Input: `data_file'"

import delimited using `"`data_file'"', clear varnames(1)
isid id time, sort
xtset id time

tempfile difference_params system_params difference_diag system_diag

* Difference GMM: y and x_pred use collapsed lags 2:3; x_exog is IV-style.
xtabond2 y L.y x_pred x_exog, ///
    gmmstyle(y, lag(2 3) collapse) ///
    gmmstyle(x_pred, lag(2 3) collapse) ///
    ivstyle(x_exog) ///
    noleveleq twostep robust small

parmest, saving(`"`difference_params'"', replace)
preserve
clear
set obs 1
generate str32 model = "difference_gmm_controlled"
generate double n_obs = e(N)
generate double n_groups = e(N_g)
generate double n_instruments = e(j)
generate double hansen_chi2 = e(hansen)
generate double hansen_p = e(hansenp)
generate double hansen_df = e(hansen_df)
generate double ar1_z = e(ar1)
generate double ar1_p = e(ar1p)
generate double ar2_z = e(ar2)
generate double ar2_p = e(ar2p)
save `"`difference_diag'"', replace
restore

* System GMM with the same roles and lag window.
xtabond2 y L.y x_pred x_exog, ///
    gmmstyle(y, lag(2 3) collapse) ///
    gmmstyle(x_pred, lag(2 3) collapse) ///
    ivstyle(x_exog) ///
    twostep robust small

parmest, saving(`"`system_params'"', replace)
preserve
clear
set obs 1
generate str32 model = "system_gmm_controlled"
generate double n_obs = e(N)
generate double n_groups = e(N_g)
generate double n_instruments = e(j)
generate double hansen_chi2 = e(hansen)
generate double hansen_p = e(hansenp)
generate double hansen_df = e(hansen_df)
generate double ar1_z = e(ar1)
generate double ar1_p = e(ar1p)
generate double ar2_z = e(ar2)
generate double ar2_p = e(ar2p)
save `"`system_diag'"', replace
restore

use `"`difference_params'"', clear
generate str32 model = "difference_gmm_controlled"
append using `"`system_params'"'
replace model = "system_gmm_controlled" if missing(model)
order model parm estimate stderr t p min95 max95
export delimited using `"`output_dir'/jss_dynamic_gmm_parameters.csv"', replace

use `"`difference_diag'"', clear
append using `"`system_diag'"'
export delimited using `"`output_dir'/jss_dynamic_gmm_diagnostics.csv"', replace

display as result "JSS Stata reference run completed."
display as result "Outputs: `output_dir'"
log close jss_gmm
