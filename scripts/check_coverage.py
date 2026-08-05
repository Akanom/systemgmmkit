from __future__ import annotations

import argparse
import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class CoverageDataError(ValueError):
    """Raised when a coverage JSON report is missing required counters."""


@dataclass(frozen=True)
class CoverageMetric:
    label: str
    covered: int
    total: int
    minimum: float

    @property
    def percent(self) -> float:
        return 100.0 * self.covered / self.total

    @property
    def passed(self) -> bool:
        return self.percent >= self.minimum


PROJECT_STATEMENT_MINIMUM = 72.0
PROJECT_BRANCH_MINIMUM = 53.0
DYNAMIC_PANEL_STATEMENT_MINIMUM = 100.0
DYNAMIC_PANEL_BRANCH_MINIMUM = 100.0
DYNAMIC_PANEL_PATH = "src/systemgmmkit/dynamic_panel.py"


def _normalise_path(value: str) -> str:
    return value.replace("\\", "/")


def _counter(summary: Mapping[str, Any], key: str, *, label: str) -> int:
    value = summary.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise CoverageDataError(f"{label} has invalid {key!r}: {value!r}")
    return value


def _metric(
    label: str,
    summary: Mapping[str, Any],
    *,
    covered_key: str,
    total_key: str,
    minimum: float,
) -> CoverageMetric:
    covered = _counter(summary, covered_key, label=label)
    total = _counter(summary, total_key, label=label)
    if total == 0:
        raise CoverageDataError(f"{label} has no measurable items")
    if covered > total:
        raise CoverageDataError(f"{label} reports {covered} covered items out of {total}")
    return CoverageMetric(label=label, covered=covered, total=total, minimum=minimum)


def _required_summary(report: Mapping[str, Any], path: str) -> Mapping[str, Any]:
    files = report.get("files")
    if not isinstance(files, Mapping):
        raise CoverageDataError("coverage report has no files mapping")

    normalised = {_normalise_path(str(key)): value for key, value in files.items()}
    file_report = normalised.get(path)
    if not isinstance(file_report, Mapping):
        raise CoverageDataError(f"coverage report has no entry for {path}")

    summary = file_report.get("summary")
    if not isinstance(summary, Mapping):
        raise CoverageDataError(f"coverage report has no summary for {path}")
    return summary


def coverage_metrics(report: Mapping[str, Any]) -> tuple[CoverageMetric, ...]:
    totals = report.get("totals")
    if not isinstance(totals, Mapping):
        raise CoverageDataError("coverage report has no totals mapping")
    dynamic_panel = _required_summary(report, DYNAMIC_PANEL_PATH)

    return (
        _metric(
            "project statements",
            totals,
            covered_key="covered_lines",
            total_key="num_statements",
            minimum=PROJECT_STATEMENT_MINIMUM,
        ),
        _metric(
            "project branches",
            totals,
            covered_key="covered_branches",
            total_key="num_branches",
            minimum=PROJECT_BRANCH_MINIMUM,
        ),
        _metric(
            "dynamic_panel.py statements",
            dynamic_panel,
            covered_key="covered_lines",
            total_key="num_statements",
            minimum=DYNAMIC_PANEL_STATEMENT_MINIMUM,
        ),
        _metric(
            "dynamic_panel.py branches",
            dynamic_panel,
            covered_key="covered_branches",
            total_key="num_branches",
            minimum=DYNAMIC_PANEL_BRANCH_MINIMUM,
        ),
    )


def check_coverage(report: Mapping[str, Any]) -> tuple[CoverageMetric, ...]:
    return tuple(metric for metric in coverage_metrics(report) if not metric.passed)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Enforce project and dynamic-panel coverage ratchets."
    )
    parser.add_argument("report", type=Path, help="coverage.py JSON report")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    try:
        report = json.loads(args.report.read_text(encoding="utf-8"))
        metrics = coverage_metrics(report)
    except (OSError, json.JSONDecodeError, CoverageDataError) as exc:
        raise SystemExit(f"Coverage report error: {exc}") from exc

    for metric in metrics:
        status = "PASS" if metric.passed else "FAIL"
        print(
            f"{status} {metric.label}: {metric.percent:.2f}% "
            f"({metric.covered}/{metric.total}; minimum {metric.minimum:.2f}%)"
        )

    if any(not metric.passed for metric in metrics):
        return 1

    print("Coverage statement and branch ratchets satisfied.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
