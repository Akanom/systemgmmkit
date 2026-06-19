from pathlib import Path

path = Path("src/systemgmmkit/native_gmm.py")
text = path.read_text(encoding="utf-8")

old = """        transformation_normalized = str(spec.transformation).strip().lower()
        transformed_start_pos = 0 if transformation_normalized == "fod" else 2

        for pos in range(transformed_start_pos, len(group)):
"""

new = """        transformation_normalized = str(spec.transformation).strip().lower()

        if transformation_normalized == "fod":
            import os as _native_fod_start_os

            _fod_start_raw = (
                _native_fod_start_os.getenv("SYSTEMGMMKIT_FOD_START_POS", "0")
                .strip()
                .lower()
            )

            if _fod_start_raw in {"default", ""}:
                transformed_start_pos = 0
            else:
                try:
                    transformed_start_pos = int(_fod_start_raw)
                except ValueError as exc:
                    raise ValueError(
                        "SYSTEMGMMKIT_FOD_START_POS must be an integer, 'default', or empty."
                    ) from exc
        else:
            transformed_start_pos = 2

        for pos in range(transformed_start_pos, len(group)):
"""

if old not in text:
    raise RuntimeError("Could not find transformed_start_pos block.")

text = text.replace(old, new, 1)
path.write_text(text, encoding="utf-8")

print("Patched FOD transformed-row start-position diagnostic mode.")
