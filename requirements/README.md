# Reproducible environments

The `.in` files are human-maintained inputs. Their corresponding `.txt` files
are hash-pinned sets; each generated header records the interpreter version.
The `.txt` extension is used because `.lock` files are not stored in the
OneDrive workspace. Generate the CI and release sets on Linux with Python 3.12
so platform-conditional dependencies match the runner.

Regenerate the platform-neutral runtime and documentation sets from the
repository root with:

```powershell
python -m pip install "pip-tools>=7.5,<8"
pip-compile --generate-hashes --resolver=backtracking --strip-extras --no-emit-index-url --no-emit-trusted-host requirements/runtime.in -o requirements/runtime.txt
pip-compile --generate-hashes --resolver=backtracking --strip-extras --no-emit-index-url --no-emit-trusted-host requirements/docs.in -o requirements/docs.txt
```

Regenerate the Linux CI and release sets with:

```powershell
docker run --rm -v "${PWD}:/workspace" -w /workspace python:3.12-slim sh -c 'python -m pip install "pip-tools>=7.5,<8" && pip-compile --generate-hashes --resolver=backtracking --strip-extras --no-emit-index-url --no-emit-trusted-host requirements/test.in -o requirements/test.txt && pip-compile --generate-hashes --resolver=backtracking --strip-extras --no-emit-index-url --no-emit-trusted-host requirements/release.in -o requirements/release.txt'
```

Install a locked environment with:

```powershell
python -m pip install --require-hashes -r requirements/runtime.txt
```

Regenerate and verify the sets whenever a dependency changes. Additional
per-Python-version `.txt` sets should be added if resolution diverges
materially.
