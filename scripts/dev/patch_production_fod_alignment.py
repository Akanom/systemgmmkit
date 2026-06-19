import re
from pathlib import Path

path = Path("src/systemgmmkit/native_gmm.py")
text = path.read_text(encoding="utf-8")

changes = []

# 1. Production default: FOD transformed-equation GMM instruments use pos + 1.
text_new, n = re.subn(
    r'(_native_fod_instr_os\.getenv\(\s*"SYSTEMGMMKIT_FOD_GMM_INSTRUMENT_POS_OFFSET",\s*)"[^\"]+"',
    r'\1"1"',
    text,
    count=1,
    flags=re.DOTALL,
)
if n == 1:
    text = text_new
    changes.append("Set SYSTEMGMMKIT_FOD_GMM_INSTRUMENT_POS_OFFSET default to 1.")
else:
    print("WARNING: Could not find FOD GMM instrument offset getenv default.")

# 2. Production default: final System-GMM standard IV placement is level-only.
text_new, n = re.subn(
    r'(getenv\(\s*"SYSTEMGMMKIT_SYSTEM_IV_Z_MODE",\s*)"[^\"]+"',
    r'\1"level_only"',
    text,
    count=1,
    flags=re.DOTALL,
)
if n == 1:
    text = text_new
    changes.append("Set SYSTEMGMMKIT_SYSTEM_IV_Z_MODE default to level_only.")
else:
    print("WARNING: Could not find SYSTEMGMMKIT_SYSTEM_IV_Z_MODE getenv default.")

# 3. If a blank/default assignment still maps FOD GMM offset to 0, map it to 1.
needle = """                    if _offset_raw in {"default", ""}:
                        _offset = 0
"""
replacement = """                    if _offset_raw in {"default", ""}:
                        _offset = 1
"""
if needle in text:
    text = text.replace(needle, replacement, 1)
    changes.append("Set blank/default FOD GMM offset assignment to 1.")

path.write_text(text, encoding="utf-8")

print("Production FOD alignment patch complete.")
for change in changes:
    print(f"- {change}")
