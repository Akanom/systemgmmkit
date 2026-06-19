from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence
import html
import math

import numpy as np

import matplotlib
matplotlib.use("Agg", force=True)
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.patches import FancyBboxPatch
from matplotlib.ticker import MaxNLocator


SGM_COLORS = {
    "ink": "#111827",
    "muted": "#52616B",
    "primary": "#0F3D5E",
    "primary_light": "#DBEAFE",
    "grid": "#E5E7EB",
    "card": "#FFFFFF",
    "border": "#CBD5E1",
    "pass": "#166534",
    "warn": "#B45309",
    "fail": "#B91C1C",
    "info": "#1F5AA6",
    "neutral": "#64748B",
    "accent": "#C2410C",
}


@dataclass(frozen=True)
class HealthMetrics:
    """
    Compact model-health record for dynamic panel post-estimation dashboards.

    Designed for System GMM / Difference GMM but usable with FE, RE, IV, and OLS
    when only a subset of diagnostics is available.
    """

    estimator: str = "System GMM"
    nobs: int | None = None
    groups: int | None = None
    instruments: int | None = None
    parameters: int | None = None
    collapsed: bool | None = None
    transformation: str | None = None
    covariance_type: str | None = None

    hansen_p: float | None = None
    sargan_p: float | None = None
    ar1_stat: float | None = None
    ar1_p: float | None = None
    ar2_stat: float | None = None
    ar2_p: float | None = None

    notes: tuple[str, ...] = field(default_factory=tuple)

    @property
    def instrument_group_ratio(self) -> float | None:
        if self.groups in (None, 0) or self.instruments is None:
            return None
        return float(self.instruments) / float(self.groups)

    @classmethod
    def from_result(cls, result: Any, *, estimator: str | None = None) -> "HealthMetrics":
        return cls(
            estimator=estimator or str(_get(result, ["estimator", "model_name", "method"], "Model")),
            nobs=_as_optional_int(_get(result, ["nobs", "n_obs", "observations"])),
            groups=_as_optional_int(_get(result, ["groups", "n_groups", "entities", "n_entities"])),
            instruments=_as_optional_int(_get(result, ["instruments", "n_instruments", "instrument_count"])),
            parameters=_as_optional_int(_get(result, ["parameters", "n_params", "k_params"])),
            collapsed=_as_optional_bool(_get(result, ["collapsed", "collapse"])),
            transformation=_as_optional_str(_get(result, ["transformation", "transform"])),
            covariance_type=_as_optional_str(_get(result, ["covariance_type", "cov_type"])),
            hansen_p=_as_optional_float(_get(result, ["hansen_p", "hansen_p_value"])),
            sargan_p=_as_optional_float(_get(result, ["sargan_p", "sargan_p_value"])),
            ar1_stat=_as_optional_float(_get(result, ["ar1_stat", "ar1_z", "ar1"])),
            ar1_p=_as_optional_float(_get(result, ["ar1_p", "ar1_p_value"])),
            ar2_stat=_as_optional_float(_get(result, ["ar2_stat", "ar2_z", "ar2"])),
            ar2_p=_as_optional_float(_get(result, ["ar2_p", "ar2_p_value"])),
        )


@dataclass(frozen=True)
class InstrumentArchitecture:
    estimator: str = "System GMM"
    difference_equation: tuple[str, ...] = field(default_factory=tuple)
    level_equation: tuple[str, ...] = field(default_factory=tuple)
    standard_instruments: tuple[str, ...] = field(default_factory=tuple)
    lag_range: tuple[int, int] | None = None
    collapsed: bool | None = None
    transformation: str | None = None
    total_instruments: int | None = None
    groups: int | None = None
    counts_by_lag: Mapping[int, int] | None = None

    @property
    def instrument_group_ratio(self) -> float | None:
        if self.groups in (None, 0) or self.total_instruments is None:
            return None
        return float(self.total_instruments) / float(self.groups)


@dataclass(frozen=True)
class PersistenceAnalytics:
    phi: float
    half_life: float | None
    long_run_multiplier: float | None
    persistence_class: str
    stable: bool

    @classmethod
    def from_phi(cls, phi: float) -> "PersistenceAnalytics":
        phi = float(phi)
        stable = abs(phi) < 1.0

        half_life: float | None = None
        if 0 < abs(phi) < 1:
            half_life = math.log(0.5) / math.log(abs(phi))

        long_run_multiplier: float | None = None
        if stable:
            long_run_multiplier = 1.0 / (1.0 - phi)

        abs_phi = abs(phi)
        if not stable:
            persistence_class = "Unstable"
        elif abs_phi < 0.25:
            persistence_class = "Low"
        elif abs_phi < 0.50:
            persistence_class = "Moderate"
        elif abs_phi < 0.80:
            persistence_class = "High"
        else:
            persistence_class = "Very high"

        return cls(
            phi=phi,
            half_life=half_life,
            long_run_multiplier=long_run_multiplier,
            persistence_class=persistence_class,
            stable=stable,
        )


class SGMVizAccessor:
    """
    Lightweight result-object adapter.

    Usage:
        from systemgmmkit.postestimation import sgm_viz
        sgm_viz(result).health(save="health.png")
    """

    def __init__(self, result: Any):
        self.result = result

    def health(self, *, save: str | Path | None = None) -> Figure:
        return model_health_dashboard_v2(
            HealthMetrics.from_result(self.result),
            save=save,
        )

    def persistence(self, *, phi: float | None = None, periods: int = 20, save: str | Path | None = None) -> Figure:
        if phi is None:
            phi = _infer_lag_coefficient(self.result)
        return dynamic_persistence_dashboard_v2(
            phi,
            periods=periods,
            save=save,
        )

    def publication_panel(
        self,
        *,
        metrics: HealthMetrics | None = None,
        instruments: InstrumentArchitecture | None = None,
        phi: float | None = None,
        save: str | Path | None = None,
    ) -> Figure:
        return publication_panel_v2(
            metrics=metrics or HealthMetrics.from_result(self.result),
            phi=_infer_lag_coefficient(self.result) if phi is None else phi,
            instruments=instruments,
            result=self.result,
            save=save,
        )


def sgm_viz(result: Any) -> SGMVizAccessor:
    return SGMVizAccessor(result)


def _get(obj: Any, names: Sequence[str], default: Any = None) -> Any:
    if obj is None:
        return default
    for name in names:
        if isinstance(obj, Mapping) and name in obj:
            return obj[name]
        if hasattr(obj, name):
            return getattr(obj, name)
    return default


def _as_optional_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        out = float(value)
    except Exception:
        return None
    if not np.isfinite(out):
        return None
    return out


def _as_optional_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        out = int(value)
    except Exception:
        return None
    return out


def _as_optional_bool(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lower = value.strip().lower()
        if lower in {"true", "yes", "y", "1"}:
            return True
        if lower in {"false", "no", "n", "0"}:
            return False
    return bool(value)


def _as_optional_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _fmt(value: Any, digits: int = 3, missing: str = "-") -> str:
    if value is None:
        return missing
    if isinstance(value, (int, np.integer)):
        return f"{int(value):,}"
    try:
        v = float(value)
    except Exception:
        return str(value)
    if not np.isfinite(v):
        return missing
    return f"{v:.{digits}f}"


def _status_p_value(
    p_value: float | None,
    *,
    test_type: str,
) -> tuple[str, str, str]:
    """
    Return status, color, interpretation.

    For Arellano-Bond diagnostics:
    - AR(2) should generally not reject.
    - AR(1) rejection is expected in differenced residuals, so it is informational.
    """

    if p_value is None:
        return "NA", SGM_COLORS["neutral"], "not reported"

    p = float(p_value)

    if test_type.lower() == "ar1":
        if p < 0.05:
            return "INFO", SGM_COLORS["info"], "AR(1) rejection is common in first-differenced residuals"
        if p < 0.10:
            return "CHECK", SGM_COLORS["warn"], "weak AR(1) evidence"
        return "INFO", SGM_COLORS["neutral"], "no strong AR(1) evidence"

    if p >= 0.05:
        return "PASS", SGM_COLORS["pass"], "acceptable"
    if p >= 0.01:
        return "WARN", SGM_COLORS["warn"], "borderline"
    return "FAIL", SGM_COLORS["fail"], "problematic"


def _status_ratio(ratio: float | None) -> tuple[str, str, str]:
    if ratio is None:
        return "NA", SGM_COLORS["neutral"], "not reported"
    if ratio <= 0.80:
        return "PASS", SGM_COLORS["pass"], "disciplined instrument count"
    if ratio <= 1.00:
        return "WARN", SGM_COLORS["warn"], "near group count"
    return "FAIL", SGM_COLORS["fail"], "instrument proliferation risk"


def _card(
    ax: Axes,
    xy: tuple[float, float],
    width: float,
    height: float,
    *,
    facecolor: str = "#FFFFFF",
    edgecolor: str = "#CBD5E1",
    linewidth: float = 0.9,
    radius: float = 0.035,
) -> FancyBboxPatch:
    patch = FancyBboxPatch(
        xy,
        width,
        height,
        boxstyle=f"round,pad=0.012,rounding_size={radius}",
        linewidth=linewidth,
        edgecolor=edgecolor,
        facecolor=facecolor,
        transform=ax.transAxes,
        clip_on=False,
    )
    ax.add_patch(patch)
    return patch


def _setup_card_axis(ax: Axes) -> None:
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")


def _save(fig: Figure, save: str | Path | None = None, *, dpi: int = 300) -> Figure:
    if save is not None:
        path = Path(save)
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, dpi=dpi, bbox_inches="tight")
    return fig


def _style_plot_axis(ax: Axes) -> None:
    ax.grid(True, axis="y", color=SGM_COLORS["grid"], linewidth=0.7, alpha=0.85)
    ax.grid(True, axis="x", color=SGM_COLORS["grid"], linewidth=0.45, alpha=0.45, linestyle=":")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(SGM_COLORS["border"])
    ax.spines["bottom"].set_color(SGM_COLORS["border"])
    ax.tick_params(colors=SGM_COLORS["ink"], labelsize=8.5)
    ax.xaxis.label.set_color(SGM_COLORS["ink"])
    ax.yaxis.label.set_color(SGM_COLORS["ink"])



def _axis_header(
    ax: Axes,
    title: str,
    subtitle: str | None = None,
    *,
    compact: bool = False,
) -> None:
    """Draw a non-overlapping SGM-Viz axis header."""
    ax.text(
        0.0,
        1.135 if not compact else 1.105,
        title,
        transform=ax.transAxes,
        fontsize=12.2 if not compact else 10.0,
        fontweight="bold",
        color=SGM_COLORS["ink"],
        ha="left",
        va="bottom",
        clip_on=False,
    )

    if subtitle:
        ax.text(
            0.0,
            1.075 if not compact else 1.045,
            subtitle,
            transform=ax.transAxes,
            fontsize=8.4 if not compact else 7.1,
            color=SGM_COLORS["muted"],
            ha="left",
            va="bottom",
            clip_on=False,
        )


def _draw_health_dashboard(ax: Axes, metrics: HealthMetrics, *, compact: bool = False) -> None:
    _setup_card_axis(ax)

    ax.text(
        0.03,
        0.95,
        "Model health dashboard",
        ha="left",
        va="top",
        fontsize=13.5 if not compact else 11.5,
        fontweight="bold",
        color=SGM_COLORS["ink"],
        transform=ax.transAxes,
    )

    ax.text(
        0.03,
        0.895,
        "Overidentification, serial-correlation, and instrument discipline.",
        ha="left",
        va="top",
        fontsize=8.7 if not compact else 7.5,
        color=SGM_COLORS["muted"],
        transform=ax.transAxes,
    )

    tests = [
        ("Hansen", metrics.hansen_p, "hansen"),
        ("Sargan", metrics.sargan_p, "sargan"),
        ("AR(1)", metrics.ar1_p, "ar1"),
        ("AR(2)", metrics.ar2_p, "ar2"),
    ]

    y0 = 0.76
    row_h = 0.105 if not compact else 0.095

    for i, (label, p_value, kind) in enumerate(tests):
        y = y0 - i * row_h
        status, color, explanation = _status_p_value(p_value, test_type=kind)

        _card(ax, (0.03, y - 0.055), 0.94, 0.078, facecolor="#FFFFFF", edgecolor="#E2E8F0", radius=0.022)

        ax.text(0.055, y, label, fontsize=9.5 if not compact else 8.2, fontweight="bold", color=SGM_COLORS["ink"], va="center")
        ax.text(0.33, y, _fmt(p_value), fontsize=9.5 if not compact else 8.2, color=SGM_COLORS["ink"], va="center")

        _card(ax, (0.51, y - 0.028), 0.16, 0.052, facecolor=color, edgecolor=color, radius=0.018)
        ax.text(0.59, y, status, fontsize=8.2 if not compact else 7.2, fontweight="bold", color="white", ha="center", va="center")

        ax.text(
            0.70,
            y,
            explanation[:42] + ("..." if len(explanation) > 42 else ""),
            fontsize=7.8 if not compact else 6.8,
            color=SGM_COLORS["muted"],
            va="center",
        )

    ratio = metrics.instrument_group_ratio
    ratio_status, ratio_color, ratio_note = _status_ratio(ratio)

    summary_items = [
        ("Estimator", metrics.estimator),
        ("N", _fmt(metrics.nobs, 0)),
        ("Groups", _fmt(metrics.groups, 0)),
        ("Instruments", _fmt(metrics.instruments, 0)),
        ("Instr/Group", _fmt(ratio)),
        ("Collapsed", "Yes" if metrics.collapsed else "No" if metrics.collapsed is False else "-"),
    ]

    start_y = 0.29
    x_positions = [0.03, 0.36, 0.69]

    for i, (label, value) in enumerate(summary_items):
        x = x_positions[i % 3]
        y = start_y - (i // 3) * 0.105
        _card(ax, (x, y - 0.06), 0.28, 0.08, facecolor="#F8FAFC", edgecolor="#E2E8F0", radius=0.02)
        ax.text(x + 0.018, y - 0.002, label, fontsize=7.5, color=SGM_COLORS["muted"], va="center")
        ax.text(x + 0.018, y - 0.033, str(value), fontsize=9.0, fontweight="bold", color=SGM_COLORS["ink"], va="center")

    _card(ax, (0.03, 0.035), 0.94, 0.07, facecolor=ratio_color, edgecolor=ratio_color, radius=0.022)
    ax.text(
        0.055,
        0.069,
        f"Instrument discipline: {ratio_status} — {ratio_note}",
        fontsize=8.5 if not compact else 7.4,
        fontweight="bold",
        color="white",
        va="center",
    )


def model_health_dashboard_v2(
    metrics: HealthMetrics | Mapping[str, Any] | Any,
    *,
    save: str | Path | None = None,
    title: str | None = None,
) -> Figure:
    if not isinstance(metrics, HealthMetrics):
        if isinstance(metrics, Mapping):
            metrics = HealthMetrics(**metrics)
        else:
            metrics = HealthMetrics.from_result(metrics)

    fig, ax = plt.subplots(figsize=(8.8, 5.8))
    fig.patch.set_facecolor("#F8FAFC")
    ax.set_facecolor("#F8FAFC")
    _draw_health_dashboard(ax, metrics)

    if title:
        fig.suptitle(title, fontsize=14, fontweight="bold", x=0.02, y=0.99, ha="left")

    fig.tight_layout()
    return _save(fig, save)



def _draw_persistence_dashboard(ax: Axes, phi: float, *, periods: int = 20, compact: bool = False) -> PersistenceAnalytics:
    analytics = PersistenceAnalytics.from_phi(phi)

    t = np.arange(periods + 1)
    response = np.power(float(phi), t)

    ax.plot(
        t,
        response,
        color=SGM_COLORS["primary"],
        linewidth=2.2,
        marker="o" if periods <= 24 else None,
        markersize=3.6 if compact else 3.9,
        markeredgecolor="white",
        markeredgewidth=0.7,
    )
    ax.axhline(0, color=SGM_COLORS["muted"], linestyle="--", linewidth=0.9, alpha=0.55)

    if analytics.half_life is not None and 0 <= analytics.half_life <= periods:
        ax.axvline(analytics.half_life, color=SGM_COLORS["accent"], linestyle=":", linewidth=1.2)
        ax.text(
            analytics.half_life,
            np.nanmax(response) * 0.55,
            f"half-life {analytics.half_life:.2f}",
            rotation=90,
            fontsize=7.6 if compact else 8.0,
            color=SGM_COLORS["accent"],
            va="center",
            ha="right",
        )

    _axis_header(
        ax,
        "Dynamic persistence analytics",
        "Shock decay implied by the lagged dependent-variable coefficient.",
        compact=compact,
    )

    ax.set_xlabel("Periods after shock")
    ax.set_ylabel("Remaining effect")
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    _style_plot_axis(ax)

    stats = [
        ("phi", f"{analytics.phi:.3f}"),
        ("half-life", _fmt(analytics.half_life)),
        ("LR multiplier", _fmt(analytics.long_run_multiplier)),
        ("class", analytics.persistence_class),
    ]

    x0 = 0.60 if compact else 0.58
    y0 = 0.86
    width = 0.34 if compact else 0.36

    for i, (label, value) in enumerate(stats):
        y = y0 - i * (0.097 if not compact else 0.088)
        _card(ax, (x0, y - 0.045), width, 0.068, facecolor="#FFFFFF", edgecolor="#E2E8F0", radius=0.018)
        ax.text(x0 + 0.018, y - 0.006, label, transform=ax.transAxes, fontsize=7.2 if compact else 7.8, color=SGM_COLORS["muted"], va="center")
        ax.text(x0 + 0.17, y - 0.006, value, transform=ax.transAxes, fontsize=8.0 if compact else 8.8, fontweight="bold", color=SGM_COLORS["ink"], va="center")

    return analytics

def dynamic_persistence_dashboard_v2(
    phi: float,
    *,
    periods: int = 20,
    save: str | Path | None = None,
) -> Figure:
    fig, ax = plt.subplots(figsize=(8.4, 5.2))
    fig.patch.set_facecolor("#FFFFFF")
    _draw_persistence_dashboard(ax, phi, periods=periods)
    fig.tight_layout()
    return _save(fig, save)



def _draw_instrument_architecture(ax: Axes, spec: InstrumentArchitecture, *, compact: bool = False) -> None:
    _setup_card_axis(ax)

    ax.text(
        0.03,
        0.955,
        "Instrument architecture",
        fontsize=12.3 if not compact else 10.5,
        fontweight="bold",
        color=SGM_COLORS["ink"],
        ha="left",
        va="top",
    )
    ax.text(
        0.03,
        0.905,
        "Equation-level instrument design and proliferation risk.",
        fontsize=8.0 if not compact else 6.9,
        color=SGM_COLORS["muted"],
        ha="left",
        va="top",
    )

    # Two-column layout:
    # left = instrument tree, right = model/instrument metadata.
    tree_x = 0.04
    tree_w = 0.58 if not compact else 0.57
    meta_x = 0.66
    meta_w = 0.30

    sections = [
        ("Difference equation", spec.difference_equation, SGM_COLORS["primary"]),
        ("Level equation", spec.level_equation, SGM_COLORS["info"]),
        ("Standard instruments", spec.standard_instruments, SGM_COLORS["neutral"]),
    ]

    current_y = 0.79
    max_items = 4 if compact else 5
    item_gap = 0.043 if compact else 0.047
    section_gap = 0.030 if compact else 0.036

    for section_title, items, color in sections:
        if not items:
            continue

        header_h = 0.055 if compact else 0.060
        _card(ax, (tree_x, current_y - header_h), tree_w, header_h, facecolor=color, edgecolor=color, radius=0.018)
        ax.text(tree_x + 0.020, current_y - header_h / 2, section_title, fontsize=7.6 if compact else 8.2, fontweight="bold", color="white", va="center")

        current_y -= header_h + 0.020

        for item in list(items)[:max_items]:
            y_line = current_y - 0.012
            ax.plot([tree_x + 0.038, tree_x + 0.038], [y_line - 0.019, y_line + 0.016], color=SGM_COLORS["border"], linewidth=1)
            ax.plot([tree_x + 0.038, tree_x + 0.068], [y_line - 0.019, y_line - 0.019], color=SGM_COLORS["border"], linewidth=1)
            ax.text(tree_x + 0.082, y_line - 0.019, str(item), fontsize=7.3 if compact else 8.0, color=SGM_COLORS["ink"], va="center")
            current_y -= item_gap

        if len(items) > max_items:
            ax.text(tree_x + 0.082, current_y - 0.018, f"+ {len(items) - max_items} more", fontsize=7.1, color=SGM_COLORS["muted"], va="center")
            current_y -= item_gap

        current_y -= section_gap

    ratio = spec.instrument_group_ratio
    ratio_status, ratio_color, ratio_note = _status_ratio(ratio)

    meta = [
        ("Estimator", spec.estimator),
        ("Lag range", f"{spec.lag_range[0]}–{spec.lag_range[1]}" if spec.lag_range else "-"),
        ("Collapsed", "Yes" if spec.collapsed else "No" if spec.collapsed is False else "-"),
        ("Transform", spec.transformation or "-"),
        ("Instruments", _fmt(spec.total_instruments, 0)),
        ("Instr/Group", _fmt(ratio)),
    ]

    ax.text(
        meta_x,
        0.79,
        "Model metadata",
        fontsize=8.6 if not compact else 7.4,
        fontweight="bold",
        color=SGM_COLORS["ink"],
        va="top",
    )

    y0 = 0.72
    row_h = 0.091 if not compact else 0.081

    for i, (label, value) in enumerate(meta):
        y = y0 - i * row_h
        _card(ax, (meta_x, y - 0.054), meta_w, 0.070, facecolor="#F8FAFC", edgecolor="#E2E8F0", radius=0.017)
        ax.text(meta_x + 0.015, y - 0.005, label, fontsize=6.9 if compact else 7.4, color=SGM_COLORS["muted"], va="center")
        ax.text(meta_x + 0.015, y - 0.033, str(value), fontsize=7.8 if compact else 8.6, fontweight="bold", color=SGM_COLORS["ink"], va="center")

    status_y = 0.045
    _card(ax, (0.04, status_y), 0.92, 0.070, facecolor=ratio_color, edgecolor=ratio_color, radius=0.020)
    ax.text(
        0.065,
        status_y + 0.035,
        f"{ratio_status}: {ratio_note}",
        fontsize=7.7 if compact else 8.4,
        color="white",
        fontweight="bold",
        va="center",
    )

def instrument_architecture_dashboard_v2(
    architecture: InstrumentArchitecture | Mapping[str, Any],
    *,
    save: str | Path | None = None,
) -> Figure:
    if not isinstance(architecture, InstrumentArchitecture):
        architecture = InstrumentArchitecture(**architecture)

    fig, ax = plt.subplots(figsize=(8.8, 5.8))
    fig.patch.set_facecolor("#F8FAFC")
    ax.set_facecolor("#F8FAFC")
    _draw_instrument_architecture(ax, architecture)
    fig.tight_layout()
    return _save(fig, save)



def effect_surface_dashboard_v2(
    x: Sequence[float],
    y: Sequence[float],
    z: Sequence[float],
    *,
    x_label: str = "x",
    y_label: str = "y",
    z_label: str = "Predicted outcome",
    save: str | Path | None = None,
) -> Figure:
    xs = np.asarray(x, dtype=float).ravel()
    ys = np.asarray(y, dtype=float).ravel()
    zs = np.asarray(z, dtype=float).ravel()

    mask = np.isfinite(xs) & np.isfinite(ys) & np.isfinite(zs)
    xs, ys, zs = xs[mask], ys[mask], zs[mask]

    if len(xs) < 3:
        raise ValueError("At least three finite points are required for an effect surface.")

    fig, ax = plt.subplots(figsize=(8.4, 5.6))
    fig.patch.set_facecolor("#FFFFFF")

    try:
        contour = ax.tricontourf(xs, ys, zs, levels=16, cmap="viridis", alpha=0.92)
        ax.tricontour(xs, ys, zs, levels=8, colors="white", linewidths=0.45, alpha=0.65)
    except Exception:
        contour = ax.scatter(xs, ys, c=zs, cmap="viridis", s=28, alpha=0.88)

    cbar = fig.colorbar(contour, ax=ax)
    cbar.set_label(z_label)

    _axis_header(
        ax,
        "Effect surface dashboard",
        "Joint response surface for nonlinear or interaction effects.",
    )

    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    _style_plot_axis(ax)

    fig.subplots_adjust(top=0.84)
    return _save(fig, save)

def _extract_params(result: Any) -> tuple[list[str], np.ndarray, np.ndarray | None]:
    params = _get(result, ["params", "coef", "coefficients", "coefs"])
    ses = _get(result, ["std_errors", "standard_errors", "bse", "se", "stderr"])

    if params is None:
        return [], np.array([]), None

    if isinstance(params, Mapping):
        terms = [str(k) for k in params.keys()]
        beta = np.asarray(list(params.values()), dtype=float)
    elif hasattr(params, "index") and hasattr(params, "values"):
        terms = [str(k) for k in params.index]
        beta = np.asarray(params.values, dtype=float)
    else:
        beta = np.asarray(params, dtype=float).ravel()
        terms = [f"x{i}" for i in range(len(beta))]

    se_arr: np.ndarray | None = None
    if ses is not None:
        if isinstance(ses, Mapping):
            se_arr = np.asarray([ses.get(t, np.nan) for t in terms], dtype=float)
        elif hasattr(ses, "reindex"):
            se_arr = np.asarray(ses.reindex(terms).values, dtype=float)
        else:
            se_arr = np.asarray(ses, dtype=float).ravel()
            if len(se_arr) != len(beta):
                se_arr = None

    return terms, beta, se_arr



def _draw_parameter_impact(ax: Axes, result: Any, *, max_terms: int = 8) -> None:
    terms, beta, se = _extract_params(result)

    _axis_header(
        ax,
        "Parameter impact",
        "Largest readable coefficients with 95% confidence intervals.",
        compact=True,
    )

    if len(beta) == 0:
        ax.axis("off")
        ax.text(0.05, 0.5, "No coefficient vector available.", transform=ax.transAxes, fontsize=9, color=SGM_COLORS["muted"])
        return

    mask = np.isfinite(beta)
    terms = [t for t, keep in zip(terms, mask) if keep]
    beta = beta[mask]
    if se is not None:
        se = se[mask]

    if len(beta) == 0:
        ax.axis("off")
        ax.text(0.05, 0.5, "No finite coefficients available.", transform=ax.transAxes, fontsize=9, color=SGM_COLORS["muted"])
        return

    order = np.argsort(np.abs(beta))[::-1][:max_terms]
    terms = [terms[i].replace("_", " ") for i in order]
    beta = beta[order]
    se = se[order] if se is not None else None

    y = np.arange(len(beta))[::-1]

    if se is not None and np.all(np.isfinite(se)):
        xerr = 1.959963984540054 * se
        ax.errorbar(beta, y, xerr=xerr, fmt="o", color=SGM_COLORS["primary"], ecolor=SGM_COLORS["primary"], capsize=3)
    else:
        ax.scatter(beta, y, color=SGM_COLORS["primary"], s=22)

    ax.axvline(0, color=SGM_COLORS["accent"], linestyle="--", linewidth=0.9, alpha=0.75)
    ax.set_yticks(y)
    ax.set_yticklabels(terms, fontsize=7.8)
    ax.set_xlabel("Estimate")
    _style_plot_axis(ax)

def publication_panel_v2(
    *,
    metrics: HealthMetrics | Mapping[str, Any] | None = None,
    phi: float | None = None,
    instruments: InstrumentArchitecture | Mapping[str, Any] | None = None,
    result: Any | None = None,
    save: str | Path | None = None,
) -> Figure:
    if metrics is None and result is not None:
        metrics_obj = HealthMetrics.from_result(result)
    elif isinstance(metrics, Mapping):
        metrics_obj = HealthMetrics(**metrics)
    elif isinstance(metrics, HealthMetrics):
        metrics_obj = metrics
    else:
        metrics_obj = HealthMetrics()

    if phi is None:
        phi = _infer_lag_coefficient(result) if result is not None else 0.5

    if instruments is None:
        instruments_obj = InstrumentArchitecture(
            estimator=metrics_obj.estimator,
            difference_equation=("L2.y", "L3.y"),
            level_equation=("D.y",),
            collapsed=metrics_obj.collapsed,
            total_instruments=metrics_obj.instruments,
            groups=metrics_obj.groups,
        )
    elif isinstance(instruments, Mapping):
        instruments_obj = InstrumentArchitecture(**instruments)
    else:
        instruments_obj = instruments

    fig = plt.figure(figsize=(13.2, 8.6))
    fig.patch.set_facecolor("#F8FAFC")

    gs = fig.add_gridspec(2, 2, width_ratios=[1.05, 1.0], height_ratios=[1.0, 1.0], wspace=0.26, hspace=0.42)

    ax_health = fig.add_subplot(gs[0, 0])
    ax_persist = fig.add_subplot(gs[0, 1])
    ax_instr = fig.add_subplot(gs[1, 0])
    ax_param = fig.add_subplot(gs[1, 1])

    _draw_health_dashboard(ax_health, metrics_obj, compact=True)
    _draw_persistence_dashboard(ax_persist, float(phi), periods=20, compact=True)
    _draw_instrument_architecture(ax_instr, instruments_obj, compact=True)

    if result is not None:
        _draw_parameter_impact(ax_param, result)
    else:
        _setup_card_axis(ax_param)
        ax_param.text(0.03, 0.95, "SGM-Viz publication panel", fontsize=12, fontweight="bold", color=SGM_COLORS["ink"], va="top")
        ax_param.text(
            0.03,
            0.84,
            "Add a result object to include a parameter impact plot here.",
            fontsize=8.5,
            color=SGM_COLORS["muted"],
            va="top",
        )
        meta = [
            ("Estimator", metrics_obj.estimator),
            ("N", _fmt(metrics_obj.nobs, 0)),
            ("Groups", _fmt(metrics_obj.groups, 0)),
            ("Instruments", _fmt(metrics_obj.instruments, 0)),
        ]
        for i, (k, v) in enumerate(meta):
            y = 0.68 - i * 0.10
            _card(ax_param, (0.05, y - 0.045), 0.55, 0.07, facecolor="#FFFFFF", edgecolor="#E2E8F0")
            ax_param.text(0.075, y - 0.01, k, fontsize=8, color=SGM_COLORS["muted"], va="center")
            ax_param.text(0.32, y - 0.01, str(v), fontsize=9, fontweight="bold", color=SGM_COLORS["ink"], va="center")

    fig.suptitle(
        "SGM-Viz dynamic panel diagnostic panel",
        x=0.02,
        y=0.99,
        ha="left",
        fontsize=15,
        fontweight="bold",
        color=SGM_COLORS["ink"],
    )
    fig.text(
        0.02,
        0.955,
        "Model health, persistence, instrument architecture, and parameter impact in one publication-ready figure.",
        fontsize=9,
        color=SGM_COLORS["muted"],
        ha="left",
    )

    fig.subplots_adjust(top=0.90)
    return _save(fig, save)


def _infer_lag_coefficient(result: Any) -> float:
    terms, beta, _ = _extract_params(result)
    for term, value in zip(terms, beta):
        lower = term.lower().replace(" ", "")
        if lower.startswith("l1.") or lower.startswith("l.") or "lag" in lower:
            if np.isfinite(value):
                return float(value)
    return 0.5


def export_sgm_viz_v2_gallery(
    figures: Mapping[str, str | Path],
    *,
    output_html: str | Path,
    title: str = "SGM-Viz v2 gallery",
    description: str = "Dynamic panel post-estimation graphics generated by systemgmmkit.",
) -> Path:
    output = Path(output_html)
    output.parent.mkdir(parents=True, exist_ok=True)

    cards: list[str] = []
    for name, path in figures.items():
        p = Path(path)
        rel = p.name if p.parent.resolve() == output.parent.resolve() else str(p)
        label = str(name).replace("_", " ").title()
        cards.append(
            f"""
            <section class="card">
              <h2>{html.escape(label)}</h2>
              <img src="{html.escape(rel)}" alt="{html.escape(label)}">
            </section>
            """
        )

    doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{html.escape(title)}</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
:root {{
  --bg: #f8fafc;
  --card: #ffffff;
  --text: #111827;
  --muted: #52616B;
  --border: #e2e8f0;
}}
body {{
  margin: 0;
  font-family: Arial, sans-serif;
  background: var(--bg);
  color: var(--text);
}}
header {{
  padding: 28px 34px 14px 34px;
}}
h1 {{
  margin: 0 0 6px 0;
  font-size: 28px;
}}
p {{
  margin: 0;
  color: var(--muted);
}}
.grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(520px, 1fr));
  gap: 18px;
  padding: 18px 34px 34px 34px;
}}
.card {{
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 16px;
  box-shadow: 0 8px 22px rgba(15, 23, 42, 0.06);
}}
.card h2 {{
  font-size: 15px;
  margin: 0 0 12px 0;
}}
.card img {{
  width: 100%;
  height: auto;
  display: block;
  border-radius: 8px;
}}
</style>
</head>
<body>
<header>
<h1>{html.escape(title)}</h1>
<p>{html.escape(description)}</p>
</header>
<main class="grid">
{''.join(cards)}
</main>
</body>
</html>
"""
    output.write_text(doc, encoding="utf-8")
    return output


# Friendly aliases
health_dashboard = model_health_dashboard_v2
persistence_dashboard = dynamic_persistence_dashboard_v2
instrument_dashboard = instrument_architecture_dashboard_v2
effect_surface_dashboard = effect_surface_dashboard_v2
publication_panel = publication_panel_v2
