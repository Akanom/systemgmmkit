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

capture program drop dump_xtdpdgmm_diag
program define dump_xtdpdgmm_diag
    syntax, Spec(string) Outfile(string)

    preserve
        clear
        set obs 1

        gen str80 spec = "`spec'"

        gen double N          = .
        gen double N_g        = .
        gen double k          = .
        gen double k_eq       = .
        gen double k_inst     = .
        gen double j          = .
        gen double j_p        = .
        gen double hansen     = .
        gen double hansen_p   = .
        gen double sargan     = .
        gen double sargan_p   = .
        gen double ar1_z      = .
        gen double ar1_p      = .
        gen double ar2_z      = .
        gen double ar2_p      = .

        capture replace N = e(N)
        capture replace N_g = e(N_g)
        capture replace k = e(k)
        capture replace k_eq = e(k_eq)
        capture replace k_inst = e(k_inst)

        capture replace j = e(j)
        capture replace j_p = e(j_p)
        capture replace hansen = e(hansen)
        capture replace hansen_p = e(hansen_p)
        capture replace sargan = e(sargan)
        capture replace sargan_p = e(sargan_p)

        capture replace ar1_z = e(ar1)
        capture replace ar1_p = e(ar1p)
        capture replace ar2_z = e(ar2)
        capture replace ar2_p = e(ar2p)

        export delimited using "`outfile'", replace
    restore
end

capture program drop dump_xtdpdgmm_ereturn
program define dump_xtdpdgmm_ereturn
    syntax, Spec(string) Outfile(string)

    tempfile tmp
    tempname handle

    postfile `handle' str80 spec str20 kind str80 name double value_num str244 value_text using `tmp', replace

    local scalars : e(scalars)
    foreach s of local scalars {
        capture scalar __v = e(`s')
        if !_rc {
            post `handle' ("`spec'") ("scalar") ("`s'") (__v) ("")
        }
    }

    local macros : e(macros)
    foreach m of local macros {
        local __txt `"`e(`m')'"'
        post `handle' ("`spec'") ("macro") ("`m'") (.) (`"`__txt'"')
    }

    postclose `handle'

    preserve
        use `tmp', clear
        export delimited using "`outfile'", replace
    restore
end

capture program drop dump_xtdpdgmm_diag
program define dump_xtdpdgmm_diag
    syntax, Spec(string) Outfile(string)

    preserve
        clear
        set obs 1

        gen str80 spec = "`spec'"

        gen double N             = .
        gen double N_g           = .
        gen double N_clust       = .
        gen double g_min         = .
        gen double g_avg         = .
        gen double g_max         = .
        gen double rank          = .
        gen double zrank         = .
        gen double zrank_nl      = .
        gen double steps         = .
        gen double twostep       = .
        gen double chi2_J        = .
        gen double chi2_J_u      = .
        gen double overid_df     = .
        gen double chi2_J_p      = .
        gen double chi2_J_u_p    = .

        capture replace N = e(N)
        capture replace N_g = e(N_g)
        capture replace N_clust = e(N_clust)
        capture replace g_min = e(g_min)
        capture replace g_avg = e(g_avg)
        capture replace g_max = e(g_max)
        capture replace rank = e(rank)
        capture replace zrank = e(zrank)
        capture replace zrank_nl = e(zrank_nl)
        capture replace steps = e(steps)
        capture replace twostep = e(twostep)
        capture replace chi2_J = e(chi2_J)
        capture replace chi2_J_u = e(chi2_J_u)

        capture replace overid_df = e(zrank) - e(rank)
        capture replace chi2_J_p = chi2tail(overid_df, chi2_J) if overid_df < . & chi2_J < .
        capture replace chi2_J_u_p = chi2tail(overid_df, chi2_J_u) if overid_df < . & chi2_J_u < .

        export delimited using "`outfile'", replace
    restore
end

capture program drop dump_return_scalars
program define dump_return_scalars
    syntax, Spec(string) Command(string) Outfile(string)

    tempfile tmp
    tempname handle

    postfile `handle' str80 spec str40 command str20 kind str80 name double value_num str244 value_text using `tmp', replace

    local scalars : r(scalars)
    foreach s of local scalars {
        capture scalar __v = r(`s')
        if !_rc {
            post `handle' ("`spec'") ("`command'") ("scalar") ("`s'") (__v) ("")
        }
    }

    local macros : r(macros)
    foreach m of local macros {
        local __txt `"`r(`m')'"'
        post `handle' ("`spec'") ("`command'") ("macro") ("`m'") (.) (`"`__txt'"')
    }

    postclose `handle'

    preserve
        use `tmp', clear
        export delimited using "`outfile'", replace
    restore
end

capture program drop dump_failed_postestimation
program define dump_failed_postestimation
    syntax, Spec(string) Command(string) Outfile(string) RC(integer)

    preserve
        clear
        set obs 1

        gen str80 spec = "`spec'"
        gen str40 command = "`command'"
        gen str20 kind = "failed"
        gen str80 name = "_rc"
        gen double value_num = `rc'
        gen str244 value_text = ""

        export delimited using "`outfile'", replace
    restore
end

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
ereturn list
dump_xtdpdgmm_diag, spec("fod_diff_endog_x_onestep") outfile("C:/Users/omoko/OneDrive/Python packages/systemgmmkit/artifacts/parity/xtdpdgmm/fod_diff/stata_fod_diff_endog_x_onestep_diagnostics.csv")
dump_xtdpdgmm_ereturn, spec("fod_diff_endog_x_onestep") outfile("C:/Users/omoko/OneDrive/Python packages/systemgmmkit/artifacts/parity/xtdpdgmm/fod_diff/stata_fod_diff_endog_x_onestep_ereturn.csv")
capture noisily estat overid
local __rc_overid = _rc
if `__rc_overid' == 0 {
    return list
    dump_return_scalars, spec("fod_diff_endog_x_onestep") command("estat_overid") outfile("C:/Users/omoko/OneDrive/Python packages/systemgmmkit/artifacts/parity/xtdpdgmm/fod_diff/stata_fod_diff_endog_x_onestep_estat_overid_return.csv")
}
else {
    dump_failed_postestimation, spec("fod_diff_endog_x_onestep") command("estat_overid") outfile("C:/Users/omoko/OneDrive/Python packages/systemgmmkit/artifacts/parity/xtdpdgmm/fod_diff/stata_fod_diff_endog_x_onestep_estat_overid_return.csv") rc(`__rc_overid')
}

capture noisily estat serial, ar(1/2)
local __rc_serial = _rc
if `__rc_serial' == 0 {
    return list
    dump_return_scalars, spec("fod_diff_endog_x_onestep") command("estat_serial_ar12") outfile("C:/Users/omoko/OneDrive/Python packages/systemgmmkit/artifacts/parity/xtdpdgmm/fod_diff/stata_fod_diff_endog_x_onestep_estat_serial_return.csv")
}
else {
    dump_failed_postestimation, spec("fod_diff_endog_x_onestep") command("estat_serial_ar12") outfile("C:/Users/omoko/OneDrive/Python packages/systemgmmkit/artifacts/parity/xtdpdgmm/fod_diff/stata_fod_diff_endog_x_onestep_estat_serial_return.csv") rc(`__rc_serial')
}

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
ereturn list
dump_xtdpdgmm_diag, spec("fod_diff_endog_x_twostep") outfile("C:/Users/omoko/OneDrive/Python packages/systemgmmkit/artifacts/parity/xtdpdgmm/fod_diff/stata_fod_diff_endog_x_twostep_diagnostics.csv")
dump_xtdpdgmm_ereturn, spec("fod_diff_endog_x_twostep") outfile("C:/Users/omoko/OneDrive/Python packages/systemgmmkit/artifacts/parity/xtdpdgmm/fod_diff/stata_fod_diff_endog_x_twostep_ereturn.csv")
capture noisily estat overid
local __rc_overid = _rc
if `__rc_overid' == 0 {
    return list
    dump_return_scalars, spec("fod_diff_endog_x_twostep") command("estat_overid") outfile("C:/Users/omoko/OneDrive/Python packages/systemgmmkit/artifacts/parity/xtdpdgmm/fod_diff/stata_fod_diff_endog_x_twostep_estat_overid_return.csv")
}
else {
    dump_failed_postestimation, spec("fod_diff_endog_x_twostep") command("estat_overid") outfile("C:/Users/omoko/OneDrive/Python packages/systemgmmkit/artifacts/parity/xtdpdgmm/fod_diff/stata_fod_diff_endog_x_twostep_estat_overid_return.csv") rc(`__rc_overid')
}

capture noisily estat serial, ar(1/2)
local __rc_serial = _rc
if `__rc_serial' == 0 {
    return list
    dump_return_scalars, spec("fod_diff_endog_x_twostep") command("estat_serial_ar12") outfile("C:/Users/omoko/OneDrive/Python packages/systemgmmkit/artifacts/parity/xtdpdgmm/fod_diff/stata_fod_diff_endog_x_twostep_estat_serial_return.csv")
}
else {
    dump_failed_postestimation, spec("fod_diff_endog_x_twostep") command("estat_serial_ar12") outfile("C:/Users/omoko/OneDrive/Python packages/systemgmmkit/artifacts/parity/xtdpdgmm/fod_diff/stata_fod_diff_endog_x_twostep_estat_serial_return.csv") rc(`__rc_serial')
}

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
ereturn list
dump_xtdpdgmm_diag, spec("fod_diff_predet_x_onestep") outfile("C:/Users/omoko/OneDrive/Python packages/systemgmmkit/artifacts/parity/xtdpdgmm/fod_diff/stata_fod_diff_predet_x_onestep_diagnostics.csv")
dump_xtdpdgmm_ereturn, spec("fod_diff_predet_x_onestep") outfile("C:/Users/omoko/OneDrive/Python packages/systemgmmkit/artifacts/parity/xtdpdgmm/fod_diff/stata_fod_diff_predet_x_onestep_ereturn.csv")
capture noisily estat overid
local __rc_overid = _rc
if `__rc_overid' == 0 {
    return list
    dump_return_scalars, spec("fod_diff_predet_x_onestep") command("estat_overid") outfile("C:/Users/omoko/OneDrive/Python packages/systemgmmkit/artifacts/parity/xtdpdgmm/fod_diff/stata_fod_diff_predet_x_onestep_estat_overid_return.csv")
}
else {
    dump_failed_postestimation, spec("fod_diff_predet_x_onestep") command("estat_overid") outfile("C:/Users/omoko/OneDrive/Python packages/systemgmmkit/artifacts/parity/xtdpdgmm/fod_diff/stata_fod_diff_predet_x_onestep_estat_overid_return.csv") rc(`__rc_overid')
}

capture noisily estat serial, ar(1/2)
local __rc_serial = _rc
if `__rc_serial' == 0 {
    return list
    dump_return_scalars, spec("fod_diff_predet_x_onestep") command("estat_serial_ar12") outfile("C:/Users/omoko/OneDrive/Python packages/systemgmmkit/artifacts/parity/xtdpdgmm/fod_diff/stata_fod_diff_predet_x_onestep_estat_serial_return.csv")
}
else {
    dump_failed_postestimation, spec("fod_diff_predet_x_onestep") command("estat_serial_ar12") outfile("C:/Users/omoko/OneDrive/Python packages/systemgmmkit/artifacts/parity/xtdpdgmm/fod_diff/stata_fod_diff_predet_x_onestep_estat_serial_return.csv") rc(`__rc_serial')
}

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
ereturn list
dump_xtdpdgmm_diag, spec("fod_diff_predet_x_twostep") outfile("C:/Users/omoko/OneDrive/Python packages/systemgmmkit/artifacts/parity/xtdpdgmm/fod_diff/stata_fod_diff_predet_x_twostep_diagnostics.csv")
dump_xtdpdgmm_ereturn, spec("fod_diff_predet_x_twostep") outfile("C:/Users/omoko/OneDrive/Python packages/systemgmmkit/artifacts/parity/xtdpdgmm/fod_diff/stata_fod_diff_predet_x_twostep_ereturn.csv")
capture noisily estat overid
local __rc_overid = _rc
if `__rc_overid' == 0 {
    return list
    dump_return_scalars, spec("fod_diff_predet_x_twostep") command("estat_overid") outfile("C:/Users/omoko/OneDrive/Python packages/systemgmmkit/artifacts/parity/xtdpdgmm/fod_diff/stata_fod_diff_predet_x_twostep_estat_overid_return.csv")
}
else {
    dump_failed_postestimation, spec("fod_diff_predet_x_twostep") command("estat_overid") outfile("C:/Users/omoko/OneDrive/Python packages/systemgmmkit/artifacts/parity/xtdpdgmm/fod_diff/stata_fod_diff_predet_x_twostep_estat_overid_return.csv") rc(`__rc_overid')
}

capture noisily estat serial, ar(1/2)
local __rc_serial = _rc
if `__rc_serial' == 0 {
    return list
    dump_return_scalars, spec("fod_diff_predet_x_twostep") command("estat_serial_ar12") outfile("C:/Users/omoko/OneDrive/Python packages/systemgmmkit/artifacts/parity/xtdpdgmm/fod_diff/stata_fod_diff_predet_x_twostep_estat_serial_return.csv")
}
else {
    dump_failed_postestimation, spec("fod_diff_predet_x_twostep") command("estat_serial_ar12") outfile("C:/Users/omoko/OneDrive/Python packages/systemgmmkit/artifacts/parity/xtdpdgmm/fod_diff/stata_fod_diff_predet_x_twostep_estat_serial_return.csv") rc(`__rc_serial')
}

export_last_xtdpdgmm, spec("fod_diff_predet_x_twostep") output("C:/Users/omoko/OneDrive/Python packages/systemgmmkit/artifacts/parity/xtdpdgmm/fod_diff/stata_fod_diff_predet_x_twostep.csv")

display as text "============================================================"
display as text "FOD xtdpdgmm oracle export complete"
display as text "============================================================"

log close
exit, clear
