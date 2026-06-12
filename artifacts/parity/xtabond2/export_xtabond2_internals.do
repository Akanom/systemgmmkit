cd "C:\Users\omoko\OneDrive\Python packages\systemgmmkit"

import delimited using "artifacts/parity/xtabond2/system_gmm_benchmark.csv", clear
xtset id t

xtabond2 y L.y x w, ///
    gmm(L.y x, lag(2 3) collapse) ///
    iv(w, eq(level)) ///
    twostep robust small

matrix b = e(b)
matrix V = e(V)
matrix A1 = e(A1)
matrix A2 = e(A2)
matrix Ze = e(Ze)

clear
set obs 1

gen spec = "system_gmm_baseline_controls"
gen stata_nobs = e(N)
gen stata_n_groups = e(N_g)
gen stata_n_instruments = e(j)
gen stata_hansen = e(hansen)
gen stata_hansen_df = e(hansen_df)
gen stata_hansen_p = e(hansenp)
gen stata_sargan = e(sargan)
gen stata_sargan_df = e(sar_df)
gen stata_sargan_p = e(sarganp)
gen stata_ar1 = e(ar1)
gen stata_ar1_p = e(ar1p)
gen stata_ar2 = e(ar2)
gen stata_ar2_p = e(ar2p)

export delimited using "artifacts/parity/xtabond2/xtabond2_internal_diagnostics.csv", replace

matrix list A1
matrix list A2
matrix list Ze
matrix list b
matrix list V
