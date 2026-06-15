## systemgmmkit 0.5.5

`systemgmmkit 0.5.5` consolidates the `0.5.x` development cycle and updates the public PyPI package after major improvements to native dynamic-panel GMM estimation, backend routing, Stata parity validation, diagnostic reporting, and reproducible output workflows.

This release should be treated as the current cumulative public release for the `0.5.x` series.

### Highlights

* Updates the public package to `systemgmmkit==0.5.5`.
* Expands `systemgmmkit` as a Python workflow package for panel-data econometrics, covering:

  * panel-structure validation;
  * pooled OLS-style panel models;
  * one-way fixed effects;
  * two-way fixed effects;
  * random effects;
  * panel IV / 2SLS;
  * Difference GMM;
  * System GMM;
  * backend routing;
  * diagnostics;
  * reproducible reporting;
  * regression-table export.
* Adds and stabilizes the public dynamic-GMM API:

  * `run_dynamic_panel_gmm()`;
  * `run_difference_gmm()`;
  * `run_system_gmm()`.
* Strengthens native Difference GMM support.
* Strengthens native System GMM support with verified `xtabond2` parity across the maintained benchmark suite.
* Improves support for:

  * collapsed instruments;
  * restricted lag windows;
  * endogenous regressors;
  * predetermined regressors;
  * exogenous IV-style instruments;
  * one-step and two-step configurations;
  * model-card style reporting;
  * regression-table export to Markdown, CSV, and LaTeX.
* Adds reviewer-facing parity artifacts and clearer validation documentation.

### Native Difference GMM

The native Difference GMM path is now part of the validated dynamic-panel GMM workflow.

The current benchmark validates native Difference GMM against the maintained reference backend / Stata oracle within numerical tolerance for the tested specification.

Supported features include:

* Arellano-Bond Difference GMM structure;
* lagged-level GMM instruments;
* endogenous, predetermined, and exogenous variable classification;
* variable-specific lag-window control;
* collapsed instruments;
* one-step and two-step estimation paths where supported;
* structured result objects;
* effective observation-count reporting;
* instrument-count reporting.

### Native System GMM

This release includes the strongest System GMM validation work in the package so far.

Native System GMM now passes the maintained `xtabond2` parity benchmark for collapsed two-step System GMM, including:

* sample size;
* panel-group count;
* instrument count;
* coefficient estimates;
* raw residual moments, including `Z'u`;
* group-scaled two-step weighting matrix alignment, including `A2 / n_groups`;
* Hansen J diagnostics;
* Windmeijer-corrected two-step standard errors;
* signed Arellano-Bond AR(1)/AR(2) diagnostics and p-values.

The maintained baseline specification is certified as:

```text
PASS_STRICT_XTABOND2_SYSTEM_GMM_BASELINE
```

Additional System GMM parity validation covers:

* baseline controls;
* no-controls specification;
* three-way interaction specification;
* decomposition-controls specification.

These checks strengthen the package’s reviewer-facing credibility by validating not only coefficients and standard errors, but also key post-estimation diagnostics.

### Row-level System GMM construction

The native System GMM implementation now uses row-level metadata during matrix construction.

Each constructed row carries:

* entity identifier;
* time identifier;
* equation type;
* original row index;
* underlying error-term composition.

This avoids relying only on balanced-panel block assumptions and improves support for more general panel structures.

The construction logic has been validated across:

* balanced panels;
* unbalanced panels;
* panels with missing internal periods;
* shorter panels;
* models with and without time dummies;
* models with and without standard IV controls;
* single and multiple GMM-style instrument blocks.

### Backend routing

The dynamic-GMM backend policy has been clarified.

Users should call the public API:

```python
from systemgmmkit import run_system_gmm, run_difference_gmm
```

The package then routes estimation through the selected backend.

Supported backend options include:

* `backend="auto"`;
* `backend="validated"`;
* `backend="native"`;
* `backend="pydynpd"`.

The recommended public route remains `backend="auto"` unless the user needs explicit native/backend comparison or strict replication of a validation benchmark.

### Variable classification and lag-window control

The `0.5.x` series improves the econometric workflow for dynamic-panel GMM by making variable classification explicit.

Users can classify variables as:

* `endogenous`;
* `predetermined`;
* `exogenous`.

Variable-specific GMM lag windows can be controlled through `lag_limits`.

This allows different lag structures for:

* the lagged dependent variable;
* endogenous regressors;
* predetermined regressors;
* interaction terms;
* decomposition variables;
* applied controls.

This is important for reducing instrument proliferation and making empirical specifications easier to document and defend.

### Reporting and export

The package supports reproducible reporting through:

* model-card style result summaries;
* structured result objects;
* Markdown export;
* CSV export;
* LaTeX export;
* regression-table export through `export_regression_table()`.

This improves the package’s usefulness for applied research workflows, thesis projects, journal appendices, and reviewer-facing replication materials.

### Stata parity and validation artifacts

This release adds and updates reviewer-facing Stata parity artifacts for native dynamic-panel GMM validation.

The System GMM validation artifacts document parity against Stata `xtabond2` for the maintained benchmark specifications, including:

* coefficients;
* standard errors;
* instrument counts;
* Hansen diagnostics;
* signed AR diagnostics;
* Windmeijer-corrected two-step covariance behavior;
* generated comparison tables.

Relevant artifact outputs include:

```text
artifacts/parity/xtabond2/xtabond2_native_system_gmm_parity.md
artifacts/parity/xtabond2/ar_diagnostics_comparison.md
artifacts/parity/xtabond2/native_xtabond2_ar_diagnostics_validation.csv
```

### Validation boundary

This release makes a strong but bounded validation claim.

Certified / validated:

* native Difference GMM on the maintained benchmark;
* native System GMM on the maintained `xtabond2` collapsed two-step benchmark;
* System GMM coefficients, instrument counts, Hansen diagnostics, Windmeijer-corrected two-step standard errors, and signed AR diagnostics for the certified benchmark suite;
* backend routing and structured result handling for applied workflows.

Not claimed:

* universal identity with every possible Stata `xtabond2` configuration;
* universal identity across every missing-data pattern, lag window, instrument classification, covariance assumption, or finite-sample correction;
* full certification of every possible unbalanced-panel design;
* parity for experimental FOD Windmeijer covariance or FOD AR diagnostic paths unless explicitly documented in a separate validation artifact.

The correct interpretation is:

```text
systemgmmkit 0.5.4 provides benchmark-specific Stata parity certification for the maintained native System GMM validation suite, not a universal claim of bit-for-bit equivalence across all dynamic-panel GMM specifications.
```

### Installation

Install the current release from PyPI:

```bash
python -m pip install systemgmmkit==0.5.5
```

Upgrade to the latest available release:

```bash
python -m pip install --upgrade systemgmmkit
```

Install with optional backend and reporting extras:

```bash
python -m pip install "systemgmmkit[all]"
```

Development installation from a local clone:

```bash
python -m pip install -e ".[dev,all]"
```

### Recommended reporting note

For academic or applied work, report the package version, backend, model specification, lag windows, instrument count, covariance type, and validation context.

Suggested wording:

```text
Estimation was performed using systemgmmkit 0.5.4. Dynamic-panel GMM models used the selected systemgmmkit backend with collapsed instruments, restricted lag windows, and documented endogenous/predetermined/exogenous variable classification. For native System GMM, the maintained collapsed two-step benchmark has been validated against Stata xtabond2 for coefficients, Windmeijer-corrected standard errors, Hansen diagnostics, and signed Arellano-Bond AR diagnostics.
```

### Summary

`systemgmmkit 0.5.5` is the strongest public release so far. It moves the package beyond basic dynamic-panel GMM execution toward a reviewer-facing empirical workflow with native Difference GMM, native System GMM, explicit backend routing, Stata parity artifacts, structured diagnostics, and reproducible reporting.
