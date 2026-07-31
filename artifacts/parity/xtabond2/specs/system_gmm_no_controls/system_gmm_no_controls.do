version 17.0
clear all
set more off

import delimited using "artifacts/parity/xtabond2/specs/system_gmm_no_controls/system_gmm_no_controls_benchmark.csv", clear

xtset id t

capture which xtabond2
if _rc {
    ssc install xtabond2, replace
}

capture which parmest
if _rc {
    ssc install parmest, replace
}

xtabond2 y L.y x, ///
    gmm(L.y x, lag(2 3) collapse eq(both)) ///
    twostep robust small

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
