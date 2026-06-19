from pathlib import Path

path = Path("src/systemgmmkit/native_gmm.py")
text = path.read_text(encoding="utf-8")

if "SYSTEMGMMKIT_LEVEL_GMM_LAGGED_DEP_OFFSET" in text:
    print("Level-GMM lagged dependent offset patch already exists. No patch needed.")
    raise SystemExit(0)

old = """                    if _level_diff_mode == "lag1":
                        left = _safe_get(s, pos - 1)
                        right = _safe_get(s, pos - 2)

                        if left is not None and right is not None:
                            z_dict[f"L:diff:{block.variable}:L1"] = left - right
"""

new = """                    if _level_diff_mode == "lag1":
                        # Diagnostic parity switch for lagged dependent variable:
                        #
                        # xtabond2 System GMM level-equation instruments for
                        # gmm(L.y, lag(2 3)) imply the level instrument:
                        #   y[t-2] - y[t-3]
                        #
                        # Native previously used:
                        #   y[t-1] - y[t-2]
                        #
                        # Enable this only for the dependent-variable GMM block with:
                        #   SYSTEMGMMKIT_LEVEL_GMM_LAGGED_DEP_OFFSET=1
                        import os as _native_level_gmm_lag_os

                        _level_dep_offset_mode = (
                            _native_level_gmm_lag_os.getenv(
                                "SYSTEMGMMKIT_LEVEL_GMM_LAGGED_DEP_OFFSET",
                                "0",
                            )
                            .strip()
                            .lower()
                        )

                        _dep_name = getattr(spec, "dependent", None)
                        _regressors = set(str(v) for v in (getattr(spec, "regressors", None) or []))

                        _is_lagged_dep_block = (
                            _dep_name is not None
                            and str(block.variable) == str(_dep_name)
                            and (
                                f"L1.{_dep_name}" in _regressors
                                or f"L.{_dep_name}" in _regressors
                            )
                        )

                        if (
                            _is_lagged_dep_block
                            and _level_dep_offset_mode in {"1", "true", "yes", "on"}
                        ):
                            left = _safe_get(s, pos - 2)
                            right = _safe_get(s, pos - 3)
                        else:
                            left = _safe_get(s, pos - 1)
                            right = _safe_get(s, pos - 2)

                        if left is not None and right is not None:
                            z_dict[f"L:diff:{block.variable}:L1"] = left - right
"""

if old not in text:
    print("Could not find exact level-GMM lag1 block.")
    print("Search context with:")
    print('rg -n -C 25 -e "_level_diff_mode == \\"lag1\\"" src/systemgmmkit/native_gmm.py')
    raise SystemExit(1)

text = text.replace(old, new, 1)
path.write_text(text, encoding="utf-8")

print("Patched level-GMM lagged dependent variable offset switch.")
