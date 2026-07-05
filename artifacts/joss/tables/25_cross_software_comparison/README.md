# Artifact 25: Cross-Software Comparison

## Purpose

This artifact positions systemgmmkit against related Python, R, and Stata tools.

It is not intended to claim that systemgmmkit is the first dynamic-panel GMM implementation. Instead, the comparison documents systemgmmkit's workflow contribution: estimation, diagnostics, post-estimation, validation artifacts, visualization, forecasting, and publication-oriented reporting in one Python package.

## Comparator groups

Python:
- pydynpd
- statsmodels
- linearmodels

R:
- plm::pgmm
- pdynmc

Stata:
- xtabond2
- xtdpdgmm

## Interpretation

Stata xtabond2 and xtdpdgmm remain the primary numerical parity references.

Python and R tools are used for ecosystem positioning and, where feasible, additional numerical comparison. Because dynamic-panel GMM implementations differ in instrument construction, sample trimming, finite-sample correction, covariance scaling, and default equation-scope conventions, cross-software comparison should not be interpreted as automatic strict parity unless the benchmark specification is explicitly aligned.

## systemgmmkit positioning

systemgmmkit's contribution is not estimator availability alone. Its contribution is the integration of:

- dynamic-panel GMM estimation
- panel/static baseline estimators
- diagnostics
- Stata-style post-estimation
- validation artifacts
- visualization
- forecasting
- publication-oriented output workflows
