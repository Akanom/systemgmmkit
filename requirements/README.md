# Reproducible environments

The `.in` files are human-maintained inputs. Their corresponding `.txt` files
are hash-pinned lock sets generated with Python 3.11; the `.txt` extension is
used because `.lock` files are not stored in the OneDrive workspace.

Regenerate from the repository root with:

```powershell
python -m pip install "pip-tools>=7.5,<8"
pip-compile --generate-hashes --resolver=backtracking --strip-extras --no-emit-index-url --no-emit-trusted-host requirements/runtime.in -o requirements/runtime.txt
pip-compile --generate-hashes --resolver=backtracking --strip-extras --no-emit-index-url --no-emit-trusted-host requirements/test.in -o requirements/test.txt
pip-compile --generate-hashes --resolver=backtracking --strip-extras --no-emit-index-url --no-emit-trusted-host requirements/docs.in -o requirements/docs.txt
pip-compile --generate-hashes --resolver=backtracking --strip-extras --no-emit-index-url --no-emit-trusted-host requirements/release.in -o requirements/release.txt
```

Install a locked environment with:

```powershell
python -m pip install --require-hashes -r requirements/runtime.txt
```

Regenerate and verify the lock sets whenever a dependency changes. Additional
per-Python-version lock sets should be added if resolution diverges materially
from the Python 3.11 set.
