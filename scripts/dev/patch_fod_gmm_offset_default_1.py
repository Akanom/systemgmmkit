from pathlib import Path

path = Path("src/systemgmmkit/native_gmm.py")
text = path.read_text(encoding="utf-8")

old = """                        _native_fod_instr_os.getenv(
                            "SYSTEMGMMKIT_FOD_GMM_INSTRUMENT_POS_OFFSET",
                            "0",
                        )
"""

new = """                        _native_fod_instr_os.getenv(
                            "SYSTEMGMMKIT_FOD_GMM_INSTRUMENT_POS_OFFSET",
                            "1",
                        )
"""

if old not in text:
    raise RuntimeError("Could not find FOD GMM instrument offset default block.")

text = text.replace(old, new, 1)

old_comment = """                    if _offset_raw in {"default", ""}:
                        _offset = 0
"""

new_comment = """                    if _offset_raw in {"default", ""}:
                        _offset = 1
"""

if old_comment not in text:
    raise RuntimeError("Could not find FOD GMM instrument offset default assignment.")

text = text.replace(old_comment, new_comment, 1)

path.write_text(text, encoding="utf-8")
print("Set default FOD transformed-equation GMM instrument offset to +1.")
