from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import pandas as pd
from pandas.testing import assert_frame_equal

if __package__:
    from .compare_xtabond2_ar_diagnostics import SPECS, _compare_spec
    from .system_gmm_certification_registry import (
        REGISTRY_PATH,
        REPOSITORY_ROOT,
        load_certification_registry,
    )
else:
    from compare_xtabond2_ar_diagnostics import SPECS, _compare_spec
    from system_gmm_certification_registry import (
        REGISTRY_PATH,
        REPOSITORY_ROOT,
        load_certification_registry,
    )

REPORT_PATH = Path("artifacts/parity/panel_econometrics_certification_report.md")
UNIFIED_CERTIFICATE = Path("artifacts/parity/xtabond2/diagnostic_parity_certificate.csv")
REGISTRY = load_certification_registry(REGISTRY_PATH)
CERTIFIED_SYSTEM_GMM_SPEC_IDS = tuple(REGISTRY.specifications)
CERTIFIED_SYSTEM_GMM_SPECS = frozenset(CERTIFIED_SYSTEM_GMM_SPEC_IDS)


CERTIFICATION_ROWS = [
    (
        "Conformance Suite",
        "TEST_CONTRACT",
        "tests/conformance",
        "Core API, diagnostics, reporting, and registry contracts.",
    ),
    (
        "Static Estimator Certification",
        "TEST_CONTRACT",
        "tests/parity/static",
        "FD, FE, RE, IV/2SLS certification contracts.",
    ),
    (
        "Difference GMM Expanded Certification",
        "TEST_CONTRACT",
        "tests/parity/gmm/test_difference_gmm_expanded_certification.py",
        "Balanced, unbalanced, missing periods, lag windows, collapse behavior.",
    ),
    (
        "System GMM Structural Contract",
        "TEST_CONTRACT",
        "tests/parity/gmm/test_system_gmm_certification.py",
        "Balanced, unbalanced, missing periods, lag windows, collapse behavior, and diagnostic availability.",
    ),
]


def _current_certificate_frame() -> pd.DataFrame:
    return pd.DataFrame([_compare_spec(spec_id, config) for spec_id, config in SPECS.items()])


def _unified_certificate_status(expected: pd.DataFrame | None = None) -> str:
    certificate_path = REPOSITORY_ROOT / UNIFIED_CERTIFICATE
    if not certificate_path.exists():
        return "MISSING"
    frame = pd.read_csv(certificate_path)
    expected = expected if expected is not None else _current_certificate_frame()
    if (
        frame.empty
        or "spec" not in frame.columns
        or len(frame) != len(CERTIFIED_SYSTEM_GMM_SPEC_IDS)
        or not frame["spec"].is_unique
        or list(frame.columns) != list(expected.columns)
    ):
        return "INVALID"
    try:
        assert_frame_equal(frame, expected, check_dtype=False, rtol=1e-12, atol=1e-15)
    except AssertionError:
        return "STALE_OR_TAMPERED"
    passes = frame["status"].eq("PASS_XTABOND2_PARITY").all()
    return "PASS" if passes else "FAIL"


def build_report(*, generated_at: Optional[str] = None) -> str:
    generated_at = generated_at or datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    spec_count = len(CERTIFIED_SYSTEM_GMM_SPEC_IDS)
    registry_relative = REGISTRY_PATH.relative_to(REPOSITORY_ROOT).as_posix()
    maintained_specs = ", ".join(f"`{spec}`" for spec in CERTIFIED_SYSTEM_GMM_SPEC_IDS)
    current_certificate = _current_certificate_frame()

    lines: list[str] = []
    lines.append("# systemgmmkit Panel Econometrics Certification Report")
    lines.append("")
    lines.append(f"Generated: `{generated_at}`")
    lines.append(f"Certification registry: `{registry_relative}`")
    lines.append(
        "Registry scope: the registry and unified certificate are authoritative only for the "
        "maintained System-GMM/xtabond2 row below. Other rows identify separate test contracts; "
        "their execution status is reported by CI, not hardcoded here."
    )
    lines.append("")
    lines.append("## Certification Summary")
    lines.append("")
    lines.append("| Suite | Status | Test Path | Scope |")
    lines.append("|---|---:|---|---|")

    certification_rows = [
        *CERTIFICATION_ROWS,
        (
            "System GMM xtabond2 Unified Parity",
            _unified_certificate_status(current_certificate),
            UNIFIED_CERTIFICATE.as_posix(),
            f"{spec_count} aligned specifications: parameters, Windmeijer SEs, exact counts, Hansen/Sargan, and signed AR diagnostics.",
        ),
    ]

    for suite, status, path, scope in certification_rows:
        lines.append(f"| {suite} | {status} | `{path}` | {scope} |")

    lines.append("")
    lines.append("## Current Certification Position")
    lines.append("")
    lines.append(f"- Maintained System GMM certification specifications: {maintained_specs}.")
    lines.append(
        "- Static panel estimators have certification tests for FE, RE, IV/2SLS, and FD workflows."
    )
    lines.append(
        "- Difference GMM has expanded native certification coverage across balanced/unbalanced panels, missing periods, lag windows, and collapsed/uncollapsed instruments."
    )
    lines.append(
        "- System GMM has benchmark-specific xtabond2 parity for complete parameter sets, Windmeijer standard errors, exact structural counts, Hansen/Sargan diagnostics, and signed AR diagnostics "
        f"on {spec_count} aligned specifications."
    )
    lines.append(
        "- The numerical gate reads raw native and Stata artifacts and records LF-normalized "
        "canonical SHA-256 digests for the registry, comparator, generators, fixtures, do-files, "
        "parameter exports, and diagnostic exports."
    )
    lines.append(
        "- Comparator identity is supplied by a path-free attestation derived from the bounded "
        "completed log and cross-checked against metadata embedded in every tracked Stata "
        "diagnostic export. Its local source log is intentionally uncommitted; the attestation "
        "binds the exact outputs and installed ado observed at generation."
    )
    lines.append(
        "- Stata xtabond2 is the formal certification oracle; pydynpd is an optional execution backend and auxiliary comparator."
    )
    lines.append(
        "- `PASS_XTABOND2_PARITY` means numerical cross-software agreement on these fixtures; it "
        "does not establish instrument validity or endorse a specification."
    )
    lines.append("")
    lines.append("### Stata overidentification evidence (not a parity gate)")
    lines.append("")
    lines.append("| Specification | Hansen p | Reject at 0.05 | Sargan p | Reject at 0.05 |")
    lines.append("|---|---:|---:|---:|---:|")
    for row in current_certificate.to_dict(orient="records"):
        lines.append(
            f"| `{row['spec']}` | {float(row['stata_hansen_p']):.8g} | "
            f"{bool(row['stata_hansen_reject_005'])} | {float(row['stata_sargan_p']):.8g} | "
            f"{bool(row['stata_sargan_reject_005'])} |"
        )
    lines.append("")
    lines.append(
        "Raw p-values and rejection flags are generated from the same recomputed certificate rows."
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
        f"| System GMM | {spec_count}-spec benchmark-specific xtabond2 estimation and diagnostic parity | Broader data/specification coverage |"
    )
    lines.append(
        f"| Diagnostics | {spec_count}-spec Hansen/Sargan and signed AR numerical parity | Difference-in-Hansen and broader designs |"
    )
    lines.append("")
    lines.append("## Next Certification Milestone")
    lines.append("")
    lines.append("Extend the current System GMM certification boundary:")
    lines.append("")
    lines.append(
        "1. generate and register evidence for `system_gmm_three_way_no_controls`, or keep it "
        "explicitly outside the certified boundary;"
    )
    lines.append("2. add short-T, longer-T, and high-N/low-T aligned designs;")
    lines.append("3. certify applicable Difference-in-Hansen diagnostics;")
    lines.append("4. add alternative lag and instrument-classification designs;")
    lines.append("5. create a separately aligned pydynpd contract before speed ranking.")
    lines.append("")
    lines.append(
        "A pydynpd parity or speed comparison is a separate milestone and requires the full alignment gate to pass first."
    )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    report_path = REPOSITORY_ROOT / REPORT_PATH
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(build_report(), encoding="utf-8")
    print(f"Wrote {report_path}")


if __name__ == "__main__":
    main()
