from pathlib import Path

path = Path("src/systemgmmkit/native_gmm.py")
text = path.read_text(encoding="utf-8")

backup = Path("artifacts/parity/xtabond2/native_gmm_before_fix_hansen_nameerror.py")
backup.parent.mkdir(parents=True, exist_ok=True)
backup.write_text(text, encoding="utf-8")

bad = '''    _n_groups_for_hansen = max(int(getattr(result, "n_groups", 0) or 0), 1)
'''

good = '''    # Use the input panel groups here because the result object has not
    # been constructed yet at this point in the function.
    _n_groups_for_hansen = max(int(df[entity].nunique()), 1)
'''

if bad not in text:
    print("Could not find the bad result-based n_groups line.")
    print("Inspect with:")
    print(r'rg -n -C 20 -e "_n_groups_for_hansen" .\src\systemgmmkit\native_gmm.py')
    raise SystemExit(1)

text = text.replace(bad, good, 1)
path.write_text(text, encoding="utf-8")

print("Fixed Hansen group-scaling NameError.")
print(f"Backup written to: {backup}")