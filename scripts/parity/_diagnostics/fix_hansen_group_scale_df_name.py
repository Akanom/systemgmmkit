import ast
import re
from pathlib import Path

path = Path("src/systemgmmkit/native_gmm.py")
text = path.read_text(encoding="utf-8")

backup = Path("artifacts/parity/xtabond2/native_gmm_before_fix_hansen_df_name.py")
backup.parent.mkdir(parents=True, exist_ok=True)
backup.write_text(text, encoding="utf-8")

tree = ast.parse(text)

func = None
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and node.name == "run_native_dynamic_panel_gmm":
        func = node
        break

if func is None:
    raise SystemExit("Could not find function run_native_dynamic_panel_gmm")

arg_names = [arg.arg for arg in func.args.args]

if len(arg_names) < 2:
    raise SystemExit(f"Unexpected function args: {arg_names}")

# Expected shape: run_native_dynamic_panel_gmm(spec, <data_arg>, entity=..., time=...)
data_arg = arg_names[1]

print(f"Detected data argument name: {data_arg}")

old = '''    _n_groups_for_hansen = max(int(df[entity].nunique()), 1)
'''

new = f'''    _n_groups_for_hansen = max(int({data_arg}[entity].nunique()), 1)
'''

if old not in text:
    # fallback for any previous replacement attempt
    pattern = re.compile(
        r"^    _n_groups_for_hansen = max\(int\([A-Za-z_][A-Za-z0-9_]*\[entity\]\.nunique\(\)\), 1\)\r?$",
        re.MULTILINE,
    )
    matches = list(pattern.finditer(text))

    if len(matches) != 1:
        print(f"Could not find exactly one _n_groups_for_hansen dataset line. Found {len(matches)}.")
        print("Inspect with:")
        print(r'rg -n -C 25 -e "_n_groups_for_hansen" .\src\systemgmmkit\native_gmm.py')
        raise SystemExit(1)

    text = pattern.sub(new.rstrip(), text, count=1)
else:
    text = text.replace(old, new, 1)

path.write_text(text, encoding="utf-8")

print("Fixed Hansen group-scaling dataset variable name.")
print(f"Backup written to: {backup}")