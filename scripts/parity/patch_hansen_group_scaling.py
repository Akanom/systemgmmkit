from pathlib import Path

path = Path("src/systemgmmkit/native_gmm.py")
text = path.read_text(encoding="utf-8")

backup = Path("artifacts/parity/xtabond2/native_gmm_before_hansen_group_scaling.py")
backup.parent.mkdir(parents=True, exist_ok=True)
backup.write_text(text, encoding="utf-8")

if "SYSTEMGMMKIT_HANSEN_GROUP_SCALE" in text:
    print("Hansen group-scaling patch already appears to exist. No patch applied.")
    raise SystemExit(0)

old = """    _j_stat = float((_ztu.T @ W @ _ztu).squeeze())
"""

new = """    _j_stat_raw = float((_ztu.T @ W @ _ztu).squeeze())

    # xtabond2-compatible Hansen scaling:
    #
    # xtabond2's e(A2) equals the native two-step weighting matrix divided by
    # the number of panel groups. Therefore Hansen J must use W / n_groups.
    # This leaves the coefficient estimates unchanged because scalar rescaling
    # of W does not change the GMM argmin.
    import os as _native_hansen_scale_os

    _hansen_group_scale_mode = (
        _native_hansen_scale_os.getenv(
            "SYSTEMGMMKIT_HANSEN_GROUP_SCALE",
            "1",
        )
        .strip()
        .lower()
    )

    _n_groups_for_hansen = max(int(getattr(result, "n_groups", 0) or 0), 1)

    if _hansen_group_scale_mode in {"1", "true", "yes", "on"}:
        _j_stat = _j_stat_raw / _n_groups_for_hansen
    else:
        _j_stat = _j_stat_raw
"""

if old not in text:
    print("Could not find exact _j_stat assignment.")
    print("Run this and inspect the active code:")
    print(r'rg -n -C 30 -e "_j_stat" .\src\systemgmmkit\native_gmm.py')
    raise SystemExit(1)

text = text.replace(old, new, 1)
path.write_text(text, encoding="utf-8")

print("Patched Hansen J group scaling.")
print(f"Backup written to: {backup}")