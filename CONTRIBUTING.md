# Contributing

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev,all]"
```

## Quality gate

Before opening a pull request, run:

```bash
ruff check .
ruff format --check .
pytest
python -m build
```

## Branching model

- `main`: production-ready code only.
- `develop`: integration branch for completed features.
- `feature/<short-name>`: isolated work.
- `fix/<short-name>`: bug fixes.
- `release/vX.Y.Z`: release preparation.

## Definition of Done

A change is done only when it is implemented, tested, documented, lint-clean, and merged through a pull request.
