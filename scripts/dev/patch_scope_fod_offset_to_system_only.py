from pathlib import Path

path = Path("src/systemgmmkit/native_gmm.py")
lines = path.read_text(encoding="utf-8").splitlines(keepends=True)

env_idx = None
for i, line in enumerate(lines):
    if "SYSTEMGMMKIT_FOD_GMM_INSTRUMENT_POS_OFFSET" in line:
        env_idx = i
        break

if env_idx is None:
    raise RuntimeError("Could not find SYSTEMGMMKIT_FOD_GMM_INSTRUMENT_POS_OFFSET in native_gmm.py")

# Walk upward from the env var to find the active FOD condition that guards the GMM instrument offset.
cond_idx = None
for j in range(env_idx, max(-1, env_idx - 40), -1):
    stripped = lines[j].strip()
    if stripped == 'if transformation_normalized == "fod":':
        cond_idx = j
        break
    if stripped == 'if transformation_normalized == "fod" and bool(spec.system):':
        print("FOD GMM offset is already scoped to System GMM only.")
        path.write_text("".join(lines), encoding="utf-8")
        raise SystemExit(0)

if cond_idx is None:
    snippet = "".join(lines[max(0, env_idx - 25) : min(len(lines), env_idx + 25)])
    raise RuntimeError(
        "Could not find the FOD condition above SYSTEMGMMKIT_FOD_GMM_INSTRUMENT_POS_OFFSET.\n"
        "Snippet:\n" + snippet
    )

indent = lines[cond_idx].split("if ", 1)[0]
lines[cond_idx] = f'{indent}if transformation_normalized == "fod" and bool(spec.system):\n'

path.write_text("".join(lines), encoding="utf-8")

print("Scoped FOD GMM instrument offset to System GMM only.")
print(f"Patched line {cond_idx + 1}.")
