from pathlib import Path

path = Path("src/systemgmmkit/native_gmm.py")
text = path.read_text(encoding="utf-8")

start_token = '        if label.startswith("IV:"):'
start = text.find(start_token)

if start == -1:
    raise SystemExit("Could not find IV block start.")

# The IV block ends at the first same-indentation 'if not cols:' after the IV block.
end_token = '    if not cols:'
end = text.find(end_token, start)

if end == -1:
    raise SystemExit("Could not find block end marker: '    if not cols:'.")

new_block = '''        if label.startswith("IV:"):
            var = label.split(":", 1)[1]

            if var not in x_cols:
                raise KeyError(
                    f"Cannot build pydynpd IV column {label!r}; {var!r} not in X names."
                )

            _iv_col = np.asarray(X[:, x_cols[var]], dtype=float)

            if spec.system:
                # In System GMM, `_con` is level-equation only:
                #   diff rows  -> _con = 0
                #   level rows -> _con = 1
                #
                # Use this marker to respect xtabond2-style IV equation scope:
                #   iv(w, eq(level)) -> w appears only on level-equation rows.
                if "_con" in x_cols:
                    _con_col = np.asarray(X[:, x_cols["_con"]], dtype=float)
                    _level_rows = np.isclose(_con_col, 1.0)
                    _diff_rows = ~_level_rows
                else:
                    _level_rows = np.zeros_like(_iv_col, dtype=bool)
                    _diff_rows = np.ones_like(_iv_col, dtype=bool)

                matching_iv_blocks = [
                    block
                    for block in spec.iv
                    if _native_style_variable(block) == var
                ]

                iv_equation = None
                if matching_iv_blocks:
                    iv_equation = getattr(matching_iv_blocks[0], "equation", None)

                if iv_equation is None:
                    col = _iv_col

                else:
                    eq = str(iv_equation).strip().lower()

                    if eq in {"level", "levels", "l"}:
                        col = np.where(_level_rows, _iv_col, 0.0)

                    elif eq in {"diff", "difference", "d"}:
                        col = np.where(_diff_rows, _iv_col, 0.0)

                    elif eq in {"both", "all", "system"}:
                        col = _iv_col

                    else:
                        raise ValueError(
                            f"Unsupported IV equation scope {iv_equation!r} for {label!r}. "
                            "Use level, diff, both/all, or None."
                        )

            else:
                col = _iv_col

            cols.append(col)
            continue

'''

text2 = text[:start] + new_block + text[end:]
path.write_text(text2, encoding="utf-8")

print("Patched IV block successfully.")
