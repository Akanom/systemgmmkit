from __future__ import annotations

from dataclasses import dataclass


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
    """Create a conservative interpretation of System GMM diagnostics."""

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
