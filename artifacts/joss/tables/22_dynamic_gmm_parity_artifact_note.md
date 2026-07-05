# Controlled Dynamic GMM Parity Artifact

This artifact provides a controlled dynamic-panel benchmark for systemgmmkit's Difference GMM and System GMM workflows.

Dataset:
- Synthetic balanced dynamic panel
- Entity index: id
- Time index: time
- Dependent variable: y
- Units: 120
- Periods: 10

Data-generating process:
y_it = 0.55*y_i,t-1 + 0.35*x_pred_it + 0.25*x_exog_it + alpha_i + tau_t + eps_it

Variable roles:
- Lagged dependent variable: endogenous, GMM-style instruments, lags 2:3
- x_pred: predetermined, GMM-style instruments, lags 2:3
- x_exog: exogenous, IV-style instrument
- Instruments are collapsed
- Estimation uses two-step GMM

Purpose:
This artifact validates the formal dynamic-GMM workflow separately from the N-CMAPSS DS01 smoke workflow. The N-CMAPSS artifact validates data processing and reporting interoperability; this controlled benchmark is designed for Difference/System GMM validation and Stata xtabond2 reference generation.

Generated outputs:
- 22_dynamic_gmm_controlled_panel_summary.json
- 22_dynamic_gmm_controlled_panel_preview.csv
- 22_difference_gmm_results.csv
- 22_system_gmm_results.csv
- 22_dynamic_gmm_health_metrics.csv
- 22_dynamic_gmm_instrument_architecture.csv
- 22_stata_xtabond2_command_reference.txt
- 22_stata_xtabond2_parity_reference.do
- 22_uoh_dynamic_gmm_controlled_comparison.md
- 22_uoh_dynamic_gmm_controlled_comparison.tex

Interpretation boundary:
The Stata do-file is a reference script for external parity execution. Numerical Stata parity should be claimed only after running the exported do-file in Stata and comparing the resulting coefficients, standard errors, diagnostics, and instrument counts.
