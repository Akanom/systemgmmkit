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
    """Build a conservative xtabond2 command template for dynamic GMM parity checks."""

    rhs = " ".join(spec.regressors)
    gmm_parts = []
    for block in spec.gmm:
        gmm_parts.append(f"gmm({block.variable}, lag({block.min_lag} {block.max_lag}) collapse)")
    iv_vars = " ".join(iv.variable for iv in spec.iv)
    iv_part = f"iv({iv_vars})" if iv_vars else ""
    time_part = f"iv(i.{time}, eq(level))" if spec.time_dummies else ""
    nolevel = " noleveleq" if not spec.system else ""
    robust = " twostep robust small"
    parts = " ".join(p for p in [*gmm_parts, iv_part, time_part] if p)
    return f"xtset {entity} {time}\nxtabond2 {spec.dependent} {rhs}, {parts}{nolevel}{robust}"


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
