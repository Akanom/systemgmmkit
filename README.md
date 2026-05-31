# systemgmmkit

`systemgmmkit` is a generic Python workflow package for panel-data econometrics.

It supports reusable model specification, panel validation, fixed-effects estimation, Difference GMM and System GMM command construction, diagnostics interpretation, and reproducible model reporting.

The package is designed for applied panel-data projects in economics, finance, management, operations, productivity analysis, political economy, industrial organization, firm-level research, country panels, regional panels, household panels, and other longitudinal-data settings.

## Core capabilities

- Validate balanced and unbalanced panel datasets before estimation.
- Estimate static panel models using the native backend.
- Build pooled OLS-style models.
- Build one-way fixed-effects models.
- Build two-way fixed-effects models.
- Build Arellano-Bond Difference GMM specifications.
- Build Blundell-Bond System GMM specifications.
- Configure collapsed instruments and restricted lag windows.
- Classify regressors as endogenous, predetermined, or exogenous.
- Generate model-card style reporting for reproducibility.
- Run dynamic-panel GMM through the optional pydynpd backend when installed.

## Stata-alignment policy

The package should be treated as Stata-aligned, not automatically Stata-identical.

Results can align with Stata xtreg, fe and xtabond2 only when the same sample, transformation, lag windows, instrument matrix, collapsed-instrument setting, time dummies, covariance assumptions, and finite-sample corrections are used.

Exact Stata parity should be verified using dedicated replication tests.

## Installation

Development installation:

python -m pip install -e ".[dev,all]"

Runtime installation:

python -m pip install -e ".[all]"

## Generic fixed-effects workflow

Use build_fixed_effects_spec to define a static panel model, then run_fixed_effects to estimate it with entity effects, time effects, or both.

## Generic dynamic-panel GMM workflow

Use build_system_gmm_spec for System GMM and build_difference_gmm_spec for Difference GMM. Use build_pydynpd_command to generate a backend command for pydynpd.

## FE plus dynamic GMM suite

Use build_panel_model_suite to pair a fixed-effects model with a dynamic-panel GMM robustness specification.

## CLI examples

Validate a panel dataset:

systemgmmkit validate data.csv --entity firm_id --time year --vars y x1 x2

Print a generic System GMM model card:

systemgmmkit spec --dependent y --regressors x1 x2 --endogenous x1 --predetermined x2 --exogenous control1 control2

Print a Difference GMM model card:

systemgmmkit spec --dependent y --regressors x1 x2 --endogenous x1 --difference

## Current production status

Version 0.3.0 is a generic panel-data workflow package. Native fixed-effects estimation is included. Difference GMM and System GMM estimation delegate to pydynpd when installed.

Future milestones:

- Random Effects wrapper.
- Panel IV and 2SLS wrapper.
- Native System GMM engine.
- Windmeijer-corrected native robust standard errors.
- Stata parity tests against xtreg, fe and xtabond2.
- More export formats for regression tables.
