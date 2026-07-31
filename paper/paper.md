---
title: 'systemgmmkit: Panel-data and dynamic-GMM workflows in Python'
tags:
  - Python
  - econometrics
  - panel data
  - dynamic panel GMM
  - generalized method of moments
  - post-estimation
  - forecasting
authors:
  - name: Oluwajuwon Mayomi Akanbi
    affiliation: 1
affiliations:
  - name: Independent Researcher / Developer
    index: 1
date: 11 July 2026
bibliography: paper.bib
---

# Summary

`systemgmmkit` is a Python package for panel-data and dynamic-panel econometric workflows. It provides a unified interface for ordinary least squares, pooled OLS, compact within-transformation fixed effects, random effects, instrumental-variable / 2SLS estimation, Difference GMM, and System GMM. The package also includes post-estimation tools, diagnostics, panel-aware prediction and forecasting utilities, visualization helpers, and reproducible validation artifacts.

The package is designed for researchers and applied analysts who need panel-data workflows in Python while keeping diagnostics and comparison evidence visible. It does not claim a new econometric estimator. The contribution is the workflow around estimation, diagnostics, interpretation, validation, and reporting.

# Statement of Need

Panel-data and dynamic-panel models are widely used in economics, finance, management, political economy, development studies, and operational research [@arellano1991some; @blundell1998initial; @bond2002dynamic]. Applied researchers often need more than an estimator call: they need data preparation, diagnostics, post-estimation, forecasting, model comparison, and reproducible evidence that results are consistent with known reference implementations.

`systemgmmkit` addresses this need by integrating static panel estimators, instrumental-variable estimation, dynamic-panel GMM, Stata-style post-estimation, panel-aware prediction workflows, visualization, and validation artifacts in one Python package. The target users are applied researchers, instructors, and analysts who want Python-based workflows without losing sight of the econometric assumptions and diagnostic checks.

# State of the Field

Dynamic-panel GMM is a mature method for panels with lagged dependent variables, persistence, unobserved heterogeneity, and endogenous or predetermined regressors. Stata commands such as `xtabond2` and `xtdpdgmm` are common applied reference points [@roodman2009xtabond2]. R packages such as `plm` provide panel-data and GMM functionality [@croissant2008panel], while Python packages such as `statsmodels`, `linearmodels`, and `pydynpd` cover other parts of the same econometric work [@seabold2010statsmodels; @sheppard2024linearmodels; @pydynpd].

`systemgmmkit` is not presented as a replacement for these tools. The reason for a separate package is the connected workflow: static panel models, IV estimation, Difference GMM, System GMM, diagnostics, post-estimation, panel/time-aware prediction utilities, visualization, and reproducible comparison artifacts are exposed through one Python interface. Static fixed-effects slopes are estimated with a native within-transformation backend, while least-squares dummy-variable construction remains an internal audit reference for slope-equivalence checks. Strict numerical parity is claimed only for aligned reference specifications where estimator definitions, instrument construction, covariance choices, and sample handling are controlled. Reference checks are package-scoped and are not used to rank unrelated software.

# Software Design

`systemgmmkit` is designed around explicit model specifications, estimator runners, and structured result objects. Convenience wrappers are available, but they compose the same lower-level APIs used in validation. This keeps common workflows short while making econometric choices such as lag windows, instrument roles, transformations, covariance options, and diagnostic metadata visible.

This matters most for dynamic-panel GMM, where small changes in instrument construction, sample trimming, finite-sample corrections, or equation scope can change results. The package therefore treats validation, diagnostics, and post-estimation as part of the workflow, not as material users have to reconstruct after estimation. Result objects expose coefficients, covariance matrices, fitted values, residuals, diagnostic tests, and metadata in a consistent form across estimator families.

The package also balances native Python implementation with aligned reference checks. Native estimators and utilities provide reproducible Python workflows, while validation artifacts compare selected `systemgmmkit` specifications against established Stata, R, and Python references where the estimand is controlled. The point is not to pretend that software implementations are identical, but to make the package's claim boundary visible enough to check.

# Package Validation and Aligned Reference Checks

The validation suite is organized as reproducible repository artifacts. The current
formal System GMM evidence is the machine-readable registry and unified certificate
under `artifacts/parity/xtabond2/`. They report benchmark-specific
`PASS_XTABOND2_PARITY` for complete parameter sets, Windmeijer-corrected two-step
standard errors, exact counts, Hansen/Sargan values, and signed AR diagnostics.
This status denotes numerical agreement, not instrument validity or specification
endorsement. Artifact 24 is retained as a frozen linked snapshot and is not an
independent authority.

| Evidence | Scope | Comparison role |
|---|---|---|
| Artifact 22 | Controlled Difference/System GMM | Auxiliary Stata comparison |
| Registry + unified certificate | Maintained four-spec System GMM certificate | Formal `xtabond2` numerical-agreement evidence |
| Artifact 24 | Frozen single-spec snapshot | Historical linked provenance only |
| Artifacts 26--27 | Static, panel, IV, and post-estimation checks | `statsmodels`, `linearmodels`, R, and Stata comparisons |
| Artifact 28 | Performance benchmarks | Practical runtime evidence |

Additional artifacts document controlled dynamic-GMM comparisons, static estimator validation, post-estimation checks, and package-aligned reference checks against Python, R, and Stata implementations. OLS, pooled OLS, fixed effects, random effects, and 2SLS are compared under aligned specifications. The native fixed-effects runtime reports `native-within`; fixed-effects validation checks slope agreement against maintained reference paths rather than treating dummy-variable coefficients as public model output. Auxiliary R/Python dynamic-GMM notes remain outside formal parity claims because defaults, instrument matrices, finite-sample corrections, and covariance scaling differ across implementations.


# Post-Estimation, ML Workflow, and Visualization Layers

Beyond estimation, `systemgmmkit` includes Stata-style post-estimation utilities for variance-covariance extraction, confidence intervals, prediction, fitted values, residuals, linear combinations, Wald tests, marginal effects, and margins. The panel-aware workflow tools add regression metrics, temporally ordered train/test splitting, expanding-window validation, model comparison, forecasting/backtesting helpers, and dynamic-GMM specification search [@bergmeir2018note; @cerqueira2019evaluating; @roberts2017crossvalidation].

A distinctive workflow contribution is the diagnostic-first dynamic-GMM search layer. `GMMGridSearch`, `DynamicGMMHybridSearch`, and `auto_dynamic_gmm` organize candidate Difference GMM and System GMM specifications over lag windows, collapse choices, estimation steps, transformations, and diagnostic rules. Unlike generic hyperparameter search, this layer filters candidates with unsafe AR(2), Hansen, convergence, or instrument-proliferation diagnostics before model ranking. The layer does not introduce a new estimator; it repeatedly calls validated estimators and organizes specification exploration, diagnostic filtering, forecasting-oriented assessment, and report generation.

The visualization layer supports coefficient, marginal-effect, margins, residual, fixed-effect, instrument, Hansen/AR diagnostic, model-health, counterfactual, response-surface, and dynamic-persistence plots. These outputs are intended to support empirical interpretation and publication-oriented reporting.

# Research Impact Statement

`systemgmmkit` supports research workflows where panel-data estimation, dynamic-GMM diagnostics, validation, and reporting need to be inspected together. The current evidence is the validation workflow itself: reproducible package-scoped checks, diagnostics, benchmarks, and artifacts that let reviewers inspect what the package is doing. The repository compares selected `systemgmmkit` estimators against established Stata, R, and Python references, with strict parity claims limited to aligned benchmark specifications.

Performance artifacts show that static, panel, IV, and dynamic-GMM workflows complete successfully on the tested panel sizes. Fixed-effects benchmarks now use the compact native `native-within` backend for ordinary one-way and two-way fixed-effects slope estimation; the optional `linearmodels` backend remains useful when users need the upstream `PanelOLS` result object or additional backend-specific features. These benchmarks are presented as reproducibility-oriented evidence, not hardware-independent speed claims.

The package is most useful for applied researchers who want Python workflows while retaining reviewer-facing evidence for models often checked against Stata or R. The validation artifacts, diagnostic outputs, benchmarks, and panel-aware forecasting utilities reduce the work needed to verify model behavior, compare specifications, and report assumptions.

# Availability and Reproducibility

The source repository is available at `https://github.com/Akanom/systemgmmkit`.

Full validation evidence is included in repository files. Dynamic-GMM parity certificates and maintained Stata-oriented comparison outputs are stored under `artifacts/parity/`. The broader JOSS validation bundle is stored under `artifacts/joss/`, with artifact indexes in `artifacts/joss/README.md` and `artifacts/joss/joss_artifact_file_index.csv`. These artifacts let reviewers inspect both the package interface and the checks behind the claims.

# AI Usage Disclosure

Generative AI tools, including OpenAI ChatGPT, were used to assist with software development workflow planning, code review support, validation-script drafting, artifact summarization, and manuscript drafting/editing. AI assistance was used for code scaffolding, documentation wording, PowerShell workflow generation, and paper-section drafting.

All AI-assisted content was reviewed, modified, and validated by the author. The author made the primary design, architectural, econometric, validation, and interpretation decisions, executed the software and comparison workflows, inspected the generated artifacts, and remains responsible for the accuracy, originality, licensing compliance, and ethical/legal compliance of the submitted work.

# Acknowledgements

The development of `systemgmmkit` benefited from comparisons with established econometric tools in Python, R, and Stata, including `statsmodels`, `linearmodels`, `plm`, `pydynpd`, `xtabond2`, and `xtdpdgmm`.

# References
