# Changelog

## 0.5.3

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

## 0.5.0

### Added

* Added native Windmeijer-corrected two-step covariance support for native dynamic-panel GMM.
* Certified native System GMM Windmeijer standard errors against Stata `xtabond2` `e(V)` on the current collapsed two-step benchmark.
* Preserved the uncorrected two-step clustered covariance benchmark path through an explicit environment toggle.

### Fixed

* Cleaned tracked parity and debug artifacts so Ruff and CI validate only intended package, test, and benchmark files.
* Updated README validation wording to document Windmeijer parity certification while keeping Stata-equivalence claims benchmark-specific.

## 0.4.1

### Added

* Added a structured `PydynpdGMMResult` adapter for `pydynpd` backend runs.
* Added package-level NumPy compatibility shim for older `pydynpd` releases.
* Added `pydynpd` backend tests using a mocked backend.

### Fixed

* Grouped IV-style variables into a single `pydynpd` `iv(...)` block.

## 0.4.0

### Added

* Added native one-way Random Effects estimation.
* Added native Panel IV / 2SLS estimation with optional entity and time effects.
* Added regression-table export to Markdown, CSV, and LaTeX.
* Added Stata parity do-file template generation for fixed effects and dynamic-panel GMM workflows.
* Added an experimental native one-step Difference/System GMM engine for validation and development workflows.

### Documentation

* Kept `pydynpd` as the recommended production backend for Difference/System GMM until native parity tests are documented.

## 0.3.0

### Changed

* Generalized package scope to domain-neutral panel-data workflows.
* Removed domain-specific examples and presets from the package core.
* Updated tests to use neutral panel-data variables and model examples.

### Added

* Added generic builders for fixed effects, Difference GMM, System GMM, and FE plus GMM model suites.
* Added a generic CLI for panel validation and dynamic-panel GMM model-card generation.

## 0.2.0

### Added

* Added native fixed-effects estimation.
* Added one-way and two-way fixed-effects support.
* Added clustered, robust, and unadjusted covariance options.
* Added FE plus dynamic GMM suite support.
* Added production repository scaffolding.

## 0.1.0

### Added

* Added dynamic-panel specification objects.
* Added `pydynpd` command construction.
* Added panel validation, diagnostic assessment, and model-card reporting.
