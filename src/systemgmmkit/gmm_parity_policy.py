"""Policy helpers for interpreting GMM parity comparisons.

This module separates production backend validation from experimental native-GMM parity.
Native Difference/System GMM is operational but not certified as pydynpd- or xtabond2-equivalent yet.
"""

from __future__ import annotations

from dataclasses import dataclass

PASS_PARITY = "PASS_PARITY"
FAIL_PARITY = "FAIL_PARITY"
EXPERIMENTAL_PARITY_PENDING = "EXPERIMENTAL_PARITY_PENDING"
OPERATIONAL_ONLY = "OPERATIONAL_ONLY"


@dataclass(frozen=True)
class GMMParityDecision:
    """Decision object for GMM comparison outcomes."""

    status: str
    blocks_release: bool
    message: str


def classify_gmm_parity(
    *,
    estimator: str,
    backend: str,
    comparison_backend: str | None = None,
    execution_passed: bool,
    strict_parity_passed: bool,
) -> GMMParityDecision:
    """Classify GMM parity results without over-claiming native-GMM certification.

    Rules:
    - pydynpd execution failure is release-blocking.
    - pydynpd execution success is production-acceptable even if external strict parity is pending.
    - native GMM execution success with strict parity failure is experimental, not release-blocking.
    - native GMM execution failure is still a release-blocking failure.
    - non-GMM estimators keep strict parity behavior.
    """

    est = estimator.lower()
    be = backend.lower()
    _ = comparison_backend.lower() if comparison_backend else None

    is_gmm = "gmm" in est or est in {
        "difference",
        "system",
        "difference_gmm",
        "system_gmm",
    }

    if not is_gmm:
        return GMMParityDecision(
            status=PASS_PARITY if strict_parity_passed else FAIL_PARITY,
            blocks_release=not strict_parity_passed,
            message="Non-GMM model uses strict parity policy.",
        )

    if not execution_passed:
        return GMMParityDecision(
            status=FAIL_PARITY,
            blocks_release=True,
            message=f"{backend} GMM execution failed.",
        )

    if be == "pydynpd":
        return GMMParityDecision(
            status=PASS_PARITY if strict_parity_passed else OPERATIONAL_ONLY,
            blocks_release=False,
            message=(
                "pydynpd is the production GMM backend; strict external parity "
                "remains a certification layer."
            ),
        )

    if be == "native":
        if strict_parity_passed:
            return GMMParityDecision(
                status=PASS_PARITY,
                blocks_release=False,
                message="Native GMM passed the requested strict parity comparison.",
            )

        return GMMParityDecision(
            status=EXPERIMENTAL_PARITY_PENDING,
            blocks_release=False,
            message=(
                "Native GMM executed but strict parity is not certified yet. "
                "Use backend='pydynpd' for production Difference/System GMM."
            ),
        )

    return GMMParityDecision(
        status=FAIL_PARITY,
        blocks_release=True,
        message=f"Unknown GMM backend: {backend}.",
    )
