from pathlib import Path

path = Path("src/systemgmmkit/native_gmm.py")
lines = path.read_text(encoding="utf-8").splitlines(keepends=True)

target_idx = None

for i, line in enumerate(lines):
    if "val = _safe_get(s, pos)" not in line:
        continue

    window_before = "".join(lines[max(0, i - 8) : i + 1])
    window_after = "".join(lines[i : min(len(lines), i + 8)])

    # Only patch the transformed-equation IV block, not unrelated safe_get calls.
    if (
        'str(spec.transformation).strip().lower() == "fod"' in window_before
        and "_transform_at(s, pos, spec.transformation)" in window_after
    ):
        target_idx = i
        break

if target_idx is None:
    raise RuntimeError(
        "Could not find active FOD IV safe_get line. "
        "Run Select-String around 'D:iv' and 'safe_get(s, pos)' to inspect current code."
    )

indent = lines[target_idx].split("val = _safe_get", 1)[0]

replacement = [
    f"{indent}import os as _native_fod_iv_os\n",
    f"{indent}_iv_offset_raw = (\n",
    f"{indent}    _native_fod_iv_os.getenv(\n",
    f'{indent}        "SYSTEMGMMKIT_FOD_IV_INSTRUMENT_POS_OFFSET",\n',
    f'{indent}        "0",\n',
    f"{indent}    )\n",
    f"{indent}    .strip()\n",
    f"{indent}    .lower()\n",
    f"{indent})\n",
    f'{indent}if _iv_offset_raw in {{"default", ""}}:\n',
    f"{indent}    _iv_offset = 0\n",
    f"{indent}else:\n",
    f"{indent}    try:\n",
    f"{indent}        _iv_offset = int(_iv_offset_raw)\n",
    f"{indent}    except ValueError as exc:\n",
    f"{indent}        raise ValueError(\n",
    f'{indent}            "SYSTEMGMMKIT_FOD_IV_INSTRUMENT_POS_OFFSET must be an integer, default, or empty."\n',
    f"{indent}        ) from exc\n",
    f"{indent}val = _safe_get(s, pos + _iv_offset)\n",
]

lines[target_idx : target_idx + 1] = replacement
path.write_text("".join(lines), encoding="utf-8")

print("Patched FOD IV-style instrument timing diagnostic.")
