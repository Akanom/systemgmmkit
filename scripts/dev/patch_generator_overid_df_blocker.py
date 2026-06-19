from pathlib import Path

path = Path("scripts/dev/generate_manual_stata_gmm_lag_window_parity.py")
text = path.read_text(encoding="utf-8")

old = """            'display "j_df=" e(j_df)',"""

new = r"""            'display "j_df_raw=" e(j_df)',
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
            'display "k_params_colsof_eb=" colsof(e(b))',"""

if old not in text:
    raise RuntimeError("Could not find j_df display line in generator script.")

text = text.replace(old, new)

path.write_text(text, encoding="utf-8")
print("Patched generator script with overidentification-df blocker.")
