# Artifact 25: Archived External-Reference Notes

## Purpose

This artifact records auxiliary outputs from related Python, R, and Stata tools.

It is not intended to claim that systemgmmkit is the first dynamic-panel GMM implementation, rank software, or host a repository-wide package comparison workflow. Instead, these notes document why formal `systemgmmkit` parity claims are limited to aligned package validation artifacts.

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

Python and R outputs are retained as auxiliary external-reference notes. Because dynamic-panel GMM implementations differ in instrument construction, sample trimming, finite-sample correction, covariance scaling, and default equation-scope conventions, these notes should not be interpreted as strict parity unless the benchmark specification is explicitly aligned.

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
