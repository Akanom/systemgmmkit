from pathlib import Path
import re

path = Path("src/systemgmmkit/native_gmm.py")
text = path.read_text(encoding="utf-8")

backup = Path("artifacts/parity/xtabond2/native_gmm_before_level_dep_offset_patch.py")
backup.parent.mkdir(parents=True, exist_ok=True)
backup.write_text(text, encoding="utf-8")

if "SYSTEMGMMKIT_LEVEL_GMM_LAGGED_DEP_OFFSET" in text:
    print("Level-GMM lagged dependent offset patch already exists. No patch needed.")
    raise SystemExit(0)

pattern = re.compile(
    r'(?ms)^                    if _level_diff_mode == "lag1":\r?\n'
    r'.*?'
    r'(?=^                    elif _level_diff_mode == "current":)'
)

matches = list(pattern.finditer(text))

if len(matches) != 1:
    print(f"Expected exactly 1 lag1 block match, found {len(matches)}.")
    print("No changes made.")
    print("Run this to inspect context:")
    print(r'rg -n -C 35 -e "_level_diff_mode" .\src\systemgmmkit\native_gmm.py')
    raise SystemExit(1)

new_block = '''                    if _level_diff_mode == "lag1":
                        # Diagnostic parity switch for lagged dependent variable:
                        #
                        # xtabond2 System GMM level-equation instruments for
                        # gmm(L.y, lag(2 3)) imply:
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

'''

text2 = pattern.sub(new_block, text, count=1)
path.write_text(text2, encoding="utf-8")

print("Patched level-GMM lagged dependent variable offset switch successfully.")
print(f"Backup written to: {backup}")
