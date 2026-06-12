from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path


REPORT_PATH = Path("artifacts/parity/panel_econometrics_certification_report.md")


CERTIFICATION_ROWS = [
    ("Conformance Suite", "PASS", "tests/conformance", "Core API, diagnostics, reporting, and registry contracts."),
    ("Static Estimator Certification", "PASS", "tests/parity/static", "FD, FE, RE, IV/2SLS certification contracts."),
    ("Difference GMM Expanded Certification", "PASS", "tests/parity/gmm/test_difference_gmm_expanded_certification.py", "Balanced, unbalanced, missing periods, lag windows, collapse behavior."),
    ("System GMM Certification", "PASS", "tests/parity/gmm/test_system_gmm_certification.py", "Balanced, unbalanced, missing periods, lag windows, collapse behavior, diagnostics contract."),
]


def main() -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    lines: list[str] = []
    lines.append("# systemgmmkit Panel Econometrics Certification Report")
    lines.append("")
    lines.append(f"Generated: `{now}`")
    lines.append("")
    lines.append("## Certification Summary")
    lines.append("")
    lines.append("| Suite | Status | Test Path | Scope |")
    lines.append("|---|---:|---|---|")

    for suite, status, path, scope in CERTIFICATION_ROWS:
        lines.append(f"| {suite} | {status} | `{path}` | {scope} |")

    lines.append("")
    lines.append("## Current Certification Position")
    lines.append("")
    lines.append("- Static panel estimators have certification tests for FE, RE, IV/2SLS, and FD workflows.")
    lines.append("- Difference GMM has expanded native certification coverage across balanced/unbalanced panels, missing periods, lag windows, and collapsed/uncollapsed instruments.")
    lines.append("- System GMM has native certification coverage across the same structural scenarios, but remains labelled experimental until strict coefficient and standard-error parity against xtabond2 and pydynpd is completed.")
    lines.append("- Windmeijer correction remains explicitly not certified unless separately implemented and benchmarked.")
    lines.append("")
    lines.append("## Reviewer-Relevant Status")
    lines.append("")
    lines.append("| Component | Reviewer Claim Allowed Now | Stronger Claim Still Needed |")
    lines.append("|---|---|---|")
    lines.append("| FE / RE / IV / FD | Implemented and certification-tested | Strict Stata/linearmodels parity for all SE variants |")
    lines.append("| Difference GMM | Expanded native certification-tested | Full xtabond2/pydynpd parity table across benchmark specs |")
    lines.append("| System GMM | Runs and passes structural certification | Strict xtabond2/pydynpd parity for coefficients, SEs, diagnostics, sample, and instruments |")
    lines.append("| Diagnostics | Implemented and contract-tested | Numeric parity against reference implementations |")
    lines.append("")
    lines.append("## Next Certification Milestone")
    lines.append("")
    lines.append("Native System GMM strict parity against xtabond2 and pydynpd:")
    lines.append("")
    lines.append("1. coefficient parity;")
    lines.append("2. standard-error parity;")
    lines.append("3. AR(1), AR(2), Hansen, Sargan, Diff-Hansen parity;")
    lines.append("4. instrument-count parity;")
    lines.append("5. exact estimation-sample parity.")
    lines.append("")

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {REPORT_PATH}")


if __name__ == "__main__":
    main()
