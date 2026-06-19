# Contributing

Thank you for contributing to `systemgmmkit`.

`systemgmmkit` is a Python package for applied panel-data econometrics, dynamic-panel GMM estimation, post-estimation, diagnostics, visualization, and reproducible reporting.

The project prioritizes:

* correctness;
* reproducibility;
* transparent model specification;
* benchmark validation against trusted reference implementations;
* clean public APIs;
* reviewer-facing documentation;
* tested examples;
* publication-quality reporting workflows.

Contributions should improve the package without weakening estimator reliability, validation discipline, or public API consistency.

---

# Development Setup

## 1. Clone the repository

```bash
git clone https://github.com/Akanom/systemgmmkit.git
cd systemgmmkit
```

## 2. Create a virtual environment

Linux / macOS:

```bash
python -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

## 3. Upgrade packaging tools

```bash
python -m pip install --upgrade pip setuptools wheel
```

## 4. Install the package in editable mode

Recommended development install:

```bash
python -m pip install -e ".[dev,all]"
```

If you are working on graphics, reports, or SGM-Viz functionality, ensure graphics dependencies are available:

```bash
python -m pip install matplotlib
```

If you are testing local integration with `universal-output-hub`, install it in editable mode from its local repository:

```bash
python -m pip install -e "<PATH_TO_UNIVERSAL_OUTPUT_HUB>"
```

---

# Local Development Workflow

Before making changes, create a feature or fix branch.

```bash
git switch main
git pull
git switch -c feature/<short-name>
```

Examples:

```bash
git switch -c feature/sgm-viz-report-modes
git switch -c fix/system-gmm-instrument-count
git switch -c docs/readme-0510
```

Keep commits focused. Avoid mixing unrelated estimator changes, documentation changes, and visualization changes in the same commit unless they are part of one coherent feature.

---

# Branching Model

| Branch type            | Purpose                                            |
| ---------------------- | -------------------------------------------------- |
| `main`                 | Production-ready code only                         |
| `develop`              | Optional integration branch for completed features |
| `feature/<short-name>` | New features                                       |
| `fix/<short-name>`     | Bug fixes                                          |
| `docs/<short-name>`    | Documentation-only changes                         |
| `test/<short-name>`    | Test or validation workflow changes                |
| `release/vX.Y.Z`       | Release preparation                                |

Do not commit directly to `main` unless explicitly maintaining a solo local development workflow and the change has already passed the full quality gate.

---

# Quality Gate

Before opening a pull request or merging into `main`, run the core quality gate:

```bash
ruff check .
ruff format --check .
pytest
python -m build
```

For Windows PowerShell:

```powershell
ruff check .
ruff format --check .
pytest
python -m build
```

A change is not ready if any of these fail.

---

# Targeted Test Commands

Use targeted tests during development, then run the full suite before merge.

## Post-estimation and graphics

```bash
pytest tests/test_postestimation_graphics.py -q
pytest tests/test_sgm_viz_v2.py -q
pytest tests/test_result_plot_accessor.py -q
pytest tests/test_standard_gallery.py -q
```

Combined:

```bash
pytest tests/test_postestimation_graphics.py tests/test_sgm_viz_v2.py tests/test_result_plot_accessor.py tests/test_standard_gallery.py -q
```

## Dynamic GMM parity and diagnostics

Run the relevant parity or conformance scripts maintained under the repository’s `scripts/` and `artifacts/` workflows.

Examples may include:

```bash
pytest tests -q
```

and, where Stata is available locally, the maintained Stata comparison workflows.

Do not claim Stata parity for a new estimator path unless the maintained benchmark artifacts support that claim.

## Import and version check

```bash
python -c "import systemgmmkit; print(systemgmmkit.__version__)"
```

## Build check

```bash
python -m build
```

---

# Coding Standards

## General principles

Code should be:

* explicit;
* typed where practical;
* readable;
* tested;
* backward compatible where possible;
* robust to missing optional dependencies;
* clear about assumptions.

Avoid hidden behaviour in estimator code. Econometric assumptions should be visible in the model specification, result metadata, or documentation.

## Public API rules

Public APIs should be stable, predictable, and documented.

When adding a public function, class, or argument:

1. add or update tests;
2. update relevant exports;
3. update documentation;
4. update examples if user-facing;
5. update the changelog;
6. preserve backward compatibility unless there is a strong reason not to.

## Error handling

Prefer clear errors over silent failure.

Good errors should explain:

* what failed;
* which argument or object caused the failure;
* what the user should change.

## Optional dependencies

Optional integrations should fail gracefully.

For example, plotting functionality may require `matplotlib`. If a plotting dependency is missing, the error should tell the user what to install.

---

# Econometric Validation Standards

Estimator changes require stronger validation than ordinary utility changes.

## Static estimators

For OLS, pooled OLS, fixed effects, random effects, and panel IV / 2SLS changes, contributors should provide one or more of:

* analytical unit tests;
* comparison against known results;
* comparison against Stata, R, or another trusted implementation;
* regression tests against maintained benchmark artifacts.

## Dynamic GMM estimators

Dynamic GMM changes require careful validation.

Relevant validation areas include:

* transformed-equation construction;
* lagged dependent-variable handling;
* endogenous-variable instrumentation;
* predetermined-variable instrumentation;
* exogenous-variable IV-style treatment;
* global GMM lag windows;
* role-specific GMM lag windows;
* variable-specific GMM lag windows;
* collapsed versus uncollapsed instruments;
* instrument count;
* instrument names or blocks;
* coefficient estimates;
* Windmeijer-corrected standard errors;
* Hansen diagnostics;
* Sargan diagnostics;
* AR(1) diagnostics;
* AR(2) diagnostics;
* sample size;
* group count.

Do not broaden validation claims beyond the maintained benchmark evidence.

If a workflow is only externally validated or near-parity, document it as such.

---

# Dynamic GMM Instrumentation Rules

Contributors should preserve the distinction between structural lags and instrument lags.

## Structural lags

Structural lags are variables included directly in the model equation.

Example:

```python
regressors = ["L1_y", "L1_investment"]
```

These variables must exist as columns in the input data.

## Instrument lags

Instrument lags define which lagged values are used internally as GMM instruments.

Example:

```python
gmm_lags = (2, 4)
```

## Variable classification

Dynamic GMM specifications should distinguish:

```python
endogenous = ["L1_y", "investment"]
predetermined = ["cashflow"]
exogenous = ["firm_size", "year2023"]
```

## Lag-window precedence

Where supported, lag-window precedence should remain:

```text
gmm_lags_by_variable > gmm_lags_by_role > gmm_lags
```

## Exogenous variables

Exogenous variables should remain IV-style by default unless the API explicitly supports and documents alternative behaviour.

Do not accidentally force exogenous variables into GMM-style instrumentation.

---

# Graphics and Reporting Standards

`systemgmmkit` includes two visualization layers:

1. standard post-estimation plots;
2. SGM-Viz diagnostic dashboards.

## Standard post-estimation plots

Standard plots should remain useful for R/Stata-style applied workflows:

* coefficient plots;
* marginal effects plots;
* margins / prediction plots;
* interaction plots;
* conditional effects plots;
* residual diagnostics;
* fixed-effects plots;
* panel trajectory plots;
* instrument count plots;
* diagnostic p-value plots;
* counterfactual plots;
* effect-surface plots.

## SGM-Viz dashboards

SGM-Viz plots should communicate dynamic-panel diagnostics clearly:

* model health;
* persistence;
* instrument architecture;
* effect surfaces;
* publication panels;
* model comparison dashboards.

## Figure export requirements

Plotting functions should support file export through a `save=` argument where practical.

Accepted output formats should include common Matplotlib-supported formats such as:

* PNG;
* SVG;
* PDF.

## Gallery export requirements

HTML gallery exports should avoid unnecessary duplication.

SGM-Viz report modes should remain:

```text
dashboard    = individual dashboards only
publication  = composed publication panel only
full         = all figures
```

---

# Documentation Standards

Documentation should be accurate, conservative, and implementation-aligned.

Do not document planned functionality as current functionality.

When documenting an estimator or diagnostic feature, state clearly whether it is:

* implemented;
* tested;
* benchmarked;
* externally validated;
* experimental;
* planned.

README, changelog, examples, and docstrings should agree with each other.

---

# Changelog Requirements

Every user-facing change should update `CHANGELOG.md`.

Include entries under the relevant release version:

```markdown
## X.Y.Z

### Added

### Changed

### Fixed

### Validation

### Documentation
```

Use `Validation` when the change affects estimator correctness, parity, diagnostics, or benchmark evidence.

Use `Documentation` when examples, README, API notes, or methodology guidance are changed.

---

# Pull Request Checklist

Before opening a pull request, confirm:

```text
[ ] The change is implemented.
[ ] The change is tested.
[ ] Existing tests pass.
[ ] New tests are added where needed.
[ ] Documentation is updated.
[ ] CHANGELOG.md is updated.
[ ] Public exports are updated if a new public API was added.
[ ] Examples are updated if the feature is user-facing.
[ ] Estimator validation claims are supported by benchmark evidence.
[ ] No generated junk files, local paths, cache files, or private artifacts are committed.
[ ] Ruff passes.
[ ] Build succeeds.
```

---

# Files That Should Not Be Committed

Do not commit:

* virtual environments;
* local cache directories;
* local editor files;
* private machine paths;
* temporary debug files;
* large generated artifacts unless intentionally tracked;
* credentials;
* API keys;
* private data;
* user-specific absolute paths;
* local Stata logs unless part of a maintained benchmark artifact;
* temporary notebook checkpoints.

Common examples:

```text
.venv/
__pycache__/
.pytest_cache/
.ruff_cache/
*.pyc
*.tmp
*.bak
.env
.ipynb_checkpoints/
```

---

# Security and Privacy

Do not commit secrets or private paths.

Use placeholders in documentation:

```text
<PROJECT_DIR>
<DATA_DIR>
<OUTPUT_DIR>
<API_KEY>
<USER_HOME>
```

Avoid exposing:

* usernames;
* local machine paths;
* private repository paths;
* credentials;
* tokens;
* internal company data;
* restricted datasets.

---

# Definition of Done

A change is done only when it is:

* implemented;
* tested;
* lint-clean;
* documented;
* validated where relevant;
* backward-compatible where practical;
* reflected in `CHANGELOG.md`;
* reviewed through a pull request or equivalent review process;
* merged into the appropriate branch.

For estimator or diagnostic changes, “done” additionally requires:

* benchmark evidence or regression tests;
* clear validation status;
* no unsupported parity claims;
* updated documentation for assumptions and limitations.

For graphics or reporting changes, “done” additionally requires:

* at least one export test;
* at least one example or documented usage path;
* no broken gallery/report generation;
* no duplicated report content unless explicitly requested by the selected report mode.

---

# Release Checklist

Before preparing a release:

```text
[ ] Version updated in pyproject.toml.
[ ] Version updated in systemgmmkit.__version__.
[ ] README.md updated.
[ ] CHANGELOG.md updated.
[ ] Tests pass.
[ ] Ruff passes.
[ ] Build succeeds.
[ ] Public API import check passes.
[ ] Example scripts run where relevant.
[ ] Validation claims are current and accurate.
[ ] Release branch or tag is prepared.
```

Recommended commands:

```bash
ruff check .
ruff format --check .
pytest
python -m build
python -c "import systemgmmkit; print(systemgmmkit.__version__)"
```

---

# Maintainer Notes

Keep the package focused.

`systemgmmkit` should remain a serious applied econometrics package, not a collection of loosely related utilities.

New features should strengthen one of the core workflows:

* panel-data estimation;
* dynamic-panel GMM;
* post-estimation;
* diagnostics;
* validation;
* reporting;
* publication-quality visualization.

When in doubt, prefer a smaller, well-tested, well-documented feature over a broad but weakly validated one.
