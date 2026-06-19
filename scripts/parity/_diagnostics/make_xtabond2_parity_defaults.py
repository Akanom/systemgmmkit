from __future__ import annotations

import re
from pathlib import Path

PATH = Path("src/systemgmmkit/native_gmm.py")
text = PATH.read_text(encoding="utf-8")

backup = Path("artifacts/parity/xtabond2/native_gmm_before_xtabond2_default_patch_final.py")
backup.parent.mkdir(parents=True, exist_ok=True)
backup.write_text(text, encoding="utf-8")


DEFAULTS = {
    "SYSTEMGMMKIT_SYSTEM_IV_Z_MODE": "level_only",
    "SYSTEMGMMKIT_DIFF_GMM_LAGGED_DEP_OFFSET": "1",
    "SYSTEMGMMKIT_LEVEL_GMM_LAGGED_DEP_OFFSET": "1",
    "SYSTEMGMMKIT_HANSEN_GROUP_SCALE": "1",
}


def patch_env_default(source: str, env_name: str, default: str) -> tuple[str, str]:
    """
    Robustly patch environment default patterns near ENV marker.

    Handles:
      getenv("ENV", "old")
      environ.get("ENV", "old")
      getenv("ENV") or "old"
      environ.get("ENV") or "old"

    If already defaulted correctly, returns unchanged source with status.
    """
    idx = source.find(env_name)
    if idx == -1:
        return source, "marker_not_found"

    # Work only around the marker to avoid accidental global replacement.
    start = max(0, idx - 350)
    end = min(len(source), idx + 900)
    window = source[start:end]

    # Already correct default: getenv/environ.get("ENV", "default")
    already_defaulted = re.search(
        rf'["\']{re.escape(env_name)}["\']\s*,\s*["\']{re.escape(default)}["\']',
        window,
        flags=re.MULTILINE,
    )
    if already_defaulted:
        return source, "already_correct"

    # Already correct fallback: get("ENV") or "default"
    already_fallback = re.search(
        rf'["\']{re.escape(env_name)}["\']\s*\)\s*(?:\.\w+\(\)\s*)*or\s*["\']{re.escape(default)}["\']',
        window,
        flags=re.MULTILINE,
    )
    if already_fallback:
        return source, "already_correct"

    original = window

    # Case 1: getenv/environ.get("ENV", "old")
    window, n = re.subn(
        rf'(["\']{re.escape(env_name)}["\']\s*,\s*)["\'][^"\']*["\']',
        rf'\g<1>"{default}"',
        window,
        count=1,
        flags=re.MULTILINE,
    )

    if n == 0:
        # Case 2: getenv/environ.get("ENV") or "old"
        window, n = re.subn(
            rf'(["\']{re.escape(env_name)}["\']\s*\)\s*(?:\.\w+\(\)\s*)*or\s*)["\'][^"\']*["\']',
            rf'\g<1>"{default}"',
            window,
            count=1,
            flags=re.MULTILINE,
        )

    if n == 0:
        # Case 3: getenv/environ.get("ENV") with no default/fallback
        window, n = re.subn(
            rf'(["\']{re.escape(env_name)}["\']\s*)\)',
            rf'\g<1>, "{default}")',
            window,
            count=1,
            flags=re.MULTILINE,
        )

    if n == 0 or window == original:
        return source, "not_patched"

    source = source[:start] + window + source[end:]
    return source, "patched"


statuses = {}

for env_name, default in DEFAULTS.items():
    text, status = patch_env_default(text, env_name, default)
    statuses[env_name] = status
    print(f"{env_name}: {status}")

failed = {
    env: status for env, status in statuses.items() if status in {"not_patched", "marker_not_found"}
}

if failed:
    print()
    print("FAILED MARKERS:")
    for env, status in failed.items():
        print(f"  {env}: {status}")
        idx = text.find(env)
        if idx != -1:
            print(text[max(0, idx - 300) : idx + 700])
    raise SystemExit(1)

PATH.write_text(text, encoding="utf-8")

print()
print("Patched xtabond2-compatible System GMM defaults.")
print(f"Backup written to: {backup}")
