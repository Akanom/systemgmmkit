from __future__ import annotations

from ..diagnostics import DiagnosticReport
from ..pydynpd_backend import build_pydynpd_command
from ..spec import DynamicPanelSpec
from ..validation import PanelValidationReport, estimate_instrument_pressure

from .parity import (
    REQUIRED_PARITY_COLUMNS,
    ParityReport,
    ParityResult,
    classify_parity_result,
)


def model_card_markdown(
    spec: DynamicPanelSpec,
    *,
    panel_report: PanelValidationReport | None = None,
    diagnostic_report: DiagnosticReport | None = None,
    n_entities: int | None = None,
    n_time_dummies: int = 0,
) -> str:
    lines: list[str] = []
    lines.append(f"# Model card: {spec.name}")
    lines.append("")
    lines.append("## Specification")
    lines.append(f"- Dependent variable: `{spec.dependent}`")
    lines.append(f"- Regressors: `{', '.join(spec.regressors)}`")
    lines.append(f"- Estimator: `{'System GMM' if spec.system else 'Difference GMM'}`")
    lines.append(f"- Steps: `{spec.steps}`")
    lines.append(f"- Transformation: `{spec.transformation}`")
    lines.append(f"- Collapse instruments: `{spec.collapse}`")
    lines.append(f"- Time dummies: `{spec.time_dummies}`")
    lines.append("")
    lines.append("## Instrument classification")

    if spec.gmm:
        lines.append("### GMM-style")
        for g in spec.gmm:
            eq = f", eq={g.eq}" if g.eq else ""
            lines.append(f"- `{g.variable}`: lags {g.min_lag}:{g.max_lag}{eq}")

    if spec.iv:
        lines.append("### IV-style / assumed exogenous")
        for iv in spec.iv:
            eq = f", eq={iv.eq}" if iv.eq else ""
            lines.append(f"- `{iv.variable}`{eq}")

    lines.append("")
    lines.append("## pydynpd command")
    lines.append("```text")
    lines.append(build_pydynpd_command(spec))
    lines.append("```")

    if panel_report is not None:
        lines.append("")
        lines.append("## Panel validation")
        lines.append(f"- Observations: `{panel_report.n_obs}`")
        lines.append(f"- Entities: `{panel_report.n_entities}`")
        lines.append(
            f"- T range: `{panel_report.min_t}` to `{panel_report.max_t}`; median `{panel_report.median_t}`"
        )
        lines.append(f"- Balanced: `{panel_report.balanced}`")
        lines.append(f"- Duplicate entity-time rows: `{panel_report.duplicate_rows}`")

        if panel_report.warnings:
            lines.append("- Warnings:")
            for w in panel_report.warnings:
                lines.append(f"  - {w}")

    if n_entities is not None:
        pressure = estimate_instrument_pressure(
            n_entities=n_entities,
            gmm_blocks=[(g.min_lag, g.max_lag) for g in spec.gmm],
            n_iv=len(spec.iv),
            n_time_dummies=n_time_dummies,
            system=spec.system,
            collapse=spec.collapse,
        )

        lines.append("")
        lines.append("## Instrument-pressure heuristic")
        lines.append(f"- Approximate instruments: `{pressure['approx_instruments']}`")
        lines.append(f"- Instrument/entity ratio: `{pressure['ratio']:.3f}`")
        lines.append(f"- Risk: `{pressure['risk']}`")

    if diagnostic_report is not None:
        lines.append("")
        lines.append("## Diagnostics")
        lines.append(diagnostic_report.to_markdown())

    return "\n".join(lines)


__all__ = [
    "REQUIRED_PARITY_COLUMNS",
    "ParityReport",
    "ParityResult",
    "classify_parity_result",
    "model_card_markdown",
]
