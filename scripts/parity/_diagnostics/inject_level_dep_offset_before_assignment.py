from pathlib import Path

path = Path("src/systemgmmkit/native_gmm.py")
text = path.read_text(encoding="utf-8")

backup = Path("artifacts/parity/xtabond2/native_gmm_before_inject_level_dep_offset.py")
backup.parent.mkdir(parents=True, exist_ok=True)
backup.write_text(text, encoding="utf-8")

if "SYSTEMGMMKIT_LEVEL_GMM_LAGGED_DEP_OFFSET" in text:
    print(
        "Level dependent offset marker already exists. Inspect active code before patching again."
    )
    raise SystemExit(0)

needle = """                        if left is not None and right is not None:
                            z_dict[f"L:diff:{block.variable}:L1"] = left - right
"""

replacement = """                        # xtabond2 parity diagnostic:
                        # For gmm(L.y, lag(2 3)), the System-GMM level-equation
                        # instrument for the lagged dependent variable must use:
                        #   y[t-2] - y[t-3]
                        # not:
                        #   y[t-1] - y[t-2]
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
                            left = _safe_get(s, pos - 2)
                            right = _safe_get(s, pos - 3)

                        if left is not None and right is not None:
                            z_dict[f"L:diff:{block.variable}:L1"] = left - right
"""

count = text.count(needle)

if count < 1:
    print("Could not find level L:diff assignment needle.")
    print(r'Run: rg -n -C 45 -e "z_dict\[f\"L:diff" .\src\systemgmmkit\native_gmm.py')
    raise SystemExit(1)

# Replace only the first occurrence inside the level-equation lag block.
text2 = text.replace(needle, replacement, 1)
path.write_text(text2, encoding="utf-8")

print("Injected level dependent offset logic before L:diff assignment.")
print(f"Backup written to: {backup}")
