# Changelog

All notable changes to `systemgmmkit` are documented in this file.

The project follows a practical semantic-versioning style:

* patch releases may include estimator fixes, parity corrections, documentation updates, validation improvements, and workflow refinements;
* minor releases may introduce new estimator families, result objects, reporting layers, or visualization systems;
* validation claims are benchmark-specific and apply to the maintained parity workflows in the repository.

---

## 0.5.11

### Added

* Added the new `systemgmmkit.ml` namespace for additive ML-style workflow utilities around already fitted econometric result objects.

* Added generic result adaptation through `ResultAdapter` and `adapt_result()` for duck-typed access to fitted model parameters, covariance matrices, diagnostics, and metadata.

* Added ML-style prediction helpers:

  * `predict()`;
  * `fitted_values()`;
  * `residuals()`.

* Added `regression_metrics()` for standard predictive-performance metrics:

  * MAE;
  * MSE;
  * RMSE;
  * MAPE;
  * SMAPE;
  * R²;
  * evaluated observation count.

* Added panel-aware train/test splitting through `panel_train_test_split()`.

* Added expanding-window panel time-series cross-validation through:

  * `PanelTimeSeriesSplit`;
  * `cross_validate_panel()`.

* Added `compare_models()` for comparing already fitted model results on a common evaluation dataset.

* Added recursive forecasting support through `forecast()`.

* Added expanding-window forecast backtesting through `backtest_forecast()`.

* Added `GMMGridSearch`, a lightweight specification-search scaffold that repeatedly calls existing validated GMM builders and runners.

* Added `GMMSearchResult` for structured GMM specification-search outputs.

* Added easier user-facing dynamic-GMM wrappers at the top level:

  ```python
  from systemgmmkit import difference_gmm, system_gmm
  ```

* Added `DynamicGMMWorkflowResult` for inspecting easy-GMM generated workflows when `return_workflow=True`.

* Added easy-GMM workflow metadata for:

  * fitted result object;
  * generated specification;
  * model dataframe after lag creation and missing-value handling;
  * final regressors;
  * endogenous variables;
  * predetermined variables;
  * exogenous variables;
  * global GMM lag window;
  * role-specific GMM lag windows;
  * variable-specific GMM lag windows;
  * collapse setting;
  * time-effect setting;
  * model type.

* Added role-specific GMM lag-window control:

  ```python
  gmm_lags_by_role = {
      "endogenous": (2, 3),
      "predetermined": (1, 2),
  }
  ```

* Added variable-specific GMM lag-window control:

  ```python
  gmm_lags_by_variable = {
      "L1_y": (2, 2),
      "cashflow": (1, 3),
  }
  ```

* Added deterministic GMM lag-window precedence:

  ```text
  gmm_lags_by_variable > gmm_lags_by_role > gmm_lags
  ```

* Added validation that exogenous variables remain IV-style by default unless explicitly classified otherwise.

* Added instrument-name and instrument-count validation for separate `gmm()` blocks in Difference GMM and System GMM.

* Added tests confirming that Difference GMM and System GMM generate separate GMM-style instrument blocks for variables with distinct lag windows.

* Added tests confirming that variable-specific lag windows override role-specific and global lag windows.

* Added tests confirming that role-specific lag windows override the global lag window.

* Added tests confirming that easy-GMM wrappers do not duplicate lagged dependent-variable notation.

* Added regression tests preventing easy-GMM workflows from producing both:

  ```text
  L1.y
  L1_y
  ```

  or both:

  ```text
  gmm(y, ...)
  gmm(L1_y, ...)
  ```

* Added FD001 real-data validation for easy-GMM lag-window workflows.

* Added FD001 real-data validation for compact instrument-count agreement across Difference GMM and System GMM scenarios.

* Added diagnostic p-value sanitation for backend outputs so impossible p-values are not reported as valid diagnostics.

* Added warning-language regression coverage to ensure native System GMM diagnostic-certification wording reflects the maintained benchmark status.

* Added a reviewer-facing ML workflow smoke script:

  ```bash
  python scripts/ml/run_ml_workflow_smoke.py --outdir artifacts/ml_workflow
  ```

* Added ML workflow smoke artifacts under `artifacts/ml_workflow`, including:

  * `static_panel.csv`;
  * `dynamic_panel.csv`;
  * `ols_predictions_residuals.csv`;
  * `panel_cv_scores.csv`;
  * `model_comparison.csv`;
  * `gmm_grid_search.csv`;
  * `forecast.csv`;
  * `forecast_backtest.csv`;
  * `summary.json`;
  * `README.md`.

* Added ML workflow documentation in `docs/ml_workflow.md`.

* Added `examples/ml_workflow_example.py` demonstrating prediction, residuals, cross-validation, model comparison, forecasting, backtesting, and GMM grid-search scaffolding.

* Added focused test coverage for the ML workflow layer:

  * `test_ml_workflow.py`;
  * `test_ml_workflow_integration.py`;
  * `test_ml_model_compare.py`;
  * `test_ml_forecast.py`;
  * `test_ml_backtest.py`;
  * `test_ml_workflow_smoke_script.py`.

### Changed

* Expanded the package positioning from estimation, post-estimation, and visualization toward a fuller empirical workflow:

  ```text
  estimate → diagnose → predict → validate → compare → forecast → backtest → report
  ```

* Documented `systemgmmkit.ml` as an additive workflow layer rather than a replacement for machine-learning libraries.

* Clarified that the ML-style workflow layer operates around already fitted econometric result objects.

* Kept the ML workflow API separate from the existing top-level post-estimation API to avoid collisions with existing public functions such as `predict()`.

* Updated the easy dynamic-GMM API so `time_effects=False` is the default for usability and compact real-data workflows.

* Mapped easy-API `time_effects` cleanly to lower-level `time_dummies`.

* Updated easy-GMM lagged dependent-variable handling so the easy wrapper creates concrete structural lag columns such as `L1_y` and prevents the lower-level builder from also adding symbolic `L1.y`.

* Updated easy-GMM command construction to remove duplicated structural-lag and instrument-lag handling.

* Updated easy-GMM instrument architecture so lagged dependent variables created by the easy API are handled as ordinary generated regressors, for example `L1_y`.

* Updated System GMM native backend warning language to reflect maintained benchmark certification for:

  * coefficients;
  * Windmeijer standard errors;
  * Hansen diagnostics;
  * Sargan diagnostics;
  * signed AR(1) diagnostics;
  * signed AR(2) diagnostics.

* Updated native System GMM result notes so they no longer describe Sargan/AR diagnostic parity as uncertified when the maintained benchmark suite certifies it.

* Updated README documentation to include:

  * ML-style workflow layer;
  * easy Difference GMM and System GMM wrappers;
  * role-specific GMM lag windows;
  * variable-specific GMM lag windows;
  * deterministic lag-window precedence;
  * FD001 easy-GMM lag-window validation;
  * corrected native System GMM diagnostic parity wording.

* Updated dynamic-GMM guidance to distinguish clearly between:

  * structural lags in the model equation;
  * lagged values used as GMM instruments.

* Updated documentation to state that exogenous variables remain IV-style by default.

* Updated validation language to distinguish:

  * strict controlled `xtabond2` certification;
  * external FD001 application validation;
  * API and workflow tests.

* Updated citation metadata for the current development line.

### Fixed

* Fixed a top-level API collision where ML-style `predict()` could shadow the existing public post-estimation `predict()` function.

* Fixed easy-GMM duplicated lagged dependent-variable handling.

* Fixed easy-GMM command generation so wrapper-generated lagged dependent variables do not create both symbolic and concrete lag names.

* Fixed easy-GMM specifications that previously produced duplicated instrument blocks such as:

  ```text
  gmm(y, ...)
  gmm(L1_y, ...)
  ```

* Fixed easy-GMM specifications that previously exposed commands containing both:

  ```text
  L1.y
  L1_y
  ```

* Fixed duplicate top-level imports of `difference_gmm` and `system_gmm` in `__init__.py`.

* Fixed Ruff import-order and redefinition issues introduced during easy-wrapper export stabilization.

* Fixed diagnostic p-value handling so invalid backend p-values outside the valid probability range are sanitized rather than reported as valid.

* Fixed stale System GMM native backend warning text that incorrectly described Sargan/AR diagnostic parity as uncertified.

* Fixed stale native System GMM result notes so they match the current maintained parity status.

* Fixed FD001 lag-window validation script behavior by forcing the intended native backend path for the real-data validation workflow.

* Fixed FD001 lag-window validation outputs so the generated command and instrument-count files reflect the cleaned easy-GMM specification.

* Removed temporary README patch scripts and backup files from the tracked project state.

* Fixed Ruff lint issues in the new ML workflow files.

* Fixed import ordering, unused imports, and Python compatibility issues detected by CI linting.

* Fixed the ML workflow smoke script contract so it:

  * accepts `--outdir`;
  * prints `PASS`;
  * writes the expected artifact filenames;
  * writes `summary.json` with expected row-count metadata.

### Validation

* Added unit tests for ML-style prediction, fitted values, residuals, and regression metrics.

* Added integration smoke tests confirming that the ML workflow layer works with real `systemgmmkit` OLS result objects.

* Added tests for panel-aware train/test splitting and expanding-window panel cross-validation.

* Added tests for `compare_models()` using both synthetic result objects and real OLS results.

* Added tests for recursive one-lag and two-lag dynamic-panel forecasting.

* Added tests for static-model forecasting behavior.

* Added tests for expanding-window forecast backtesting.

* Added tests for `GMMGridSearch` scaffolding.

* Added a smoke-script test confirming that the reviewer-facing ML workflow script runs successfully and writes the expected artifacts.

* Added tests for easy Difference GMM and easy System GMM wrappers.

* Added tests for global GMM lag-window handling through `gmm_lags`.

* Added tests for role-specific GMM lag-window handling through `gmm_lags_by_role`.

* Added tests for variable-specific GMM lag-window handling through `gmm_lags_by_variable`.

* Added tests confirming the precedence rule:

  ```text
  gmm_lags_by_variable > gmm_lags_by_role > gmm_lags
  ```

* Added tests confirming exogenous variables remain IV-style by default.

* Added tests confirming generated instrument names and expected compact instrument counts.

* Added tests confirming Difference GMM includes `nolevel` while System GMM does not.

* Added tests confirming easy-GMM wrappers avoid duplicated lagged dependent-variable notation.

* Added tests confirming native System GMM warning language reflects maintained diagnostic parity certification.

* Validated easy-GMM lag-window workflows on CMAPSS FD001 real-data panel specifications.

* Confirmed FD001 easy-GMM validation produces no symbolic `L1.risk` rows in generated commands.

* Confirmed FD001 easy-GMM validation produces no duplicated `gmm(risk, ...)` plus `gmm(L1_risk, ...)` instrumentation.

* Confirmed FD001 actual instrument counts equal expected compact instrument counts across all tested Difference GMM and System GMM scenarios:

  | Scenario                          |      Estimator | Actual instruments | Expected compact instruments | Status |
  | --------------------------------- | -------------: | -----------------: | ---------------------------: | ------ |
  | `global_compact_22`               | Difference GMM |                  6 |                            6 | PASS   |
  | `global_compact_22`               |     System GMM |                 11 |                           11 | PASS   |
  | `role_endog_23_predet_12`         | Difference GMM |                 10 |                           10 | PASS   |
  | `role_endog_23_predet_12`         |     System GMM |                 15 |                           15 | PASS   |
  | `variable_override_sensor_l1risk` | Difference GMM |                  9 |                            9 | PASS   |
  | `variable_override_sensor_l1risk` |     System GMM |                 14 |                           14 | PASS   |

* Confirmed that the ML workflow layer does not modify estimator internals.

* Confirmed that the ML workflow layer does not create new estimator-parity claims.

### Documentation

* Added a new ML-style workflow section to the README.

* Added examples for:

  * prediction;
  * fitted values;
  * residuals;
  * panel-aware cross-validation;
  * model comparison;
  * recursive forecasting;
  * forecast backtesting;
  * GMM specification-search scaffolding.

* Added documentation explaining that `systemgmmkit.ml` is designed for workflow orchestration around fitted econometric models, not for generic machine-learning model estimation.

* Added documentation for reviewer-facing smoke artifacts.

* Added documentation for easy Difference GMM and easy System GMM.

* Added documentation for structural lag handling through `lagged_dependent`.

* Added documentation for `lagged_dependent_role`.

* Added documentation for global, role-specific, and variable-specific GMM lag-window controls.

* Added documentation for deterministic GMM lag-window precedence.

* Added documentation explaining that exogenous variables remain IV-style by default.

* Added FD001 easy-GMM lag-window validation documentation.

* Updated validation language to distinguish estimator parity from workflow testing.

* Updated validation language to distinguish strict controlled benchmark certification from real-data application validation.

### Validation Boundary

Version `0.5.11` does not introduce new econometric estimator theory.

The new ML-style workflow layer is validated as a workflow layer. It does not alter or replace the existing validated estimator implementations.

The easy-GMM wrappers are convenience APIs over the existing dynamic-GMM builders and runners. They do not introduce a new estimator.

Role-specific and variable-specific GMM lag windows are implemented and tested as instrument-design controls. Their validation applies to the maintained tests and validation workflows, including the FD001 easy-GMM lag-window validation.

Certified and maintained estimator validation claims remain benchmark-specific and continue to apply only to the maintained parity workflows in the repository.

Not claimed in this release:

* replacement of dedicated ML libraries;
* universal Stata equivalence across all possible specifications;
* universal bit-for-bit equivalence across all lag windows, missing-data patterns, covariance estimators, or instrument designs;
* automatic validation of every user-specified GMM instrument strategy;
* automatic proof that a user’s chosen endogenous, predetermined, or exogenous classification is theoretically correct.

### Roadmap

The next technical extension should focus on robustness and preflight validation around GMM instrument design.

Planned features:

* preflight feasibility checks for impossible lag windows on short panels;
* clearer validation errors when requested GMM lags exceed usable panel depth;
* stronger handling of unknown variables in `gmm_lags_by_variable`;
* explicit rejection or warning when users try to apply GMM lag windows to exogenous-only variables;
* additional Stata comparison scripts for role-specific and variable-specific lag-window specifications;
* deeper documentation examples for instrument architecture;
* more real-data validation examples;
* richer post-estimation support for nonlinear combinations;
* extended marginal-effects workflows;
* additional integration examples with `universal-output-hub`.

Implemented and validated features should remain in the current-feature and validation sections, not in the roadmap.

---

## 0.5.10

### Added

* Added SGM-Viz v2, a dynamic-panel diagnostic visualization system for model-health, persistence, instrument architecture, effect surfaces, and publication-ready diagnostic panels.

* Added `HealthMetrics`, `InstrumentArchitecture`, and `PersistenceAnalytics` data structures for diagnostic visualization workflows.

* Added model-health dashboard support through `model_health_dashboard_v2()`.

* Added dynamic-persistence dashboard support through `dynamic_persistence_dashboard_v2()`, including persistence coefficient, shock-decay path, half-life, long-run multiplier, and persistence classification.

* Added instrument-architecture dashboard support through `instrument_architecture_dashboard_v2()`, including difference-equation instruments, level-equation instruments, standard instruments, lag range, collapse status, instrument count, and instrument/group ratio.

* Added effect-surface dashboard support through `effect_surface_dashboard_v2()`.

* Added composed publication-panel support through `publication_panel_v2()`.

* Added SGM-Viz HTML gallery export through `export_sgm_viz_v2_gallery()`.

* Added one-command SGM-Viz report export through `export_sgm_viz_report()`.

* Added report modes for SGM-Viz exports:

  * `dashboard`;
  * `publication`;
  * `full`.

* Added result-level plot accessor support:

  * `result.plot.health()`;
  * `result.plot.persistence()`;
  * `result.plot.instruments()`;
  * `result.plot.publication_panel()`;
  * `result.plot.standard_gallery()`;
  * `result.plot.export_all()`.

* Added `plot_accessor(result)` for result objects that do not support direct `.plot` attachment.

* Added `attach_plot_accessor(result)` for best-effort instance-level `.plot` attachment.

* Added `install_result_plot_accessors()` for best-effort class-level plot accessor installation on known result classes.

* Added `model_comparison_dashboard_v2()` for comparing alternative model specifications using Hansen, Sargan, AR(2), and instrument/group diagnostics.

* Added standard post-estimation graphics gallery support through `export_standard_postestimation_gallery()`.

* Added `StandardGalleryResult` for structured standard-gallery outputs.

* Added standard gallery coverage for:

  * coefficient plots;
  * marginal effects plots;
  * margins / prediction plots;
  * conditional effects plots;
  * interaction plots;
  * residuals vs fitted plots;
  * QQ residual plots;
  * residual histograms;
  * panel trajectory plots;
  * fixed-effects plots;
  * instrument count plots;
  * Hansen / Sargan / AR diagnostic plots;
  * counterfactual scenario plots;
  * 3D / effect-surface plots.

* Added support for plotting one figure directly without generating a full gallery.

* Added tests for SGM-Viz v2 dashboards.

* Added tests for result-level plotting accessors.

* Added tests for standard post-estimation gallery export.

* Added examples for:

  * SGM-Viz v2 demo gallery;
  * result-level SGM-Viz integration;
  * standard post-estimation gallery generation.

### Changed

* Updated public documentation from `0.5.9` to `0.5.10`.

* Expanded README coverage of post-estimation graphics, SGM-Viz dashboards, result-level plotting, and standard gallery workflows.

* Clarified the distinction between standard R/Stata-style post-estimation plots and SGM-Viz flagship diagnostic dashboards.

* Clarified single-plot usage versus full gallery/report export.

* Updated dynamic GMM documentation to cover endogenous, predetermined, and exogenous instrumentation more explicitly.

* Updated dynamic GMM documentation to distinguish structural lags included as regressors from lagged values used internally as GMM instruments.

* Clarified that exogenous variables remain IV-style by default unless explicitly handled otherwise.

* Improved HTML gallery export to avoid duplicated dashboard content by supporting report modes.

* Improved print/PDF CSS for SGM-Viz HTML reports.

* Improved gallery layout so publication panels can span full width where appropriate.

* Added `matplotlib` as an explicit graphics dependency where required by the installed package configuration.

### Fixed

* Fixed SGM-Viz HTML report CSS escaping inside Python f-string templates.

* Fixed publication-panel gallery rendering so the composed publication panel is not squeezed into a narrow gallery card.

* Fixed duplicated report content by separating dashboard, publication, and full report modes.

* Fixed title/subtitle spacing issues in post-estimation graphics.

* Fixed figure-closing behavior in demos and tests to avoid excessive open Matplotlib figure warnings.

* Restored backward-compatible post-estimation exports after adding the graphics layer, including:

  * `confint`;
  * `fitted_values`;
  * `residuals`;
  * `predict`;
  * `vcov`;
  * `lincom`;
  * `wald_test`;
  * `marginal_effects`.

### Validation

* Added automated tests for SGM-Viz v2 figure generation and file export.

* Added automated tests for result-level plotting accessors.

* Added automated tests for the standard post-estimation gallery.

* Validated SGM-Viz v2 on the CMAPSS FD001 workflow as an external real-data visualization case.

* Validated one-command report export and HTML gallery generation.

* Validated PNG, SVG, and PDF-compatible figure export paths.

### Documentation

* Rewrote README for `0.5.10`.

* Added examples for plotting individual figures.

* Added examples for full standard post-estimation galleries.

* Added examples for SGM-Viz diagnostic dashboards.

* Added examples for one-command SGM-Viz report export.

* Added examples for model-comparison dashboards.

* Added documentation for report modes:

  * `dashboard`;
  * `publication`;
  * `full`.

* Expanded dynamic GMM instrumentation guidance for endogenous, predetermined, and exogenous variables.

* Documented recommended dynamic GMM reporting fields, including instrument architecture and model-health dashboard outputs.

---

## 0.5.9

### Added

* Added public OLS specification and estimation support through `OLSSpec` and `run_ols()`.

* Added public pooled OLS specification and estimation support through `PooledOLSSpec` and `run_pooled_ols()`.

* Added public post-estimation utilities:

  * `predict()`;
  * `fitted_values()`;
  * `residuals()`;
  * `vcov()`;
  * `confint()`;
  * `lincom()`;
  * `wald_test()`;
  * `marginal_effects()`.

* Added confidence-interval support to the public post-estimation API.

* Added linear-combination support comparable to Stata `lincom`.

* Added Wald-test support for linear restrictions.

* Added marginal-effects support for linear estimators.

* Added clearer public API coverage for baseline linear modelling workflows.

* Added documentation distinguishing lagged regressors in the structural equation from lagged values used as GMM instruments.

### Changed

* Expanded the public modelling workflow beyond dynamic GMM to include baseline OLS and pooled OLS models.

* Improved consistency between OLS, pooled OLS, panel estimators, and post-estimation result handling.

* Clarified that lagged variables entering the model equation must be created by users as data columns before estimation.

* Clarified that `gmm_lags=(a, b)` controls instrument lag windows, not structural lag creation.

### Fixed

* Improved backward-compatible exports for public post-estimation functions.

* Improved result normalization for OLS and pooled OLS workflows.

* Tightened documentation around safe dynamic-panel modelling practice.

### Validation

* Verified OLS and pooled OLS against Stata on the maintained FD001 benchmark.

* Confirmed machine-precision agreement for maintained OLS benchmark coefficients and standard errors.

* Maintained existing System GMM, Difference GMM, Windmeijer, Hansen, Sargan, AR(1), and AR(2) parity claims under the repository benchmark workflows.

### Documentation

* Added OLS and pooled OLS quick-start examples.

* Added post-estimation usage examples.

* Added explicit explanation of structural lags versus instrument lags.

* Added modelling guidance for endogenous, predetermined, and exogenous classifications.

---

## 0.5.8

### Added

* Expanded Stata parity workflow coverage for the maintained panel-econometrics certification suite.

* Added broader certification reporting for static and dynamic estimators.

* Added additional parity artifacts for System GMM and Difference GMM workflows.

* Added improved comparison workflows for coefficient estimates, standard errors, diagnostic statistics, and sample metadata.

### Changed

* Consolidated parity language to distinguish strict parity, comparison parity, and external validation.

* Improved certification-report structure for reviewer-facing documentation.

* Improved workflow separation between package validation scripts and publication-case validation scripts.

### Fixed

* Tightened benchmark output paths and artifact organization.

* Reduced ambiguity in parity status labels.

* Improved handling of dynamic-GMM benchmark metadata.

### Validation

* Confirmed maintained estimator paths across static and dynamic panel workflows.

* Confirmed System GMM and Difference GMM parity paths under maintained `xtabond2` workflows.

* Confirmed continued alignment of Windmeijer-corrected two-step standard errors under the maintained benchmark specifications.

### Documentation

* Updated validation language around benchmark-specific claims.

* Clarified that parity claims apply to maintained benchmark specifications and should not be generalized mechanically to all possible user specifications.

---

## 0.5.7

### Added

* Added external CMAPSS FD001 validation workflows for publication-style System GMM applications.

* Added FD001 risk-model validation workflow.

* Added FD001 degradation-index validation workflow.

* Added export workflows integrating `systemgmmkit` results with `universal-output-hub`.

* Added generated Stata comparison scripts for FD001 validation.

* Added FD001 model-output tables for coefficients, standard errors, diagnostics, and reporting artifacts.

### Changed

* Strengthened package validation beyond synthetic and controlled benchmark data by adding an external real-data application.

* Improved FD001 workflow organization across preparation, estimation, comparison, and reporting scripts.

* Improved result export compatibility with publication-table workflows.

### Fixed

* Improved FD001 model-run reproducibility.

* Improved handling of coefficient and diagnostic comparison files.

* Improved workflow robustness for local editable installs and external package integration.

### Validation

* Validated System GMM on CMAPSS FD001 risk and degradation specifications.

* Compared FD001 `systemgmmkit` outputs against Stata `xtabond2` reference outputs.

* Confirmed coefficient, standard-error, sample-size, instrument-count, Hansen, Sargan, AR(1), and AR(2) diagnostics within declared external-validation tolerance.

### Documentation

* Added FD001 validation references to package-level validation guidance.

* Clarified that the controlled `xtabond2` benchmark remains the strict certification benchmark, while FD001 is an external application validation case.

---

## 0.5.6

### Added

* Added expanded public estimator exports for panel workflows.

* Added additional parity and smoke-test workflows for static panel estimators.

* Added package import checks to detect local-version and installed-version mismatches.

* Added additional support for documentation and README consistency checks.

### Changed

* Improved public API consistency across fixed effects, random effects, panel IV, Difference GMM, and System GMM.

* Improved packaging metadata consistency.

* Improved local-development validation steps before release.

### Fixed

* Fixed version mismatch issues between runtime `__version__` and installed package metadata.

* Fixed incomplete public exports for selected estimators.

* Improved import stability for editable installations.

### Documentation

* Updated quick-start coverage for the public estimator API.

* Added clearer local-development verification commands.

---

## 0.5.5

### Added

* Added additional dynamic-GMM conformance checks.

* Added expanded parity scripts for maintained System GMM specifications.

* Added additional diagnostic comparison artifacts.

* Added improved support for collapsed-instrument benchmark validation.

### Changed

* Improved dynamic-GMM benchmark reproducibility.

* Improved naming consistency for parity specifications.

* Improved comparison of native outputs against Stata reference outputs.

### Fixed

* Corrected benchmark specification naming inconsistencies.

* Tightened instrument-count and diagnostic comparison logic.

* Improved output-path consistency for parity artifacts.

### Validation

* Expanded maintained System GMM benchmark evidence.

* Improved confidence in coefficient, standard-error, and diagnostic alignment under maintained specifications.

---

## 0.5.4

### Added

* Added FOD Difference GMM parity certification against Stata `xtdpdgmm model(fodev)`.

* Certified numerical point-estimate parity for maintained collapsed FOD Difference GMM specifications.

* Added near Windmeijer standard-error parity for endogenous and predetermined timing specifications, with maximum absolute standard-error gap below `1e-2` on the maintained oracle set.

* Added dedicated FOD Difference GMM parity scripts and comparison artifacts under the `xtdpdgmm` parity workflow.

* Added regression tests for FOD Difference GMM coefficient parity and Windmeijer standard-error near-parity.

### Fixed

* Corrected FOD transformed-equation row construction so FOD no longer inherits the first-difference two-period burn-in rule.

* Corrected FOD IV-style instrument semantics to use current level values in transformed equations, matching `xtdpdgmm model(fodev)` behavior.

* Added a dedicated FOD Difference GMM Windmeijer-style covariance correction.

* Preserved numerical coefficient parity while improving FOD two-step Windmeijer standard-error alignment.

### Documentation

* Added a FOD Difference GMM `xtdpdgmm` certification report.

* Added documented follow-up tickets for exact Windmeijer standard-error parity, diagnostic parity, and broader FOD oracle expansion.

* Clarified that FOD Difference GMM has coefficient-level parity and near Windmeijer-SE parity, not full exact diagnostic parity.

---

## 0.5.3

### Added

* Added additional dynamic-panel GMM parity scaffolding.

* Added improved native System GMM benchmark workflows.

* Added additional scripts for comparing native GMM output against Stata reference output.

* Added improved diagnostic reporting for native GMM development.

### Changed

* Improved internal dynamic-GMM result normalization.

* Improved native GMM benchmark artifact organization.

* Improved separation between development diagnostics and public package outputs.

### Fixed

* Fixed selected native GMM transformation and stacking issues discovered during parity development.

* Fixed inconsistencies in benchmark comparison outputs.

* Improved numerical stability in maintained dynamic-GMM comparison workflows.

### Documentation

* Updated parity-roadmap documentation for native dynamic-GMM development.

* Clarified remaining certification requirements before full native parity claims.

---

## 0.5.2

### Added

* Added additional native dynamic-GMM implementation refinements.

* Added improved matrix-construction diagnostics for System GMM development.

* Added parity investigation scripts for instrument stacking, weighting, and covariance behavior.

* Added expanded comparison artifacts for native versus Stata GMM outputs.

### Fixed

* Corrected selected instrument-stacking and weighting inconsistencies.

* Improved alignment of native System GMM matrix construction with Stata benchmark expectations.

* Improved handling of benchmark data ordering and transformed-equation construction.

### Documentation

* Added development notes around GMM weighting, instrument matrices, and benchmark interpretation.

* Improved roadmap language for native System GMM parity certification.

---

## 0.5.1

### Added

* Added maintained native System GMM `xtabond2` parity benchmark workflow.

* Added comparison artifacts for coefficients, Windmeijer standard errors, Hansen diagnostics, Sargan diagnostics, and AR diagnostics.

* Added certification reporting for the maintained collapsed two-step System GMM benchmark.

* Added stricter benchmark comparison tolerances for maintained parity specifications.

### Changed

* Improved public validation language for System GMM parity.

* Clarified that parity claims apply to maintained benchmark specifications.

* Improved benchmark artifact naming and output organization.

### Fixed

* Fixed System GMM benchmark alignment issues.

* Improved handling of signed AR diagnostic statistics.

* Improved consistency between native diagnostic output and Stata reference output.

### Validation

* Certified native System GMM against Stata `xtabond2` under the maintained collapsed two-step Windmeijer benchmark.

* Confirmed coefficient, standard-error, Hansen, Sargan, AR(1), and AR(2) parity under the maintained benchmark specification.

---

## 0.5.0

### Added

* Added native Windmeijer-corrected two-step covariance support for native dynamic-panel GMM.

* Certified native System GMM Windmeijer standard errors against Stata `xtabond2` `e(V)` on the current collapsed two-step benchmark.

* Preserved the uncorrected two-step clustered covariance benchmark path through an explicit environment toggle.

### Fixed

* Cleaned tracked parity and debug artifacts so Ruff and CI validate only intended package, test, and benchmark files.

* Updated README validation wording to document Windmeijer parity certification while keeping Stata-equivalence claims benchmark-specific.

---

## 0.4.1

### Added

* Added a structured `PydynpdGMMResult` adapter for `pydynpd` backend runs.

* Added package-level NumPy compatibility shim for older `pydynpd` releases.

* Added `pydynpd` backend tests using a mocked backend.

### Fixed

* Grouped IV-style variables into a single `pydynpd` `iv(...)` block.

---

## 0.4.0

### Added

* Added native one-way Random Effects estimation.

* Added native Panel IV / 2SLS estimation with optional entity and time effects.

* Added regression-table export to Markdown, CSV, and LaTeX.

* Added Stata parity do-file template generation for fixed effects and dynamic-panel GMM workflows.

* Added an experimental native one-step Difference/System GMM engine for validation and development workflows.

### Documentation

* Kept `pydynpd` as the recommended production backend for Difference/System GMM until native parity tests are documented.

---

## 0.3.0

### Changed

* Generalized package scope to domain-neutral panel-data workflows.

* Removed domain-specific examples and presets from the package core.

* Updated tests to use neutral panel-data variables and model examples.

### Added

* Added generic builders for fixed effects, Difference GMM, System GMM, and FE plus GMM model suites.

* Added a generic CLI for panel validation and dynamic-panel GMM model-card generation.

---

## 0.2.0

### Added

* Added native fixed-effects estimation.

* Added one-way and two-way fixed-effects support.

* Added clustered, robust, and unadjusted covariance options.

* Added FE plus dynamic GMM suite support.

* Added production repository scaffolding.

---

## 0.1.0

### Added

* Added dynamic-panel specification objects.

* Added `pydynpd` command construction.

* Added panel validation, diagnostic assessment, and model-card reporting.
