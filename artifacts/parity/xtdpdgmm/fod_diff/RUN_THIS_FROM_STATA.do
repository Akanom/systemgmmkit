clear all
set more off
set varabbrev off

args project_root
if `"`project_root'"' != "" {
    cd `"`project_root'"'
}

do "artifacts/parity/xtdpdgmm/fod_diff/fod_diff_xtdpdgmm_reference.do"
