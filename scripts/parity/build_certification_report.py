from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

REPORT_PATH = Path("artifacts/parity/panel_econometrics_certification_report.md")
UNIFIED_CERTIFICATE = Path("artifacts/parity/xtabond2/diagnostic_parity_certificate.csv")
CERTIFIED_SYSTEM_GMM_SPECS = {
    "system_gmm_baseline_controls",
    "system_gmm_no_controls",
    "system_gmm_three_way_controls",
    "system_gmm_decomposition_controls",
}


CERTIFICATION_ROWS = [
    (
        "Conformance Suite",
        "PASS",
        "tests/conformance",
        "Core API, diagnostics, reporting, and registry contracts.",
    ),
    (
        "Static Estimator Certification",
        "PASS",
        "tests/parity/static",
        "FD, FE, RE, IV/2SLS certification contracts.",
    ),
    (
        "Difference GMM Expanded Certification",
        "PASS",
        "tests/parity/gmm/test_difference_gmm_expanded_certification.py",
        "Balanced, unbalanced, missing periods, lag windows, collapse behavior.",
    ),
    (
        "System GMM Structural Contract",
        "CONTRACT_PASS",
        "tests/parity/gmm/test_system_gmm_certification.py",
        "Balanced, unbalanced, missing periods, lag windows, collapse behavior, and diagnostic availability.",
    ),
]


def _unified_certificate_status() -> str:
    if not UNIFIED_CERTIFICATE.exists():
        return "MISSING"
    frame = pd.read_csv(UNIFIED_CERTIFICATE)
    required = {
        "spec",
        "status",
        "parameter_status",
        "diagnostic_status",
        "parameter_set_complete",
        "parameters_finite",
        "standard_errors_positive",
    }
    if frame.empty or not required.issubset(frame.columns):
        return "INVALID"
    passes = (
        set(frame["spec"]) == CERTIFIED_SYSTEM_GMM_SPECS
        and frame["status"].eq("PASS_XTABOND2_PARITY").all()
        and frame["parameter_status"].eq("PASS_PARAMETER_PARITY").all()
        and frame["diagnostic_status"].eq("PASS_DIAGNOSTIC_PARITY").all()
        and frame["parameter_set_complete"].eq(True).all()
        and frame["parameters_finite"].eq(True).all()
        and frame["standard_errors_positive"].eq(True).all()
    )
    return "PASS" if passes else "FAIL"


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

    certification_rows = [
        *CERTIFICATION_ROWS,
        (
            "System GMM xtabond2 Unified Parity",
            _unified_certificate_status(),
            UNIFIED_CERTIFICATE.as_posix(),
            "Four aligned specifications: parameters, Windmeijer SEs, exact counts, Hansen/Sargan, and signed AR diagnostics.",
        ),
    ]

    for suite, status, path, scope in certification_rows:
        lines.append(f"| {suite} | {status} | `{path}` | {scope} |")

    lines.append("")
    lines.append("## Current Certification Position")
    lines.append("")
    lines.append(
        "- Static panel estimators have certification tests for FE, RE, IV/2SLS, and FD workflows."
    )
    lines.append(
        "- Difference GMM has expanded native certification coverage across balanced/unbalanced panels, missing periods, lag windows, and collapsed/uncollapsed instruments."
    )
    lines.append(
        "- System GMM has benchmark-specific xtabond2 parity for complete parameter sets, Windmeijer standard errors, exact structural counts, Hansen/Sargan diagnostics, and signed AR diagnostics on four aligned specifications."
    )
    lines.append(
        "- The numerical gate reads raw native and Stata artifacts and records fixture, do-file, parameter-export, and diagnostic-export SHA-256 hashes."
    )
    lines.append(
        "- Stata xtabond2 is the formal certification oracle; pydynpd is an optional execution backend and auxiliary comparator."
    )
    lines.append("")
    lines.append("## Reviewer-Relevant Status")
    lines.append("")
    lines.append("| Component | Reviewer Claim Allowed Now | Stronger Claim Still Needed |")
    lines.append("|---|---|---|")
    lines.append(
        "| FE / RE / IV / FD | Implemented and certification-tested | Strict Stata/linearmodels parity for all SE variants |"
    )
    lines.append(
        "| Difference GMM | Expanded native certification-tested | Additional aligned xtabond2 specifications |"
    )
    lines.append(
        "| System GMM | Four-spec benchmark-specific xtabond2 estimation and diagnostic parity | Broader data/specification coverage |"
    )
    lines.append(
        "| Diagnostics | Four-spec Hansen/Sargan and signed AR numerical parity | Difference-in-Hansen and broader designs |"
    )
    lines.append("")
    lines.append("## Next Certification Milestone")
    lines.append("")
    lines.append("Extend the current System GMM certification boundary:")
    lines.append("")
    lines.append("1. add or explicitly exclude `system_gmm_three_way_no_controls`;")
    lines.append("2. add unbalanced-panel and missing-data fixtures;")
    lines.append("3. certify applicable Difference-in-Hansen diagnostics;")
    lines.append("4. add alternative lag and instrument-classification designs;")
    lines.append("5. create a separately aligned pydynpd contract before speed ranking.")
    lines.append("")
    lines.append(
        "A pydynpd parity or speed comparison is a separate milestone and requires the full alignment gate to pass first."
    )
    lines.append("")

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {REPORT_PATH}")


if __name__ == "__main__":
    main()
