# N-CMAPSS DS01 Static-Dynamic Smoke Comparison

This artifact reports a static and dynamic model-comparison smoke test using the processed N-CMAPSS DS01 unit-cycle panel.

Dataset structure:
- Entity index: unit
- Time index: cycle
- Dependent variable: risk
- Rows after lag construction: 547
- Units: 6

Models:
1. Static OLS: excludes lagged risk.
2. Dynamic OLS: includes lagged risk.
3. Dynamic fixed effects: includes lagged risk and unit effects.

Purpose:
This artifact validates interoperability between the processed N-CMAPSS panel, systemgmmkit 0.5.11 estimation routines, and universal-output-hub Markdown/LaTeX reporting.

Interpretation boundary:
The table is a workflow smoke artifact, not the formal dynamic-GMM parity benchmark. Because the risk variable is derived from remaining useful life and is mechanically persistent over cycles, dynamic specifications are expected to be dominated by lagged risk.

Generated outputs:
- 21_ncmapss_static_dynamic_raw_results.csv
- 21_ncmapss_static_dynamic_summary.json
- 21_uoh_ncmapss_static_dynamic_comparison.md
- 21_uoh_ncmapss_static_dynamic_comparison.tex
