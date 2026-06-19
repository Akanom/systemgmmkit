from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


@dataclass(frozen=True)
class HealthMetrics:
    estimator: str
    nobs: int
    groups: int
    instruments: int

    hansen_p: float | None = None
    sargan_p: float | None = None

    ar1_stat: float | None = None
    ar1_p: float | None = None

    ar2_stat: float | None = None
    ar2_p: float | None = None

    collapsed: bool = False


def _save(fig, save):
    if save:
        save = Path(save)
        save.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save, dpi=300, bbox_inches="tight")
    return fig


def model_health_dashboard(
    metrics: HealthMetrics,
    *,
    save=None,
):
    fig, ax = plt.subplots(figsize=(8.5, 5.5))

    ax.axis("off")

    ratio = metrics.instruments / metrics.groups if metrics.groups else np.nan

    rows = [
        ("Estimator", metrics.estimator),
        ("Observations", f"{metrics.nobs:,}"),
        ("Groups", f"{metrics.groups:,}"),
        ("Instruments", f"{metrics.instruments:,}"),
        ("Collapsed", "Yes" if metrics.collapsed else "No"),
        ("Instr/Group", f"{ratio:.3f}"),
        ("Hansen p", f"{metrics.hansen_p:.3f}" if metrics.hansen_p is not None else "-"),
        ("Sargan p", f"{metrics.sargan_p:.3f}" if metrics.sargan_p is not None else "-"),
        ("AR(1) p", f"{metrics.ar1_p:.3f}" if metrics.ar1_p is not None else "-"),
        ("AR(2) p", f"{metrics.ar2_p:.3f}" if metrics.ar2_p is not None else "-"),
    ]

    ax.text(
        0.02,
        0.95,
        "SYSTEM GMM HEALTH DASHBOARD",
        fontsize=15,
        fontweight="bold",
    )

    y = 0.82

    for key, value in rows:
        ax.text(0.05, y, key, fontsize=11)
        ax.text(0.55, y, value, fontsize=11)
        y -= 0.07

    return _save(fig, save)


def dynamic_persistence_dashboard(
    phi: float,
    *,
    periods: int = 20,
    save=None,
):
    fig, ax = plt.subplots(figsize=(8, 5))

    t = np.arange(periods + 1)

    response = phi**t

    ax.plot(
        t,
        response,
        linewidth=2.5,
        marker="o",
    )

    half_life = None

    if 0 < abs(phi) < 1:
        half_life = math.log(0.5) / math.log(abs(phi))

    multiplier = 1 / (1 - phi) if abs(phi) < 1 else np.inf

    ax.set_title(
        f"Persistence={phi:.3f} | Half-life={half_life:.2f} | LR Multiplier={multiplier:.2f}"
    )

    ax.set_xlabel("Periods")
    ax.set_ylabel("Remaining Effect")

    ax.grid(True, alpha=0.3)

    return _save(fig, save)


def instrument_architecture_dashboard(
    lag_depths,
    instrument_counts,
    *,
    save=None,
):
    fig, ax = plt.subplots(figsize=(8, 5))

    ax.bar(
        lag_depths,
        instrument_counts,
    )

    ax.set_title("Instrument Architecture")

    ax.set_xlabel("Lag Depth")
    ax.set_ylabel("Instrument Count")

    return _save(fig, save)


def effect_surface_dashboard(
    x,
    y,
    z,
    *,
    save=None,
):
    fig, ax = plt.subplots(figsize=(8, 6))

    sc = ax.scatter(
        x,
        y,
        c=z,
    )

    plt.colorbar(sc)

    ax.set_title("Effect Surface")

    return _save(fig, save)


def publication_panel(
    metrics: HealthMetrics,
    phi: float,
    lag_depths,
    instrument_counts,
    *,
    save=None,
):
    fig = plt.figure(figsize=(12, 8))

    gs = fig.add_gridspec(2, 2)

    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])
    ax3 = fig.add_subplot(gs[1, 0])
    ax4 = fig.add_subplot(gs[1, 1])

    ax1.axis("off")

    ax1.text(
        0.05,
        0.95,
        "Model Health",
        fontsize=14,
        fontweight="bold",
    )

    ax1.text(
        0.05,
        0.75,
        f"Hansen: {metrics.hansen_p}",
    )

    ax1.text(
        0.05,
        0.65,
        f"AR(2): {metrics.ar2_p}",
    )

    t = np.arange(21)

    ax2.plot(
        t,
        phi**t,
    )

    ax2.set_title("Persistence")

    ax3.bar(
        lag_depths,
        instrument_counts,
    )

    ax3.set_title("Instrument Structure")

    ax4.axis("off")

    ax4.text(
        0.05,
        0.95,
        "systemgmmkit SGM-Viz",
        fontsize=14,
        fontweight="bold",
    )

    fig.tight_layout()

    return _save(fig, save)
