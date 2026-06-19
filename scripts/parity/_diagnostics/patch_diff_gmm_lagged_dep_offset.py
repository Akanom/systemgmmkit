from pathlib import Path

path = Path("src/systemgmmkit/native_gmm.py")
text = path.read_text(encoding="utf-8")

if "SYSTEMGMMKIT_DIFF_GMM_LAGGED_DEP_OFFSET" in text:
    print("Lagged-dependent-variable offset patch already exists. No patch needed.")
    raise SystemExit(0)

old = """            for block in spec.gmm:
                s = group[block.variable].astype(float)

                for lag in range(block.min_lag, block.max_lag + 1):
                    val = _safe_get(s, pos - lag)

                    if val is not None:
                        z_dict[f"D:{block.variable}:L{lag}"] = val
"""

new = """            for block in spec.gmm:
                s = group[block.variable].astype(float)

                # Diagnostic parity switch:
                #
                # xtabond2 interprets gmm(L.y, lag(2 3)) as instruments for the
                # lagged dependent regressor L.y, not raw y. Therefore:
                #   L2.(L.y) = y[t-3]
                #   L3.(L.y) = y[t-4]
                #
                # Native previously used y[t-2] and y[t-3].
                # Enable this shift with:
                #   SYSTEMGMMKIT_DIFF_GMM_LAGGED_DEP_OFFSET=1
                import os as _native_diff_gmm_lag_os

                _lag_offset_mode = (
                    _native_diff_gmm_lag_os.getenv(
                        "SYSTEMGMMKIT_DIFF_GMM_LAGGED_DEP_OFFSET",
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

                _lag_offset = (
                    1
                    if _is_lagged_dep_block
                    and _lag_offset_mode in {"1", "true", "yes", "on"}
                    else 0
                )

                for lag in range(block.min_lag, block.max_lag + 1):
                    val = _safe_get(s, pos - lag - _lag_offset)

                    if val is not None:
                        z_dict[f"D:{block.variable}:L{lag}"] = val
"""

if old not in text:
    print("Could not find exact difference-GMM instrument block.")
    print("Showing nearby context:")
    raise SystemExit(1)

text = text.replace(old, new, 1)
path.write_text(text, encoding="utf-8")

print("Patched difference-GMM lagged dependent variable offset switch.")
