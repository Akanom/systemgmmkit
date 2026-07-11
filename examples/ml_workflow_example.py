"""Compatibility entry point for the full ML workflow example.

Run:
    python examples/ml_workflow_example.py

The full example is kept in ``07_ml_forecast_search_workflow.py`` so the
numbered examples read like a user guide, while this older filename still works.
"""

from __future__ import annotations

import runpy
from pathlib import Path


def main() -> None:
    runpy.run_path(
        str(Path(__file__).with_name("07_ml_forecast_search_workflow.py")),
        run_name="__main__",
    )


if __name__ == "__main__":
    main()
