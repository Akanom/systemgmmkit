# Release Integrity

The security and build jobs call `Akanom/python-package-governance` at immutable
commit `09d19a220bdcbd2355c8cc1006def5e913dd4462`; dependency updates must review
and deliberately advance that SHA.

Every release must:

1. originate from a reviewed GitHub release tag matching `pyproject.toml`;
2. pass the supported-Python, minimum-dependency, audit, and build jobs;
3. build wheel and sdist once in the unprivileged build job;
4. pass strict Twine checks and `scripts/inspect_dist.py`;
5. install the wheel with `--only-binary=:all:` and test the sdist separately;
6. produce an artifact inventory, CycloneDX SBOM, and provenance attestation;
7. publish unchanged artifacts through PyPI Trusted Publishing;
8. use protected-environment approval for the `pypi` environment; and
9. verify and smoke-test the package downloaded from PyPI after publication.

The final post-publication verification is an operator step until a separate
post-release workflow is introduced. Record the source commit, workflow run,
artifact hashes, PyPI URL, and smoke-test result in the release notes.
