from __future__ import annotations

from pathlib import Path

from .fixed_effects import FixedEffectsSpec
from .pydynpd_backend import build_pydynpd_command
from .spec import DynamicPanelSpec


def stata_xtreg_fe_command(spec: FixedEffectsSpec, *, entity: str, time: str) -> str:
    """Build a Stata fixed-effects command template for parity checks."""

    rhs = " ".join(spec.regressors)
    if spec.time_effects:
        rhs = f"{rhs} i.{time}" if rhs else f"i.{time}"
    vce = f", vce(cluster {entity})" if spec.covariance == "clustered" else ""
    if spec.entity_effects:
        return f"xtset {entity} {time}\nxtreg {spec.dependent} {rhs}, fe{vce}"
    return f"reg {spec.dependent} {rhs}{vce}"


def stata_xtabond2_command(spec: DynamicPanelSpec, *, entity: str, time: str) -> str:
    """Build a conservative xtabond2 command template for dynamic GMM parity checks.

    The command is intended as an auditable Stata reference template for the
    Python specification. It preserves the package's instrument classification
    while making transformation and system/difference choices explicit.
    """

    rhs = " ".join(str(v) for v in spec.regressors)

    gmm_parts: list[str] = []
    for block in spec.gmm:
        option_parts = [f"lag({block.min_lag} {block.max_lag})"]

        collapse_enabled = bool(
            getattr(block, "collapse", False) or getattr(spec, "collapse", False)
        )
        if collapse_enabled:
            option_parts.append("collapse")

        options = " ".join(option_parts)
        gmm_parts.append(f"gmmstyle({block.variable}, {options})")

    iv_vars = " ".join(str(iv.variable) for iv in spec.iv)
    iv_part = f"ivstyle({iv_vars})" if iv_vars else ""

    time_part = f"ivstyle(i.{time}, equation(level))" if spec.time_dummies else ""

    nolevel = "noleveleq" if not spec.system else ""

    transformation = str(getattr(spec, "transformation", "")).lower()
    orthogonal = "orthogonal" if transformation in {"fod", "forward_orthogonal_deviations"} else ""

    steps = str(getattr(spec, "steps", "")).lower()
    step_option = "twostep" if steps == "twostep" else "onestep"

    options = [
        *gmm_parts,
        iv_part,
        time_part,
        nolevel,
        step_option,
        "robust",
        "small",
        orthogonal,
    ]

    parts = " ".join(str(p).strip() for p in options if str(p).strip())

    return f"xtset {entity} {time}\nxtabond2 {spec.dependent} {rhs}, {parts}"


def write_stata_parity_do_file(
    path: str | Path,
    *,
    data_path: str,
    entity: str,
    time: str,
    fixed_effects: list[FixedEffectsSpec] | None = None,
    dynamic_gmm: list[DynamicPanelSpec] | None = None,
) -> Path:
    """Write a Stata do-file skeleton for parity testing against systemgmmkit specs."""

    out = Path(path)
    lines = [
        "version 14",
        "clear all",
        "set more off",
        f'import delimited "{data_path}", clear',
        f"xtset {entity} {time}",
        "",
    ]
    for i, spec in enumerate(fixed_effects or [], start=1):
        lines.extend(
            [
                f"* Fixed-effects parity model {i}: {spec.name}",
                stata_xtreg_fe_command(spec, entity=entity, time=time),
                "",
            ]
        )
    for i, spec in enumerate(dynamic_gmm or [], start=1):
        lines.extend(
            [
                f"* Dynamic-panel GMM parity model {i}: {spec.name}",
                f"* pydynpd equivalent: {build_pydynpd_command(spec)}",
                stata_xtabond2_command(spec, entity=entity, time=time),
                "",
            ]
        )
    out.write_text("\n".join(lines), encoding="utf-8")
    return out
