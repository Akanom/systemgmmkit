# Production Workflow

## Goal

Keep `systemgmmkit` reproducible, testable, and releaseable as a Python econometrics workflow package.

## Local workflow

```bash
git checkout -b feature/<feature-name>
python -m pip install -e ".[dev,all]"
ruff check .
pytest
python -m build
git add .
git commit -m "feat: add <feature-name>"
git push -u origin feature/<feature-name>
```

Open a pull request into `develop`. After review and CI success, merge into `develop`. For release, merge `develop` into `main`, tag the release, and publish through GitHub Releases.

## Release workflow

```bash
git checkout main
git pull origin main
git tag -a v0.2.0 -m "Release v0.2.0"
git push origin v0.2.0
```

Create a GitHub Release from the tag. The `publish.yml` workflow can publish to PyPI when PyPI trusted publishing is configured.

## Production criteria

- CI passes on Python 3.9, 3.10, 3.11, and 3.12.
- Tests cover core specification, validation, diagnostics, FE estimation, and pydynpd command generation.
- README examples run without modification.
- Version number follows semantic versioning.
- No generated data, local notebooks, or private thesis data committed.
