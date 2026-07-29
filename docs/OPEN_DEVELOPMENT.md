# Open Development

`systemgmmkit` is developed in public so estimator design, validation evidence,
reporting workflows, and adoption can be inspected before release.

## Public discussion tracks

Use GitHub Discussions for work that benefits from early public input:

- dynamic-panel GMM specification questions;
- Stata, R, Python, or published benchmark comparisons;
- reporting, prediction, and ML-workflow ideas;
- roadmap priorities for future releases;
- adoption notes from papers, teaching material, replication packages, or external
  projects.

Ready-to-post starter threads are kept in
[Public discussion drafts](PUBLIC_DISCUSSION_DRAFTS.md).

Use GitHub Issues for concrete, actionable work:

- reproducible bugs;
- failing parity or conformance checks;
- documentation gaps;
- scoped feature work;
- release blockers.

## Validation record

New estimator paths or materially different GMM configurations should have a visible
record before they are described as certified. That record should include:

1. the model specification and instrument design;
2. data handling assumptions;
3. diagnostic quantities and covariance target;
4. benchmark scripts or committed artifacts;
5. tolerances and software versions; and
6. documentation describing known boundaries.

## Evidence that helps future review

The most useful public evidence is specific:

- issue threads showing design choices and reviewer questions;
- pull requests that connect code, tests, parity evidence, and documentation;
- discussion posts with public data, hashes, commands, and comparison tables;
- external examples in papers, replication packages, teaching, or applied projects.

Keeping the repository public for a period of time is not enough by itself. The public
record should show active development, scrutiny, and use.
