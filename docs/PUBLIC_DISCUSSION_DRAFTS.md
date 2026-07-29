# Public Discussion Drafts

These drafts are ready to post as GitHub Discussions. They are written to create a
public development trail around roadmap decisions, validation evidence, and adoption.

## Discussion 1: System GMM validation roadmap after native Windmeijer parity

Category: Ideas

Labels: `roadmap`, `validation`

Body:

`systemgmmkit` now has benchmark-specific System GMM certification against maintained
Stata `xtabond2` artifacts for several controlled specifications, including native
Windmeijer-corrected two-step covariance.

This thread is for public discussion of the next validation slices. Current candidates
include:

- unbalanced-panel System GMM parity;
- missing-data behavior;
- alternative lag-window designs;
- alternative instrument-classification examples;
- reviewer-facing evidence tables for the software paper;
- additional public datasets suitable for replication examples.

Parity statements should stay specific to the tested data, scripts, covariance target,
diagnostics, and tolerances. The package should not make a universal Stata-equivalence
claim.

## Discussion 2: Prediction, ML workflow, and reporting layer

Category: Ideas

Labels: `prediction`, `reporting`, `ml-workflow`

Body:

One distinctive part of `systemgmmkit` is the layer around estimation: prediction,
diagnostics, ML-style workflow helpers, visual summaries, and reproducible reporting.

This thread is for discussion of what should come next in that layer. Useful proposals
should specify:

- the applied workflow being improved;
- what the user should be able to inspect or export;
- how the output should connect to fitted GMM results and diagnostics;
- whether the feature is descriptive, predictive, inferential, or reporting-only;
- tests or examples needed to avoid overstating the estimator.

The goal is to make dynamic-panel results easier to review, replicate, and communicate
without hiding model assumptions.

## Discussion 3: Adoption, teaching, and replication examples

Category: Show and tell

Labels: `adoption`

Body:

This thread records public uses of `systemgmmkit` in applied work, teaching, replication
packages, technical reports, and examples.

Helpful notes include:

- which estimator or workflow was used;
- whether the use was exploratory, teaching, replication, or publication support;
- links to public notebooks, repositories, papers, or course material;
- diagnostics, reporting, or validation features that were useful;
- limitations encountered in applied use.

This adoption record helps the project document real use beyond internal development and
prioritize future work.

