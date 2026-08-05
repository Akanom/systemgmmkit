from __future__ import annotations

import pytest

from scripts.check_coverage import CoverageDataError, check_coverage, coverage_metrics


def _report(
    *,
    project_lines: tuple[int, int] = (720, 1000),
    project_branches: tuple[int, int] = (530, 1000),
    dynamic_lines: tuple[int, int] = (101, 101),
    dynamic_branches: tuple[int, int] = (32, 32),
    windows_path: bool = False,
) -> dict[str, object]:
    path = (
        "src\\systemgmmkit\\dynamic_panel.py"
        if windows_path
        else ("src/systemgmmkit/dynamic_panel.py")
    )
    return {
        "totals": {
            "covered_lines": project_lines[0],
            "num_statements": project_lines[1],
            "covered_branches": project_branches[0],
            "num_branches": project_branches[1],
        },
        "files": {
            path: {
                "summary": {
                    "covered_lines": dynamic_lines[0],
                    "num_statements": dynamic_lines[1],
                    "covered_branches": dynamic_branches[0],
                    "num_branches": dynamic_branches[1],
                }
            }
        },
    }


@pytest.mark.parametrize("windows_path", [False, True])
def test_coverage_ratchets_accept_posix_and_windows_report_paths(windows_path: bool) -> None:
    report = _report(windows_path=windows_path)

    metrics = coverage_metrics(report)

    assert check_coverage(report) == ()
    assert [metric.percent for metric in metrics] == [72.0, 53.0, 100.0, 100.0]


def test_coverage_ratchets_report_project_and_targeted_regressions() -> None:
    report = _report(
        project_lines=(719, 1000),
        project_branches=(529, 1000),
        dynamic_lines=(100, 101),
        dynamic_branches=(31, 32),
    )

    failures = check_coverage(report)

    assert [failure.label for failure in failures] == [
        "project statements",
        "project branches",
        "dynamic_panel.py statements",
        "dynamic_panel.py branches",
    ]


@pytest.mark.parametrize(
    ("report", "message"),
    [
        ({}, "no totals mapping"),
        ({"totals": {}}, "no files mapping"),
        (_report(dynamic_branches=(0, 0)), "has no measurable items"),
        (_report(project_lines=(1001, 1000)), "covered items out of"),
    ],
)
def test_coverage_ratchets_reject_incomplete_or_invalid_reports(
    report: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(CoverageDataError, match=message):
        coverage_metrics(report)
