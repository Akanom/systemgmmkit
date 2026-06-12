# Changelog

## 0.5.0

- Added native Windmeijer-corrected two-step covariance support for native dynamic-panel GMM.
- Certified native System GMM Windmeijer standard errors against Stata `xtabond2` `e(V)` on the current collapsed two-step benchmark.
- Preserved the uncorrected two-step clustered covariance benchmark path through an explicit environment toggle.
- Cleaned tracked parity/debug artifacts so Ruff and CI validate only intended package, test, and benchmark files.
- Updated README validation wording to document Windmeijer parity certification while keeping Stata-equivalence claims benchmark-specific.

## 0.4.1

- Added a structured `PydynpdGMMResult` adapter for pydynpd backend runs.
- Added package-level NumPy compatibility shim for older pydynpd releases.
- Grouped IV-style variables into a single pydynpd `iv(...)` block.
- Added pydynpd backend tests using a mocked backend.

## 0.4.0

- Added native one-way Random Effects estimation.
- Added native Panel IV / 2SLS estimation with optional entity and time effects.
- Added regression-table export to Markdown, CSV, and LaTeX.
- Added Stata parity do-file template generation for fixed effects and dynamic-panel GMM workflows.
- Added an experimental native one-step Difference/System GMM engine for validation and development workflows.
- Kept pydynpd as the recommended production backend for Difference/System GMM until native parity tests are documented.

## 0.3.0

- Generalized package scope to domain-neutral panel-data workflows.
- Added generic builders for fixed effects, Difference GMM, System GMM, and FE plus GMM model suites.
- Removed domain-specific examples and presets from the package core.
- Added a generic CLI for panel validation and dynamic-panel GMM model-card generation.
- Updated tests to use neutral panel-data variables and model examples.

## 0.2.0

- Added native fixed-effects estimation.
- Added one-way and two-way fixed-effects support.
- Added clustered, robust, and unadjusted covariance options.
- Added FE plus dynamic GMM suite support.
- Added production repository scaffolding.

## 0.1.0

- Added dynamic-panel specification objects.
- Added pydynpd command construction.
- Added panel validation, diagnostic assessment, and model-card reporting.
