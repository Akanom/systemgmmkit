from __future__ import annotations

from dataclasses import dataclass

from .gmm import GmmDiagnostics
from .panel import (
    DiagnosticResult,
    breusch_pagan_lm,
    hausman_fe_re,
    modified_wald_groupwise_heteroskedasticity,
    pesaran_cd,
    wooldridge_serial_correlation,
)


@dataclass(frozen=True)
class DiagnosticCheck:
    name: str
    value: float | int | None
    passed: bool | None
    interpretation: str


@dataclass(frozen=True)
class DiagnosticReport:
    checks: list[DiagnosticCheck]
    recommendation: str

    def to_markdown(self) -> str:
        lines = ["| Diagnostic | Value | Pass | Interpretation |", "|---|---:|:---:|---|"]
        for c in self.checks:
            value = (
                ""
                if c.value is None
                else f"{c.value:.4g}"
                if isinstance(c.value, float)
                else str(c.value)
            )
            passed = "—" if c.passed is None else "Yes" if c.passed else "No"
            lines.append(f"| {c.name} | {value} | {passed} | {c.interpretation} |")
        lines.append("")
        lines.append(f"**Recommendation:** {self.recommendation}")
        return "\n".join(lines)


@dataclass(frozen=True)
class InstrumentHealth:
    """Instrument-proliferation assessment for a fitted GMM result."""

    n_instruments: int | None
    n_groups: int | None
    ratio: float | None
    status: str
    warning: str | None
    recommendation: str

    @property
    def proliferation_detected(self) -> bool:
        return self.status == "critical"

    def to_markdown(self) -> str:
        instruments = "unavailable" if self.n_instruments is None else str(self.n_instruments)
        groups = "unavailable" if self.n_groups is None else str(self.n_groups)
        ratio = "unavailable" if self.ratio is None else f"{self.ratio:.3f}"
        lines = [
            "## Instrument health",
            "",
            f"- Instruments: `{instruments}`",
            f"- Groups: `{groups}`",
            f"- Instrument/group ratio: `{ratio}`",
            f"- Status: **{self.status.upper()}**",
        ]
        if self.warning:
            lines.extend(["", f"> **Warning:** {self.warning}"])
        lines.extend(["", f"**Recommendation:** {self.recommendation}"])
        return "\n".join(lines)


def check_instrument_health(
    result: object,
    *,
    warning_ratio: float = 0.8,
) -> InstrumentHealth:
    """Assess instrument count relative to the cross-sectional group count.

    This is a diagnostic rule of thumb, not a mechanical validity test. An
    instrument count above the number of groups is classified as critical;
    ratios strictly above ``warning_ratio`` are classified as approaching.
    """

    if not 0.0 < warning_ratio <= 1.0:
        raise ValueError("warning_ratio must be in the interval (0, 1].")

    n_instruments = getattr(result, "n_instruments", None)
    n_groups = getattr(result, "n_groups", None)
    n_instruments = int(n_instruments) if n_instruments is not None else None
    n_groups = int(n_groups) if n_groups is not None else None

    if n_instruments is not None and n_instruments < 0:
        raise ValueError("n_instruments must be non-negative.")
    if n_groups is not None and n_groups <= 0:
        raise ValueError("n_groups must be positive when supplied.")

    if n_instruments is None or n_groups is None:
        return InstrumentHealth(
            n_instruments=n_instruments,
            n_groups=n_groups,
            ratio=None,
            status="unavailable",
            warning="Instrument health could not be assessed because both counts are required.",
            recommendation="Report the instrument count and cross-sectional group count.",
        )

    ratio = n_instruments / n_groups
    if n_instruments > n_groups:
        return InstrumentHealth(
            n_instruments=n_instruments,
            n_groups=n_groups,
            ratio=ratio,
            status="critical",
            warning=(
                "Instrument proliferation detected (instruments exceed groups). "
                "This can overfit endogenous variables, weaken Hansen-test power, "
                "and make inference less reliable."
            ),
            recommendation=(
                "Shorten GMM lag windows (for example, use (2, 3) instead of a deep "
                "open-ended window), enable collapse=True, and report sensitivity checks."
            ),
        )
    if ratio > warning_ratio:
        return InstrumentHealth(
            n_instruments=n_instruments,
            n_groups=n_groups,
            ratio=ratio,
            status="approaching",
            warning="Instrument count is approaching the number of groups.",
            recommendation=(
                "Monitor Hansen/Sargan results and compare estimates using shorter lag "
                "windows or collapsed instruments."
            ),
        )
    return InstrumentHealth(
        n_instruments=n_instruments,
        n_groups=n_groups,
        ratio=ratio,
        status="acceptable",
        warning=None,
        recommendation=(
            "Keep reporting the count and verify robustness across defensible instrument sets."
        ),
    )


def assess_diagnostics(
    *,
    ar1_p: float | None = None,
    ar2_p: float | None = None,
    hansen_p: float | None = None,
    sargan_p: float | None = None,
    diff_hansen_p: float | None = None,
    n_instruments: int | None = None,
    n_entities: int | None = None,
) -> DiagnosticReport:
    checks: list[DiagnosticCheck] = []

    checks.append(
        DiagnosticCheck(
            "AR(1) p-value",
            ar1_p,
            None if ar1_p is None else ar1_p < 0.10,
            "Expected to be significant or near-significant in differenced errors.",
        )
    )
    checks.append(
        DiagnosticCheck(
            "AR(2) p-value",
            ar2_p,
            None if ar2_p is None else ar2_p > 0.10,
            "Should not be significant; rejection implies invalid lag instruments.",
        )
    )
    checks.append(
        DiagnosticCheck(
            "Hansen p-value",
            hansen_p,
            None if hansen_p is None else 0.05 < hansen_p < 0.90,
            "Should not reject, but values near 1 can indicate instrument proliferation.",
        )
    )
    checks.append(
        DiagnosticCheck(
            "Sargan p-value",
            sargan_p,
            None if sargan_p is None else sargan_p > 0.05,
            "Useful under homoskedasticity; less reliable with robust two-step estimation.",
        )
    )
    checks.append(
        DiagnosticCheck(
            "Difference-in-Hansen p-value",
            diff_hansen_p,
            None if diff_hansen_p is None else diff_hansen_p > 0.05,
            "Should not reject validity of additional system/instrument subsets.",
        )
    )

    instrument_pass: bool | None = None
    instrument_value: float | None = None

    if n_instruments is not None and n_entities is not None and n_entities > 0:
        instrument_value = n_instruments / n_entities
        instrument_pass = n_instruments <= n_entities

    checks.append(
        DiagnosticCheck(
            "Instrument/entity ratio",
            instrument_value,
            instrument_pass,
            "Prefer instruments fewer than, or at least not materially above, number of entities.",
        )
    )

    failures = [c.name for c in checks if c.passed is False]

    if not failures:
        recommendation = "Diagnostics are broadly defensible. Interpret coefficients with normal dynamic-panel caution."
    elif "AR(2) p-value" in failures:
        recommendation = (
            "Do not rely on this specification until serial-correlation failure is resolved."
        )
    elif "Instrument/entity ratio" in failures or "Hansen p-value" in failures:
        recommendation = "Reduce instrument count: collapse instruments, shorten lag windows, or move weakly endogenous blocks to IV-style treatment."
    else:
        recommendation = (
            "Use as sensitivity evidence only; explain diagnostic weaknesses transparently."
        )

    return DiagnosticReport(checks=checks, recommendation=recommendation)


__all__ = [
    "DiagnosticCheck",
    "DiagnosticReport",
    "DiagnosticResult",
    "GmmDiagnostics",
    "InstrumentHealth",
    "assess_diagnostics",
    "breusch_pagan_lm",
    "hausman_fe_re",
    "modified_wald_groupwise_heteroskedasticity",
    "pesaran_cd",
    "wooldridge_serial_correlation",
    "check_instrument_health",
]
