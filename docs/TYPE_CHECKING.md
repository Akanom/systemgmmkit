# Progressive Type Checking

`systemgmmkit` enforces mypy incrementally. The stage-1 gate covers the stable
specification, static-estimator, result, and table path without pretending that
the entire package is already clean.

## Run the gate

Use Python 3.12 or newer for the typing toolchain:

```bash
python -m pip install -e ".[typing]"
python -m mypy
```

The command and its file list live in `[tool.mypy]` in `pyproject.toml`. CI runs
the same command on Python 3.12. The `typing` extra installs maintained pandas
and SciPy stubs; the configuration does not use `ignore_missing_imports` or
disable error codes.

## Stage-1 scope

The enforced files are:

1. `src/systemgmmkit/spec.py`
2. `src/systemgmmkit/validation.py`
3. `src/systemgmmkit/tables.py`
4. `src/systemgmmkit/linear.py`
5. `src/systemgmmkit/fixed_effects.py`
6. `src/systemgmmkit/panel_iv.py`
7. `src/systemgmmkit/random_effects.py`
8. `src/systemgmmkit/estimators/first_difference.py`
9. `src/systemgmmkit/suite.py`

`follow_imports = "silent"` is deliberate: mypy uses imported interfaces when
checking these nine explicit targets, but typing debt in modules outside the
stage-1 boundary does not make this first ratchet unenforceable. Adding a file
to the list makes its errors blocking. Removing a file weakens the gate and
requires explicit review.

## Baseline and expansion plan

On 2026-08-01, the stage-1 command passed with no issues in nine source files
under mypy 2.3.0. A full-package audit with the same checks and typed scientific
dependencies reported 78 errors in 17 of 43 source files. That audit is a debt
inventory, not a waived baseline: no error snapshots, blanket ignores, or broad
suppression rules are committed.

Expand the gate in focused pull requests:

1. repair the dynamic-panel dispatch typing and native-GMM row/instrument types,
   then add `dynamic_panel.py` and `native_gmm.py`;
2. type the pydynpd adapter, parser, and GMM diagnostics boundary;
3. cover post-estimation, visualization, and ML modules;
4. finish optional OutputHub integration, presets, parity orchestration, CLI,
   and package exports;
5. enable stronger return-value checks once NumPy/pandas result annotations no
   longer leak `Any` through otherwise typed estimator functions.

Each expansion must preserve numerical tests and should add regression tests for
any runtime defect exposed by the typing work.
