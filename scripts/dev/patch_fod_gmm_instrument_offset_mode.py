from pathlib import Path

path = Path("src/systemgmmkit/native_gmm.py")
text = path.read_text(encoding="utf-8")

old = """            for block in spec.gmm:
                s = _style_source_series(group, block.variable)
                block_label = _style_label(block.variable)

                for lag in range(block.min_lag, block.max_lag + 1):
                    val = _lagged_level_instrument_at(s, pos, lag)

                    if val is not None:
                        z_dict[f"D:{block_label}:L{lag}"] = val
"""

new = """            for block in spec.gmm:
                s = _style_source_series(group, block.variable)
                block_label = _style_label(block.variable)

                instrument_pos = pos
                if transformation_normalized == "fod":
                    import os as _native_fod_instr_os

                    _offset_raw = (
                        _native_fod_instr_os.getenv(
                            "SYSTEMGMMKIT_FOD_GMM_INSTRUMENT_POS_OFFSET",
                            "0",
                        )
                        .strip()
                        .lower()
                    )

                    if _offset_raw in {"default", ""}:
                        _offset = 0
                    else:
                        try:
                            _offset = int(_offset_raw)
                        except ValueError as exc:
                            raise ValueError(
                                "SYSTEMGMMKIT_FOD_GMM_INSTRUMENT_POS_OFFSET must be an integer, 'default', or empty."
                            ) from exc

                    instrument_pos = pos + _offset

                for lag in range(block.min_lag, block.max_lag + 1):
                    val = _lagged_level_instrument_at(s, instrument_pos, lag)

                    if val is not None:
                        z_dict[f"D:{block_label}:L{lag}"] = val
"""

if old not in text:
    raise RuntimeError("Could not find transformed-equation GMM instrument block.")

text = text.replace(old, new, 1)
path.write_text(text, encoding="utf-8")

print("Patched FOD transformed-equation GMM instrument timing offset diagnostic.")
