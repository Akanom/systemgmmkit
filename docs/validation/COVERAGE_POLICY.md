# Coverage policy

`systemgmmkit` enforces coverage in a dedicated Linux/Python 3.12 CI job with
all optional package dependencies installed. The compatibility matrix continues
to run without coverage instrumentation, so Python-version checks are not made
slower by coverage collection.

## Initial measured baseline

The pre-gate baseline was measured from `origin/main` commit `3b9d25d` on
Python 3.14.6 with all extras installed and `coverage.py 7.15.2`:

| Metric | Covered / total | Baseline |
| --- | ---: | ---: |
| Project statements | 5,080 / 6,982 | 72.76% |
| Project branches | 1,368 / 2,552 | 53.61% |
| Combined statements and branches | 6,448 / 9,534 | 67.63% |
| `dynamic_panel.py` statements | 20 / 101 | 19.80% |
| `dynamic_panel.py` branches | 0 / 32 | 0.00% |

The focused routing and failure-path tests introduced with the gate produced
the following local verification result on the same interpreter and dependency
class:

| Metric | Covered / total | Verified result | Enforced minimum |
| --- | ---: | ---: | ---: |
| Project statements | 5,161 / 6,982 | 73.92% | 72.00% |
| Project branches | 1,400 / 2,552 | 54.86% | 53.00% |
| Combined statements and branches | 6,561 / 9,534 | 68.82% | 66.00% |
| `dynamic_panel.py` statements | 101 / 101 | 100.00% | 100.00% |
| `dynamic_panel.py` branches | 32 / 32 | 100.00% | 100.00% |

The project floors retain a small platform/interpreter margin below the observed
baseline. The `dynamic_panel.py` target is exact because its backend-selection,
adapter-signature, metadata, warning, environment-override, import-failure, and
public-wrapper branches are deterministic and directly tested.

## Post-PR40 integrated measurement

The post-PR40 source and test tree was measured after merging `origin/main`
commit `269eb307` into the coverage branch at signed merge commit `736d410`.
The 2026-08-06 verification used Python 3.12.3 on Windows with all extras and
`coverage.py 7.15.2`; all 330 tests passed before the ratchets were evaluated:

| Metric | Covered / total | Verified result | Enforced minimum |
| --- | ---: | ---: | ---: |
| Project statements | 5,179 / 6,723 | 77.03% | 72.00% |
| Project branches | 1,404 / 2,438 | 57.59% | 53.00% |
| Combined statements and branches | 6,583 / 9,161 | 71.86% | 66.00% |
| `dynamic_panel.py` statements | 101 / 101 | 100.00% | 100.00% |
| `dynamic_panel.py` branches | 32 / 32 | 100.00% | 100.00% |

These values supersede the earlier focused result as the current integrated
measurement. The initial pre-gate baseline above remains the historical point
from which the coverage policy was introduced. The enforced floors are not
raised by this integration because their documented platform margin has not yet
been validated on the Linux/Python 3.12 CI runner.

## Enforcement

The `[tool.coverage]` configuration in `pyproject.toml` enables branch coverage,
measures the complete `systemgmmkit` source package without coverage exclusions,
and enforces the 66% combined floor. `scripts/check_coverage.py` independently
enforces project statement and branch floors plus the targeted
`dynamic_panel.py` floors from the generated JSON report.

Run the same gates locally with:

```powershell
python -m pip install -e ".[dev,all]" "coverage==7.15.2"
python -m coverage erase
python -m coverage run -m pytest
python -m coverage json -o coverage.json
python scripts/check_coverage.py coverage.json
python -m coverage report
```

## Ratchet rules

1. Do not omit production modules, branches, or failure paths merely to increase
   the reported percentage.
2. Changes to dynamic-panel backend routing must retain 100% statement and branch
   coverage in `dynamic_panel.py`.
3. New or changed high-risk estimator paths should add behavioral tests for
   success, validation, dependency failure, and fallback branches before raising
   a target.
4. Raise project floors after the Python 3.12 job is stable on `main`; record the
   commit, interpreter, counts, and percentages used for each ratchet.
5. Do not lower a floor to make a pull request pass. Investigate the regression
   or explicitly document a deliberate, reviewed increase in untested surface.

Coverage is a regression signal, not proof of econometric correctness. Numerical
parity, conformance, diagnostics, and real-data certification remain separate
release gates.
