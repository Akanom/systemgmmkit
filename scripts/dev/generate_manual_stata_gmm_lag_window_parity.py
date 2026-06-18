from __future__ import annotations

from pathlib import Path

from systemgmmkit import build_system_gmm_spec
from systemgmmkit.parity import stata_xtabond2_command


OUT = Path("artifacts/parity/gmm_lag_windows")
OUT.mkdir(parents=True, exist_ok=True)

specs = {
    "m_base": build_system_gmm_spec(
        dependent="y",
        regressors=["x"],
        endogenous=["x"],
    ),

    "m_role": build_system_gmm_spec(
        dependent="y",
        regressors=["x", "cashflow"],
        endogenous=["x"],
        predetermined=["cashflow"],
        gmm_lags=(2, 4),
        gmm_lags_by_role={
            "endogenous": (2, 5),
            "predetermined": (1, 3),
        },
    ),

    "m_var": build_system_gmm_spec(
        dependent="y",
        regressors=["x", "cashflow"],
        endogenous=["x"],
        predetermined=["cashflow"],
        gmm_lags=(2, 4),
        gmm_lags_by_role={
            "endogenous": (2, 5),
            "predetermined": (1, 3),
        },
        gmm_lags_by_variable={
            "y": (2, 4),
            "x": (3, 5),
            "cashflow": (1, 2),
        },
    ),
}

lines = [
    "********************************************************************************",
    "* systemgmmkit manual Stata parity check",
    "* Run this file manually in Stata.",
    "*",
    "* IMPORTANT:",
    "* 1. Load the existing parity dataset before running these commands, OR",
    "* 2. Add the dataset import/use command below before xtset.",
    "*",
    "* Required variables for this generated check:",
    "*   id, t, y, x, cashflow",
    "********************************************************************************",
    "",
    "capture log close",
    'log using "artifacts/parity/gmm_lag_windows/gmm_lag_windows_xtabond2_manual.log", replace text',
    "",
    "* Example if using a Stata dataset:",
    '* use "path/to/your/parity_dataset.dta", clear',
    "",
    "* Example if using CSV:",
    '* import delimited "path/to/your/parity_dataset.csv", clear',
    "",
]

for name, spec in specs.items():
    cmd = stata_xtabond2_command(spec, entity="id", time="t")

    lines.extend(
        [
            "",
            "********************************************************************************",
            f"* {name}",
            "********************************************************************************",
            cmd,
            f"estimates store {name}",
            "",
            f'matrix b_{name} = e(b)',
            f'matrix V_{name} = e(V)',
            "",
            f'display "MODEL={name}"',
            'display "N=" e(N)',
            'display "N_g=" e(N_g)',
            'display "j=" e(j)',
            'display "j_df_raw=" e(j_df)',
            '',
            'scalar __sgmmkit_overid_df = .',
            'scalar __sgmmkit_overid_df_source = 0',
            '',
            'capture scalar __sgmmkit_overid_df = e(j_df)',
            'if !missing(__sgmmkit_overid_df) {',
            '    scalar __sgmmkit_overid_df_source = 1',
            '}',
            '',
            'if missing(__sgmmkit_overid_df) {',
            '    capture scalar __sgmmkit_overid_df = e(hansen_df)',
            '    if !_rc & !missing(__sgmmkit_overid_df) {',
            '        scalar __sgmmkit_overid_df_source = 2',
            '    }',
            '}',
            '',
            'if missing(__sgmmkit_overid_df) {',
            '    capture scalar __sgmmkit_overid_df = e(df_hansen)',
            '    if !_rc & !missing(__sgmmkit_overid_df) {',
            '        scalar __sgmmkit_overid_df_source = 3',
            '    }',
            '}',
            '',
            'if missing(__sgmmkit_overid_df) {',
            '    capture scalar __sgmmkit_overid_df = e(j) - colsof(e(b))',
            '    if !_rc & !missing(__sgmmkit_overid_df) {',
            '        scalar __sgmmkit_overid_df_source = 4',
            '    }',
            '}',
            '',
            'if missing(__sgmmkit_overid_df) | __sgmmkit_overid_df < 0 {',
            '    display as error "BLOCKED: could not recover Hansen/Sargan overidentification degrees of freedom."',
            '    display as error "Run ereturn list after xtabond2 and inspect stored diagnostics."',
            '    ereturn list',
            '    exit 459',
            '}',
            '',
            'display "j_df_effective=" __sgmmkit_overid_df',
            'display "j_df_source=" __sgmmkit_overid_df_source',
            'display "k_instruments_ej=" e(j)',
            'display "k_params_colsof_eb=" colsof(e(b))',
            'display "hansenp=" e(hansenp)',
            'display "sarganp=" e(sarganp)',
            'display "ar1p=" e(ar1p)',
            'display "ar2p=" e(ar2p)',
        ]
    )

lines.extend(
    [
        "",
        "log close",
        "",
        "********************************************************************************",
        "* End of manual parity file",
        "********************************************************************************",
    ]
)

do_path = OUT / "gmm_lag_windows_xtabond2_manual.do"
do_path.write_text("\n".join(lines), encoding="utf-8")

cmd_path = OUT / "gmm_lag_windows_expected_commands.txt"
cmd_path.write_text(
    "\n\n".join(
        [
            f"{name}\n{'=' * len(name)}\n{stata_xtabond2_command(spec, entity='id', time='t')}"
            for name, spec in specs.items()
        ]
    ),
    encoding="utf-8",
)

print(f"Wrote: {do_path}")
print(f"Wrote: {cmd_path}")


