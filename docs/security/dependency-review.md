# Dependency Review

Review date: 2026-07-21

Owner: Maintainer

Reassessment: every dependency change and at least quarterly

## Runtime dependencies

| Package | Purpose | Decision |
|---|---|---|
| NumPy | Numerical arrays and linear algebra | Mandatory; `>=1.23,<3` |
| pandas | Panel-data indexing and tabular results | Mandatory; `>=1.5,<4` |
| SciPy | Optimization, distributions, and matrix routines | Mandatory; `>=1.9,<2` |
| Matplotlib | Post-estimation graphics | Moved to the optional `plots` extra |

Optional backends (`pydynpd`, `linearmodels`, `tabulate`, and Matplotlib) are
bounded, independently installable, and excluded from core import requirements.

## NumPy 2.5.1 source-archive alert

Alert: obfuscated or opaque archive

Artifact: `numpy-2.5.1.tar.gz`

Official PyPI SHA-256:
`a48a113e6afea91f5608793bafa7ef2ad481fefbda87ec5069f483de61cb9fa3`

Disposition: `MONITOR` pending comparison with the Socket.dev artifact hash

The official PyPI archive hash was verified. Its five nested compressed paths
are vendored Meson test fixtures: two are six-byte `dummy` invalid-archive
fixtures and three contain only small Meson/Rust test sources. No executable
payload was found. An OSV-backed `pip-audit` of the resolved runtime graph found
no known vulnerability. This evidence supports a scanner heuristic, but a
version-specific suppression must not be applied until Socket's exact artifact
hash matches the official hash.

## Expected capabilities

Native code in NumPy, pandas, and SciPy is expected. Subprocess use occurs in
development/parity scripts and tests, not in the installed core runtime.
Package import does not require network or shell access.
