version 17.0
clear all
set more off

import delimited using "artifacts/parity/xtabond2/specs/system_gmm_no_controls/system_gmm_no_controls_benchmark.csv", clear

xtset id t

capture which xtabond2
if _rc {
    display as error "xtabond2 is required. Install it explicitly with: ssc install xtabond2, replace"
    exit 499
}

capture which parmest
if _rc {
    display as error "parmest is required. Install it explicitly with: ssc install parmest, replace"
    exit 499
}

quietly findfile xtabond2.ado
local xtabond2_ado_file "`r(fn)'"
tempname xtabond2_ado_handle
file open `xtabond2_ado_handle' using "`xtabond2_ado_file'", read text
file read `xtabond2_ado_handle' xtabond2_ado_header
file close `xtabond2_ado_handle'
local xtabond2_ado_header = strtrim("`xtabond2_ado_header'")

xtabond2 y L.y x, ///
    gmm(L.y x, lag(2 3) collapse eq(both)) ///
    twostep robust small

local xtabond2_e_version "`e(version)'"

matrix b = e(b)
matrix V = e(V)

ereturn list

preserve
clear
set obs 1

gen spec = "system_gmm_no_controls"
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
gen str20 stata_reported_date = c(current_date)
gen str20 stata_reported_time = c(current_time)
gen double stata_version = c(stata_version)
gen str20 xtabond2_e_version = "`xtabond2_e_version'"
gen str80 xtabond2_ado_header = "`xtabond2_ado_header'"

export delimited using "artifacts/parity/xtabond2/specs/system_gmm_no_controls/stata_diagnostics.csv", replace
restore

preserve
clear
svmat double b, names(b)
gen row_id = _n
export delimited using "artifacts/parity/xtabond2/specs/system_gmm_no_controls/stata_b.csv", replace
restore

preserve
clear
svmat double V, names(v)
gen row_id = _n
export delimited using "artifacts/parity/xtabond2/specs/system_gmm_no_controls/stata_V.csv", replace
restore

parmest, saving("artifacts/parity/xtabond2/specs/system_gmm_no_controls/stata_params.dta", replace)

use "artifacts/parity/xtabond2/specs/system_gmm_no_controls/stata_params.dta", clear
export delimited using "artifacts/parity/xtabond2/specs/system_gmm_no_controls/stata_params.csv", replace
