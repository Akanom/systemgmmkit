clear all
set more off
set varabbrev off
capture log close _all

log using "C:/Users/omoko/OneDrive/Python packages/systemgmmkit/artifacts/parity/xtdpdgmm/fod_diff/fod_diff_xtdpdgmm_reference.log", text replace

display as text "============================================================"
display as text "FOD Difference GMM reference using xtdpdgmm model(fodev)"
display as text "Repo: C:/Users/omoko/OneDrive/Python packages/systemgmmkit"
display as text "Data: C:/Users/omoko/OneDrive/Python packages/systemgmmkit/artifacts/parity/xtabond2/system_gmm_benchmark.csv"
display as text "Output: C:/Users/omoko/OneDrive/Python packages/systemgmmkit/artifacts/parity/xtdpdgmm/fod_diff"
display as text "============================================================"

capture which xtdpdgmm
if _rc {
    display as error "xtdpdgmm not found. Install manually in Stata with: ssc install xtdpdgmm, replace"
    exit 499
}

confirm file "C:/Users/omoko/OneDrive/Python packages/systemgmmkit/artifacts/parity/xtabond2/system_gmm_benchmark.csv"

import delimited using "C:/Users/omoko/OneDrive/Python packages/systemgmmkit/artifacts/parity/xtabond2/system_gmm_benchmark.csv", clear varnames(1) numericcols(_all)

describe

confirm variable id
confirm variable t
confirm variable y
confirm variable x
confirm variable w

sort id t
xtset id t

capture program drop export_last_xtdpdgmm
program define export_last_xtdpdgmm
    syntax, SPEC(string) OUTPUT(string)

    tempname b V
    matrix `b' = e(b)
    matrix `V' = e(V)

    local cn : colfullnames `b'
    local k = colsof(`b')

    preserve
        clear
        set obs `k'

        gen str80 spec = "`spec'"
        gen str80 term = ""
        gen double stata_coef = .
        gen double stata_std_err = .
        gen double stata_z = .
        gen double stata_p_value = .

        local j = 1
        foreach nm of local cn {
            replace term = "`nm'" in `j'
            replace stata_coef = el(`b', 1, `j') in `j'
            replace stata_std_err = sqrt(el(`V', `j', `j')) in `j'
            replace stata_z = stata_coef / stata_std_err in `j'
            replace stata_p_value = 2 * normal(-abs(stata_z)) in `j'
            local ++j
        }

        gen double e_N = .
        gen double e_N_g = .
        gen double e_j = .
        gen double e_j_p = .
        gen double e_hansen = .
        gen double e_hansenp = .
        gen double e_sargan = .
        gen double e_sarganp = .
        gen double e_ar1 = .
        gen double e_ar1p = .
        gen double e_ar2 = .
        gen double e_ar2p = .

        capture replace e_N = e(N) in 1
        capture replace e_N_g = e(N_g) in 1
        capture replace e_j = e(j) in 1
        capture replace e_j_p = e(j_p) in 1
        capture replace e_hansen = e(hansen) in 1
        capture replace e_hansenp = e(hansenp) in 1
        capture replace e_sargan = e(sargan) in 1
        capture replace e_sarganp = e(sarganp) in 1
        capture replace e_ar1 = e(ar1) in 1
        capture replace e_ar1p = e(ar1p) in 1
        capture replace e_ar2 = e(ar2) in 1
        capture replace e_ar2p = e(ar2p) in 1

        export delimited using "`output'", replace
    restore
end

display as text "============================================================"
display as text "SPEC 1: x endogenous, one-step"
display as text "============================================================"

xtdpdgmm L(0/1).y x w, ///
    model(fodev) ///
    collapse ///
    gmm(y, lag(1 2)) ///
    gmm(x, lag(1 2)) ///
    iv(w) ///
    nocons ///
    vce(r)

ereturn list
matrix list e(b)
matrix list e(V)
export_last_xtdpdgmm, spec("fod_diff_endog_x_onestep") output("C:/Users/omoko/OneDrive/Python packages/systemgmmkit/artifacts/parity/xtdpdgmm/fod_diff/stata_fod_diff_endog_x_onestep.csv")


display as text "============================================================"
display as text "SPEC 2: x endogenous, two-step"
display as text "============================================================"

xtdpdgmm L(0/1).y x w, ///
    model(fodev) ///
    collapse ///
    gmm(y, lag(1 2)) ///
    gmm(x, lag(1 2)) ///
    iv(w) ///
    nocons ///
    two vce(r)

ereturn list
matrix list e(b)
matrix list e(V)
export_last_xtdpdgmm, spec("fod_diff_endog_x_twostep") output("C:/Users/omoko/OneDrive/Python packages/systemgmmkit/artifacts/parity/xtdpdgmm/fod_diff/stata_fod_diff_endog_x_twostep.csv")


display as text "============================================================"
display as text "SPEC 3: x predetermined, one-step"
display as text "============================================================"

xtdpdgmm L(0/1).y x w, ///
    model(fodev) ///
    collapse ///
    gmm(y, lag(1 2)) ///
    gmm(x, lag(0 1)) ///
    iv(w) ///
    nocons ///
    vce(r)

ereturn list
matrix list e(b)
matrix list e(V)
export_last_xtdpdgmm, spec("fod_diff_predet_x_onestep") output("C:/Users/omoko/OneDrive/Python packages/systemgmmkit/artifacts/parity/xtdpdgmm/fod_diff/stata_fod_diff_predet_x_onestep.csv")


display as text "============================================================"
display as text "SPEC 4: x predetermined, two-step"
display as text "============================================================"

xtdpdgmm L(0/1).y x w, ///
    model(fodev) ///
    collapse ///
    gmm(y, lag(1 2)) ///
    gmm(x, lag(0 1)) ///
    iv(w) ///
    nocons ///
    two vce(r)

ereturn list
matrix list e(b)
matrix list e(V)
export_last_xtdpdgmm, spec("fod_diff_predet_x_twostep") output("C:/Users/omoko/OneDrive/Python packages/systemgmmkit/artifacts/parity/xtdpdgmm/fod_diff/stata_fod_diff_predet_x_twostep.csv")

display as text "============================================================"
display as text "FOD xtdpdgmm oracle export complete"
display as text "============================================================"

log close
exit, clear
