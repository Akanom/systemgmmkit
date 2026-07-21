# Security Policy

## Supported versions

Security fixes are provided for the latest released minor version and the
current `main` branch. Supported releases run on Python 3.9–3.12. Older package
versions and unsupported Python versions may not receive fixes.

## Reporting a vulnerability

Use GitHub's private security-advisory form for this repository. Do not place
exploit details, credentials, private data, or unpublished research material in
a public issue. Include the affected version or commit, impact, reproduction
steps, and any suggested mitigation.

The maintainer aims to acknowledge reports within five business days and to
provide an initial status update within ten business days. Remediation timing
depends on severity, exploitability, and coordinated-disclosure needs.

## Disclosure and dependency policy

Coordinated disclosure is preferred. Confirmed critical and high
vulnerabilities block release unless a documented, owner-approved,
time-bounded exception exists. Behavioural and heuristic scanner alerts are
reviewed at package, version, artifact, and file level and are not treated as
confirmed vulnerabilities without corroborating evidence.

Runtime dependencies use tested compatibility ranges. CI resolves and audits
the supported graph, validates distributions, performs wheel-only and sdist
installation tests, and generates an SBOM. Dependency exceptions are recorded
in `docs/security/accepted-risks.md` and reassessed on version changes.

## Release integrity

PyPI publication uses GitHub OIDC Trusted Publishing from the protected `pypi`
environment. Release workflows use least-privilege permissions, immutable
action revisions, distribution inspection, and GitHub build-provenance
attestations. Repository administrators must keep the PyPI trusted-publisher
mapping and GitHub environment protection enabled.

This package is research software. Independently validate results before using
them for high-stakes financial, policy, legal, or scientific decisions.
