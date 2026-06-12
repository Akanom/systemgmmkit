from pathlib import Path
import re

path = Path("src/systemgmmkit/native_gmm.py")
text = path.read_text(encoding="utf-8")

backup = Path("artifacts/parity/xtabond2/native_gmm_before_FORCE_level_dep_lag_patch.py")
backup.parent.mkdir(parents=True, exist_ok=True)
backup.write_text(text, encoding="utf-8")

pattern = re.compile(
    r'(?ms)^                    if _level_diff_mode == "lag1":\r?\n'
    r'.*?'
    r'(?=^                    elif _level_diff_mode == "current":)'
)

matches = list(pattern.finditer(text))

if len(matches) != 1:
    print(f"FAILED: expected exactly 1 lag1 branch, found {len(matches)}")
    print(r'Run: rg -n -C 45 -e "_level_diff_mode" .\src\systemgmmkit\native_gmm.py')
    raise SystemExit(1)

new_branch = '''                    if _level_diff_mode == "lag1":
                        import os as _native_level_dep_offset_os

                        _level_dep_offset_enabled = (
                            _native_level_dep_offset_os.getenv(
                                "SYSTEMGMMKIT_LEVEL_GMM_LAGGED_DEP_OFFSET",
                                "0",
                            )
                            .strip()
                            .lower()
                            in {"1", "true", "yes", "on"}
                        )

                        _dep_name = getattr(spec, "dependent", None)
                        _regressors = set(
                            str(v) for v in (getattr(spec, "regressors", None) or [])
                        )

                        _is_lagged_dep_block = (
                            _dep_name is not None
                            and str(block.variable) == str(_dep_name)
                            and (
                                f"L1.{_dep_name}" in _regressors
                                or f"L.{_dep_name}" in _regressors
                            )
                        )

                        if _level_dep_offset_enabled and _is_lagged_dep_block:
                            # xtabond2-compatible level-equation instrument for
                            # gmm(L.y, lag(2 3)):
                            #   y[t-2] - y[t-3]
                            left = _safe_get(s, pos - 2)
                            right = _safe_get(s, pos - 3)
                        else:
                            # Existing/native behavior for non-lagged-dependent blocks,
                            # including x, which already matches xtabond2.
                            left = _safe_get(s, pos - 1)
                            right = _safe_get(s, pos - 2)

                        if left is not None and right is not None:
                            z_dict[f"L:diff:{block.variable}:L1"] = left - right

'''

text2 = pattern.sub(new_branch, text, count=1)
path.write_text(text2, encoding="utf-8")

print("FORCE patched level lag1 branch.")
print(f"Backup written to: {backup}")
