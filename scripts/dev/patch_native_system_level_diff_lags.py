from pathlib import Path

path = Path("src/systemgmmkit/native_gmm.py")
text = path.read_text(encoding="utf-8")

helper_marker = """def _native_style_max_lag(style: object) -> int:
    value = getattr(style, "max_lag", None)
    if value is None:
        raise AttributeError(f"Could not extract max_lag from {style!r}.")
    return int(value)


def _native_pydynpd_compat_instrument_order(spec: DynamicPanelSpec) -> list[str]:
"""

helper_replacement = '''def _native_style_max_lag(style: object) -> int:
    value = getattr(style, "max_lag", None)
    if value is None:
        raise AttributeError(f"Could not extract max_lag from {style!r}.")
    return int(value)


def _native_system_level_diff_lag(style: object) -> int:
    """Return xtabond2-style System-GMM level-equation diff-instrument lag.

    For a GMM-style block with difference-equation lag window (a, b),
    xtabond2 uses a single collapsed level-equation difference instrument
    whose lag is effectively a - 1:

        lag(2 .) -> D.var / Δvar_{t-1}
        lag(3 .) -> DL2.var / Δvar_{t-2}
        lag(1 .) -> D.var at the current level row / Δvar_t

    The max(..., 0) guard is needed for predetermined lag(1 .) blocks.
    """

    return max(_native_style_min_lag(style) - 1, 0)


def _native_pydynpd_compat_instrument_order(spec: DynamicPanelSpec) -> list[str]:
'''

if helper_marker not in text:
    raise RuntimeError("Could not find helper insertion marker.")

text = text.replace(helper_marker, helper_replacement, 1)

old_order = """    if spec.system:
        for block in spec.gmm:
            var = _style_label(_native_style_variable(block))
            labels.append(f"L:diff:{var}:L1")
"""

new_order = """    if spec.system:
        for block in spec.gmm:
            var = _style_label(_native_style_variable(block))
            level_lag = _native_system_level_diff_lag(block)
            labels.append(f"L:diff:{var}:L{level_lag}")
"""

if old_order not in text:
    raise RuntimeError("Could not find system-level instrument order block.")

text = text.replace(old_order, new_order, 1)

old_level = """                for block in spec.gmm:
                    s = _style_source_series(group, block.variable)
                    block_label = _style_label(block.variable)
                    val = _lagged_difference_instrument_at(s, pos, lag=1)

                    if val is not None:
                        z_dict[f"L:diff:{block_label}:L1"] = val
"""

new_level = """                for block in spec.gmm:
                    s = _style_source_series(group, block.variable)
                    block_label = _style_label(block.variable)
                    level_lag = _native_system_level_diff_lag(block)
                    val = _lagged_difference_instrument_at(s, pos, lag=level_lag)

                    if val is not None:
                        z_dict[f"L:diff:{block_label}:L{level_lag}"] = val
"""

if old_level not in text:
    raise RuntimeError("Could not find level-equation GMM instrument block.")

text = text.replace(old_level, new_level, 1)

path.write_text(text, encoding="utf-8")
print("Patched native System-GMM level-equation diff-instrument lag logic.")
