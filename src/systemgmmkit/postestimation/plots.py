from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence
import html
import math

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg", force=True)
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator


@dataclass(frozen=True)
class PlotTheme:
    style: str = "sgm"
    preset: str = "paper"
    dpi: int = 240
    font_family: str = "DejaVu Sans"

    @classmethod
    def build(
        cls,
        style: str | "PlotTheme" | None = "journal",
        preset: str = "paper",
        dpi: int | None = None,
    ) -> "PlotTheme":
        if isinstance(style, PlotTheme):
            return style

        style_value = (style or "journal").strip().lower()
        preset_value = (preset or "paper").strip().lower()

        if style_value not in {"sgm", "systemgmmkit", "stata", "journal", "dashboard"}:
            raise ValueError("style must be one of: sgm, systemgmmkit, stata, journal, dashboard")

        if preset_value not in {"paper", "slide", "dashboard", "compact"}:
            raise ValueError("preset must be one of: paper, slide, dashboard, compact")

        default_dpi = {
            "paper": 300,
            "slide": 220,
            "dashboard": 180,
            "compact": 220,
        }[preset_value]

        return cls(
            style=("sgm" if style_value == "systemgmmkit" else style_value),
            preset=preset_value,
            dpi=int(dpi or default_dpi),
        )


def available_styles() -> list[str]:
    return ["sgm", "stata", "journal", "dashboard"]


_PALETTES = {
    "sgm": {
        "primary": "#0F3D5E",
        "secondary": "#52616B",
        "accent": "#C2410C",
        "success": "#166534",
        "warning": "#B45309",
        "danger": "#B91C1C",
        "grid": "#E5E7EB",
        "band": "#DBEAFE",
        "text": "#111827",
        "spine": "#CBD5E1",
    },
    "stata": {
        "primary": "#1F4E79",
        "secondary": "#7F7F7F",
        "accent": "#B22222",
        "grid": "#D0D0D0",
        "band": "#D7E3F4",
        "text": "#1F1F1F",
        "spine": "#666666",
    },
    "journal": {
        "primary": "#1F5AA6",
        "secondary": "#444444",
        "accent": "#B33A3A",
        "grid": "#E6E6E6",
        "band": "#CBD9F5",
        "text": "#171717",
        "spine": "#303030",
    },
    "dashboard": {
        "primary": "#166534",
        "secondary": "#475569",
        "accent": "#B91C1C",
        "grid": "#E2E8F0",
        "band": "#DCFCE7",
        "text": "#0F172A",
        "spine": "#CBD5E1",
    },
}


def _theme(style: str | PlotTheme | None = "sgm", preset: str = "paper", dpi: int | None = None) -> PlotTheme:
    return PlotTheme.build(style=style, preset=preset, dpi=dpi)


def _size(kind: str, theme: PlotTheme, n: int | None = None) -> tuple[float, float]:
    base = {
        "paper": {
            "coef": (7.2, 4.6),
            "line": (7.4, 4.6),
            "resid": (6.4, 4.4),
            "square": (5.5, 5.0),
            "wide": (8.2, 4.8),
            "surface": (7.2, 5.4),
        },
        "slide": {
            "coef": (9.5, 5.8),
            "line": (9.5, 5.7),
            "resid": (8.0, 5.2),
            "square": (6.4, 5.8),
            "wide": (10.5, 5.8),
            "surface": (8.5, 6.2),
        },
        "dashboard": {
            "coef": (8.2, 5.0),
            "line": (8.6, 5.0),
            "resid": (7.2, 4.7),
            "square": (6.1, 5.4),
            "wide": (9.5, 5.2),
            "surface": (8.0, 5.8),
        },
        "compact": {
            "coef": (6.2, 3.8),
            "line": (6.2, 3.8),
            "resid": (5.8, 3.8),
            "square": (4.8, 4.4),
            "wide": (7.0, 3.8),
            "surface": (6.2, 4.8),
        },
    }[theme.preset]

    w, h = base[kind]

    if kind == "coef" and n:
        h = max(h, 1.25 + 0.36 * n)

    return w, h


def _apply_theme(ax: plt.Axes, theme: PlotTheme, title: str | None = None, subtitle: str | None = None) -> None:
    p = _PALETTES[theme.style]

    plt.rcParams.update({
        "font.family": theme.font_family,
        "axes.titlesize": 10.5,
        "axes.labelsize": 9.5,
        "xtick.labelsize": 8.5,
        "ytick.labelsize": 8.5,
        "legend.fontsize": 8.5,
    })

    ax.set_facecolor("white")
    ax.figure.set_facecolor("white")

    ax.tick_params(axis="both", colors=p["text"], labelsize=8.5)
    ax.xaxis.label.set_color(p["text"])
    ax.yaxis.label.set_color(p["text"])

    if theme.style == "sgm":
        ax.grid(True, axis="y", linestyle="-", linewidth=0.65, color=p["grid"], alpha=0.85)
        ax.grid(True, axis="x", linestyle=":", linewidth=0.45, color=p["grid"], alpha=0.55)
        for side in ["top", "right"]:
            ax.spines[side].set_visible(False)
        for side in ["left", "bottom"]:
            ax.spines[side].set_color(p["spine"])
            ax.spines[side].set_linewidth(0.8)

    elif theme.style == "stata":
        ax.grid(True, axis="x", linestyle=":", linewidth=0.85, color=p["grid"], alpha=0.9)
        ax.grid(False, axis="y")
        for spine in ax.spines.values():
            spine.set_color(p["spine"])
            spine.set_linewidth(0.8)

    elif theme.style == "journal":
        ax.grid(True, axis="both", linestyle="-", linewidth=0.55, color=p["grid"], alpha=0.75)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color(p["spine"])
        ax.spines["bottom"].set_color(p["spine"])
        ax.spines["left"].set_linewidth(0.8)
        ax.spines["bottom"].set_linewidth(0.8)

    elif theme.style == "dashboard":
        ax.grid(True, axis="y", linestyle="-", linewidth=0.7, color=p["grid"], alpha=0.85)
        ax.grid(False, axis="x")
        for side in ["top", "right"]:
            ax.spines[side].set_visible(False)
        for side in ["left", "bottom"]:
            ax.spines[side].set_color(p["spine"])
            ax.spines[side].set_linewidth(0.8)

    # Use explicit axes-level text instead of ax.set_title().
    # This prevents title/subtitle collision across all exported plots.
    if title:
        ax.text(
            0.0,
            1.125,
            title,
            transform=ax.transAxes,
            fontsize=13.0 if theme.preset != "compact" else 11.0,
            fontweight="bold",
            color=p["text"],
            ha="left",
            va="bottom",
            clip_on=False,
        )

    if subtitle:
        ax.text(
            0.0,
            1.065,
            subtitle,
            transform=ax.transAxes,
            fontsize=9.2 if theme.preset != "compact" else 8.2,
            color=p["secondary"],
            ha="left",
            va="bottom",
            clip_on=False,
        )

def _save(fig: plt.Figure, save: str | Path | None, theme: PlotTheme) -> plt.Figure:
    if save is not None:
        path = Path(save)
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, bbox_inches="tight", dpi=theme.dpi)
    return fig


def _attr(result: Any, names: Sequence[str], default: Any = None) -> Any:
    if result is None:
        return default

    for name in names:
        if isinstance(result, Mapping) and name in result:
            return result[name]
        if hasattr(result, name):
            return getattr(result, name)

    return default


def _series(obj: Any, names: Sequence[str] | None = None) -> pd.Series:
    if obj is None:
        return pd.Series(dtype=float)

    if isinstance(obj, pd.Series):
        return obj.astype(float)

    if isinstance(obj, pd.DataFrame):
        if obj.shape[1] == 1:
            return obj.iloc[:, 0].astype(float)
        raise ValueError("Expected a one-column DataFrame.")

    if isinstance(obj, Mapping):
        return pd.Series(obj, dtype=float)

    arr = np.asarray(obj, dtype=float).ravel()
    idx = list(names) if names is not None else [f"x{i}" for i in range(len(arr))]
    return pd.Series(arr, index=idx, dtype=float)


def _params(result: Any) -> pd.Series:
    obj = _attr(result, ["params", "coef", "coefficients", "coefs"])
    if obj is None:
        raise ValueError("Could not extract coefficients. Expected params, coef, coefficients, or coefs.")
    return _series(obj)


def _ses(result: Any, index: Sequence[str]) -> pd.Series:
    obj = _attr(result, ["std_errors", "standard_errors", "bse", "se", "stderr"])
    if obj is None:
        return pd.Series(np.full(len(index), np.nan), index=index)
    return _series(obj, names=index).reindex(index)


def _ci(result: Any, level: float = 0.95) -> pd.DataFrame:
    b = _params(result)
    se = _ses(result, b.index)
    z = 1.959963984540054

    return pd.DataFrame({
        "term": b.index.astype(str),
        "estimate": b.values,
        "std_error": se.values,
        "ci_low": b.values - z * se.values,
        "ci_high": b.values + z * se.values,
    })


def _safe_float_array(values: Any) -> np.ndarray:
    arr = np.asarray(values, dtype=float).ravel()
    return arr[np.isfinite(arr)]


def _clean_label(value: Any) -> str:
    return str(value).replace("_", " ")


def coefficient_plot(
    result: Any,
    *,
    terms: Sequence[str] | None = None,
    drop_constant: bool = True,
    level: float = 0.95,
    style: str | PlotTheme = "sgm",
    preset: str = "paper",
    title: str = "Parameter impact plot",
    subtitle: str | None = None,
    save: str | Path | None = None,
) -> plt.Figure:
    th = _theme(style, preset)
    p = _PALETTES[th.style]

    df = _ci(result, level)

    if drop_constant:
        df = df[~df["term"].isin(["_cons", "_con", "const", "constant", "Intercept"])]

    if terms is not None:
        df = df[df["term"].isin(list(terms))]

    if df.empty:
        raise ValueError("No coefficients available for plotting.")

    df = df.iloc[::-1].reset_index(drop=True)

    fig, ax = plt.subplots(figsize=_size("coef", th, len(df)))

    y = np.arange(len(df))
    xerr = np.vstack([
        df["estimate"].to_numpy() - df["ci_low"].to_numpy(),
        df["ci_high"].to_numpy() - df["estimate"].to_numpy(),
    ])

    ax.errorbar(
        df["estimate"],
        y,
        xerr=xerr,
        fmt="o",
        color=p["primary"],
        ecolor=p["primary"],
        elinewidth=1.4,
        capsize=3,
        markersize=4.5,
        markeredgecolor="white",
        markeredgewidth=0.7,
    )

    ax.axvline(0, linestyle="--", linewidth=1.0, color=p["accent"], alpha=0.65)
    ax.set_yticks(y)
    ax.set_yticklabels([_clean_label(t) for t in df["term"]])
    ax.set_xlabel(f"Estimate ({int(level * 100)}% CI)")

    _apply_theme(ax, th, title, subtitle or "Dot-whisker coefficient estimates with confidence intervals.")
    fig.tight_layout()
    return _save(fig, save, th)


def marginal_effects_plot(
    effects: Any,
    *,
    term_col: str = "term",
    effect_col: str = "effect",
    se_col: str = "std_error",
    level: float = 0.95,
    style: str | PlotTheme = "sgm",
    preset: str = "paper",
    title: str = "Marginal response plot",
    subtitle: str | None = None,
    save: str | Path | None = None,
) -> plt.Figure:
    th = _theme(style, preset)
    p = _PALETTES[th.style]

    df = pd.DataFrame(effects).copy()

    if term_col not in df or effect_col not in df:
        raise ValueError(f"effects must contain '{term_col}' and '{effect_col}'.")

    z = 1.959963984540054

    if se_col in df:
        df["ci_low"] = df[effect_col] - z * df[se_col]
        df["ci_high"] = df[effect_col] + z * df[se_col]
    else:
        df["ci_low"] = df[effect_col]
        df["ci_high"] = df[effect_col]

    df = df.iloc[::-1].reset_index(drop=True)

    fig, ax = plt.subplots(figsize=_size("coef", th, len(df)))

    y = np.arange(len(df))
    xerr = np.vstack([
        df[effect_col].to_numpy() - df["ci_low"].to_numpy(),
        df["ci_high"].to_numpy() - df[effect_col].to_numpy(),
    ])

    ax.errorbar(
        df[effect_col],
        y,
        xerr=xerr,
        fmt="o",
        color=p["primary"],
        ecolor=p["primary"],
        elinewidth=1.4,
        capsize=3,
        markersize=4.5,
        markeredgecolor="white",
        markeredgewidth=0.7,
    )

    ax.axvline(0, linestyle="--", linewidth=1.0, color=p["accent"], alpha=0.65)
    ax.set_yticks(y)
    ax.set_yticklabels([_clean_label(t) for t in df[term_col]])
    ax.set_xlabel(f"Average marginal effect dy/dx ({int(level * 100)}% CI)")

    _apply_theme(ax, th, title, subtitle or "Average marginal effects with confidence intervals.")
    fig.tight_layout()
    return _save(fig, save, th)


def margins_prediction_plot(
    data: Any,
    *,
    x: str,
    y: str,
    lower: str | None = None,
    upper: str | None = None,
    group: str | None = None,
    style: str | PlotTheme = "sgm",
    preset: str = "paper",
    title: str = "Prediction path plot",
    subtitle: str | None = None,
    xlabel: str | None = None,
    ylabel: str = "Predicted outcome",
    save: str | Path | None = None,
) -> plt.Figure:
    th = _theme(style, preset)
    p = _PALETTES[th.style]
    df = pd.DataFrame(data).copy()

    if x not in df or y not in df:
        raise ValueError(f"data must contain '{x}' and '{y}'.")

    fig, ax = plt.subplots(figsize=_size("line", th))

    line_styles = ["-", "--", "-.", ":"]
    markers = ["o", "s", "^", "D"]

    if group and group in df:
        for i, (key, g) in enumerate(df.groupby(group, sort=False)):
            g = g.sort_values(x)
            ax.plot(
                g[x],
                g[y],
                linewidth=2.0,
                linestyle=line_styles[i % len(line_styles)],
                marker=markers[i % len(markers)] if len(g) <= 12 else None,
                markersize=3.8,
                label=str(key),
            )
            if lower and upper and lower in g and upper in g:
                ax.fill_between(
                    g[x].to_numpy(),
                    g[lower].to_numpy(),
                    g[upper].to_numpy(),
                    color=p["primary"],
                    alpha=0.10,
                )
        ax.legend(frameon=False, loc="best")
    else:
        df = df.sort_values(x)
        ax.plot(df[x], df[y], linewidth=2.2, color=p["primary"])
        if lower and upper and lower in df and upper in df:
            ax.fill_between(
                df[x].to_numpy(),
                df[lower].to_numpy(),
                df[upper].to_numpy(),
                color=p["band"],
                alpha=0.55,
            )

    ax.set_xlabel(xlabel or _clean_label(x))
    ax.set_ylabel(ylabel)
    ax.xaxis.set_major_locator(MaxNLocator(nbins=6))

    _apply_theme(ax, th, title, subtitle or "Predictive margins with optional confidence intervals.")
    fig.tight_layout()
    return _save(fig, save, th)


def interaction_plot(
    data: Any,
    *,
    x: str,
    y: str,
    moderator: str,
    lower: str | None = None,
    upper: str | None = None,
    style: str | PlotTheme = "sgm",
    preset: str = "paper",
    title: str = "Interaction response plot",
    subtitle: str | None = None,
    save: str | Path | None = None,
) -> plt.Figure:
    return margins_prediction_plot(
        data,
        x=x,
        y=y,
        lower=lower,
        upper=upper,
        group=moderator,
        style=style,
        preset=preset,
        title=title,
        subtitle=subtitle or f"Predicted outcome across {_clean_label(x)} by {_clean_label(moderator)}.",
        ylabel="Predicted outcome",
        save=save,
    )


def conditional_effects_plot(
    data: Any,
    *,
    x: str,
    effect: str,
    condition: str,
    lower: str | None = None,
    upper: str | None = None,
    style: str | PlotTheme = "sgm",
    preset: str = "paper",
    title: str = "Conditional effect path",
    subtitle: str | None = None,
    save: str | Path | None = None,
) -> plt.Figure:
    return margins_prediction_plot(
        data,
        x=x,
        y=effect,
        lower=lower,
        upper=upper,
        group=condition,
        style=style,
        preset=preset,
        title=title,
        subtitle=subtitle or f"Marginal effect across {_clean_label(x)} by {_clean_label(condition)}.",
        ylabel="Marginal effect",
        save=save,
    )


def residuals_vs_fitted_plot(
    result: Any | None = None,
    *,
    fitted: Sequence[float] | None = None,
    residuals: Sequence[float] | None = None,
    style: str | PlotTheme = "sgm",
    preset: str = "paper",
    title: str = "Model fit residual map",
    subtitle: str | None = None,
    save: str | Path | None = None,
) -> plt.Figure:
    th = _theme(style, preset)
    p = _PALETTES[th.style]

    if fitted is None:
        fitted = _attr(result, ["fittedvalues", "fitted_values", "fitted"])
    if residuals is None:
        residuals = _attr(result, ["resid", "residuals", "errors"])

    if fitted is None or residuals is None:
        raise ValueError("Provide fitted and residuals, or a result object exposing them.")

    fitted_arr = np.asarray(fitted, dtype=float).ravel()
    resid_arr = np.asarray(residuals, dtype=float).ravel()
    mask = np.isfinite(fitted_arr) & np.isfinite(resid_arr)

    fitted_arr = fitted_arr[mask]
    resid_arr = resid_arr[mask]

    fig, ax = plt.subplots(figsize=_size("resid", th))
    ax.scatter(fitted_arr, resid_arr, s=17, alpha=0.70, color=p["primary"], edgecolor="white", linewidth=0.25)
    ax.axhline(0, linestyle="--", linewidth=1.0, color=p["accent"], alpha=0.75)

    if len(fitted_arr) >= 15:
        order = np.argsort(fitted_arr)
        window = max(7, int(len(fitted_arr) * 0.12))
        smooth = pd.Series(resid_arr[order]).rolling(window, center=True, min_periods=4).mean()
        ax.plot(fitted_arr[order], smooth, linewidth=1.6, color=p["accent"], alpha=0.9)

    ax.set_xlabel("Fitted values")
    ax.set_ylabel("Residuals")

    _apply_theme(ax, th, title, subtitle or "Checks residual structure and possible nonlinearity.")
    fig.tight_layout()
    return _save(fig, save, th)


def qq_residual_plot(
    residuals: Sequence[float],
    *,
    style: str | PlotTheme = "sgm",
    preset: str = "paper",
    title: str = "Residual distribution check",
    subtitle: str | None = None,
    save: str | Path | None = None,
) -> plt.Figure:
    th = _theme(style, preset)
    p = _PALETTES[th.style]

    r = _safe_float_array(residuals)
    if len(r) < 3:
        raise ValueError("At least 3 residuals are required.")

    try:
        from scipy import stats
        theoretical = stats.norm.ppf((np.arange(1, len(r) + 1) - 0.5) / len(r))
    except Exception:
        theoretical = np.linspace(-2.6, 2.6, len(r))

    sample = np.sort((r - np.mean(r)) / np.std(r, ddof=1))

    fig, ax = plt.subplots(figsize=_size("square", th))
    ax.scatter(theoretical, sample, s=17, alpha=0.75, color=p["primary"], edgecolor="white", linewidth=0.25)

    lo = min(theoretical.min(), sample.min())
    hi = max(theoretical.max(), sample.max())
    ax.plot([lo, hi], [lo, hi], linewidth=1.1, color=p["accent"], alpha=0.75)

    ax.set_xlabel("Theoretical quantiles")
    ax.set_ylabel("Sample quantiles")

    _apply_theme(ax, th, title, subtitle or "Compares standardized residual quantiles against normal quantiles.")
    fig.tight_layout()
    return _save(fig, save, th)


def residual_histogram(
    residuals: Sequence[float],
    *,
    bins: int = 30,
    density: bool = True,
    style: str | PlotTheme = "sgm",
    preset: str = "paper",
    title: str = "Residual density profile",
    subtitle: str | None = None,
    save: str | Path | None = None,
) -> plt.Figure:
    th = _theme(style, preset)
    p = _PALETTES[th.style]
    r = _safe_float_array(residuals)

    fig, ax = plt.subplots(figsize=_size("resid", th))
    ax.hist(r, bins=bins, density=density, color=p["primary"], alpha=0.72, edgecolor="white", linewidth=0.5)

    if len(r) > 2 and np.std(r, ddof=1) > 0:
        xs = np.linspace(r.min(), r.max(), 250)
        mu = r.mean()
        sd = r.std(ddof=1)
        ys = (1 / (sd * math.sqrt(2 * math.pi))) * np.exp(-0.5 * ((xs - mu) / sd) ** 2)
        if density:
            ax.plot(xs, ys, linewidth=1.7, color=p["accent"], alpha=0.9)

    ax.set_xlabel("Residuals")
    ax.set_ylabel("Density" if density else "Frequency")

    _apply_theme(ax, th, title, subtitle or "Distribution of residuals with normal-density overlay.")
    fig.tight_layout()
    return _save(fig, save, th)


def fixed_effects_plot(
    effects: Any,
    *,
    entity_col: str = "entity",
    effect_col: str = "effect",
    se_col: str | None = "std_error",
    style: str | PlotTheme = "sgm",
    preset: str = "paper",
    title: str = "Unit effect profile",
    subtitle: str | None = None,
    save: str | Path | None = None,
) -> plt.Figure:
    th = _theme(style, preset)
    p = _PALETTES[th.style]

    df = pd.DataFrame(effects).copy()

    if entity_col not in df or effect_col not in df:
        raise ValueError(f"effects must contain '{entity_col}' and '{effect_col}'.")

    df = df.sort_values(effect_col).reset_index(drop=True)

    fig, ax = plt.subplots(figsize=_size("coef", th, len(df)))
    y = np.arange(len(df))

    if se_col and se_col in df:
        z = 1.959963984540054
        ax.errorbar(
            df[effect_col],
            y,
            xerr=z * df[se_col].to_numpy(),
            fmt="o",
            color=p["primary"],
            ecolor=p["primary"],
            capsize=3,
            elinewidth=1.3,
            markersize=4.2,
            markeredgecolor="white",
            markeredgewidth=0.7,
        )
    else:
        ax.scatter(df[effect_col], y, s=22, color=p["primary"])

    ax.axvline(0, linestyle="--", linewidth=1.0, color=p["accent"], alpha=0.7)
    ax.set_yticks(y)
    ax.set_yticklabels([_clean_label(v) for v in df[entity_col]])
    ax.set_xlabel("Fixed effect")

    _apply_theme(ax, th, title, subtitle or "Estimated unit fixed effects with optional confidence intervals.")
    fig.tight_layout()
    return _save(fig, save, th)


def panel_spaghetti_plot(
    data: Any,
    *,
    entity: str,
    time: str,
    y: str,
    highlight: Sequence[Any] | None = None,
    style: str | PlotTheme = "sgm",
    preset: str = "paper",
    title: str = "Panel trajectory map",
    subtitle: str | None = None,
    save: str | Path | None = None,
) -> plt.Figure:
    th = _theme(style, preset)
    p = _PALETTES[th.style]

    df = pd.DataFrame(data).copy()
    for col in [entity, time, y]:
        if col not in df:
            raise ValueError(f"data must contain '{col}'.")

    highlight_set = set(highlight or [])

    fig, ax = plt.subplots(figsize=_size("wide", th))

    for key, g in df.groupby(entity, sort=False):
        g = g.sort_values(time)
        if key in highlight_set:
            ax.plot(g[time], g[y], linewidth=2.1, label=str(key))
        else:
            ax.plot(g[time], g[y], linewidth=0.75, alpha=0.22, color=p["secondary"])

    if highlight_set:
        ax.legend(frameon=False, loc="best")

    ax.set_xlabel(_clean_label(time))
    ax.set_ylabel(_clean_label(y))
    ax.xaxis.set_major_locator(MaxNLocator(nbins=7))

    _apply_theme(ax, th, title, subtitle or "Panel trajectories over time with selected units highlighted.")
    fig.tight_layout()
    return _save(fig, save, th)


def instrument_count_plot(
    data: Any,
    *,
    lag_col: str = "lag",
    count_col: str = "instruments",
    style: str | PlotTheme = "sgm",
    preset: str = "paper",
    title: str = "Instrument architecture plot",
    subtitle: str | None = None,
    save: str | Path | None = None,
) -> plt.Figure:
    th = _theme(style, preset)
    p = _PALETTES[th.style]

    df = pd.DataFrame(data).copy()

    if lag_col not in df or count_col not in df:
        raise ValueError(f"data must contain '{lag_col}' and '{count_col}'.")

    df = df.sort_values(lag_col)

    fig, ax = plt.subplots(figsize=_size("resid", th))
    ax.plot(
        df[lag_col],
        df[count_col],
        marker="o",
        linewidth=2.0,
        markersize=4.8,
        color=p["primary"],
        markeredgecolor="white",
        markeredgewidth=0.7,
    )

    ax.set_xlabel("Lag depth")
    ax.set_ylabel("Number of instruments")
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))

    _apply_theme(ax, th, title, subtitle or "Instrument growth by lag depth.")
    fig.tight_layout()
    return _save(fig, save, th)


def hansen_ar_diagnostic_plot(
    diagnostics: Mapping[str, float] | Any,
    *,
    style: str | PlotTheme = "sgm",
    preset: str = "paper",
    title: str = "Model health panel",
    subtitle: str | None = None,
    save: str | Path | None = None,
) -> plt.Figure:
    th = _theme(style, preset)
    p = _PALETTES[th.style]

    if not isinstance(diagnostics, Mapping):
        diagnostics = {
            "Hansen": _attr(diagnostics, ["hansen_p", "hansen_p_value"]),
            "Sargan": _attr(diagnostics, ["sargan_p", "sargan_p_value"]),
            "AR(1)": _attr(diagnostics, ["ar1_p", "ar1_p_value"]),
            "AR(2)": _attr(diagnostics, ["ar2_p", "ar2_p_value"]),
        }

    labels: list[str] = []
    vals: list[float] = []

    for k, v in diagnostics.items():
        if v is not None and np.isfinite(float(v)):
            labels.append(str(k))
            vals.append(float(v))

    if not vals:
        raise ValueError("No valid diagnostic p-values supplied.")

    colors = [p["accent"] if value < 0.05 else p["primary"] for value in vals]

    fig, ax = plt.subplots(figsize=_size("resid", th))
    ax.bar(labels, vals, color=colors, alpha=0.82, edgecolor="white", linewidth=0.7)
    ax.axhline(0.05, linestyle="--", linewidth=1.1, color=p["accent"], alpha=0.80)

    for i, value in enumerate(vals):
        ax.text(i, min(value + 0.03, 0.97), f"{value:.3f}", ha="center", va="bottom", fontsize=8.3, color=p["text"])

    ax.set_ylim(0, 1)
    ax.set_ylabel("p-value")

    _apply_theme(ax, th, title, subtitle or "Values below 0.05 are visually flagged.")
    fig.tight_layout()
    return _save(fig, save, th)


def counterfactual_scenario_plot(
    data: Any,
    *,
    time: str,
    y: str,
    scenario: str,
    style: str | PlotTheme = "sgm",
    preset: str = "paper",
    title: str = "Scenario response path",
    subtitle: str | None = None,
    save: str | Path | None = None,
) -> plt.Figure:
    return margins_prediction_plot(
        data,
        x=time,
        y=y,
        group=scenario,
        style=style,
        preset=preset,
        title=title,
        subtitle=subtitle or "Predicted outcome under alternative scenarios.",
        ylabel=_clean_label(y),
        save=save,
    )


def surface_3d_plot(
    data: Any,
    *,
    x: str,
    y: str,
    z: str,
    style: str | PlotTheme = "sgm",
    preset: str = "paper",
    title: str = "Effect surface",
    save: str | Path | None = None,
) -> plt.Figure:
    th = _theme(style, preset)
    p = _PALETTES[th.style]

    df = pd.DataFrame(data).copy()

    for col in [x, y, z]:
        if col not in df:
            raise ValueError(f"data must contain '{col}'.")

    fig = plt.figure(figsize=_size("surface", th))
    ax = fig.add_subplot(111, projection="3d")

    xs = df[x].to_numpy(dtype=float)
    ys = df[y].to_numpy(dtype=float)
    zs = df[z].to_numpy(dtype=float)

    try:
        surf = ax.plot_trisurf(xs, ys, zs, cmap="viridis", linewidth=0.12, antialiased=True, alpha=0.94)
        fig.colorbar(surf, ax=ax, shrink=0.65, pad=0.1)
    except Exception:
        ax.scatter(xs, ys, zs, s=14, alpha=0.78, color=p["primary"])

    ax.set_xlabel(_clean_label(x))
    ax.set_ylabel(_clean_label(y))
    ax.set_zlabel(_clean_label(z))
    ax.set_title(title, fontsize=11.5, fontweight="bold", color=p["text"], pad=12)

    fig.tight_layout()
    return _save(fig, save, th)




def model_health_panel(
    diagnostics: Mapping[str, float] | Any,
    *,
    style: str | PlotTheme = "sgm",
    preset: str = "paper",
    title: str = "Model health panel",
    subtitle: str | None = None,
    save: str | Path | None = None,
) -> plt.Figure:
    """
    SGM-Viz wrapper for GMM model health diagnostics.

    Combines Hansen/Sargan overidentification and AR serial-correlation
    diagnostics into one reviewer-friendly diagnostic panel.
    """
    return hansen_ar_diagnostic_plot(
        diagnostics,
        style=style,
        preset=preset,
        title=title,
        subtitle=subtitle or "Overidentification and serial-correlation p-values with weak-test flags.",
        save=save,
    )


def parameter_impact_plot(
    result: Any,
    *,
    terms: Sequence[str] | None = None,
    drop_constant: bool = True,
    level: float = 0.95,
    style: str | PlotTheme = "sgm",
    preset: str = "paper",
    title: str = "Parameter impact plot",
    subtitle: str | None = None,
    save: str | Path | None = None,
) -> plt.Figure:
    """
    SGM-Viz branded coefficient plot.
    """
    return coefficient_plot(
        result,
        terms=terms,
        drop_constant=drop_constant,
        level=level,
        style=style,
        preset=preset,
        title=title,
        subtitle=subtitle,
        save=save,
    )


def effect_surface_plot(
    data: Any,
    *,
    x: str,
    y: str,
    z: str,
    style: str | PlotTheme = "sgm",
    preset: str = "paper",
    title: str = "Effect surface",
    save: str | Path | None = None,
) -> plt.Figure:
    """
    SGM-Viz branded surface plot for interaction and nonlinear effects.
    """
    return surface_3d_plot(
        data,
        x=x,
        y=y,
        z=z,
        style=style,
        preset=preset,
        title=title,
        save=save,
    )


def instrument_architecture_plot(
    data: Any,
    *,
    lag_col: str = "lag",
    count_col: str = "instruments",
    style: str | PlotTheme = "sgm",
    preset: str = "paper",
    title: str = "Instrument architecture plot",
    subtitle: str | None = None,
    save: str | Path | None = None,
) -> plt.Figure:
    """
    SGM-Viz branded instrument-count plot.

    Designed for dynamic panel GMM workflows where reviewers care about
    lag depth, instrument proliferation, and instrument discipline.
    """
    return instrument_count_plot(
        data,
        lag_col=lag_col,
        count_col=count_col,
        style=style,
        preset=preset,
        title=title,
        subtitle=subtitle or "Instrument growth by lag depth for dynamic panel GMM.",
        save=save,
    )


def dynamic_persistence_plot(
    phi: float,
    *,
    periods: int = 20,
    shock: float = 1.0,
    style: str | PlotTheme = "sgm",
    preset: str = "paper",
    title: str = "Dynamic persistence path",
    save: str | Path | None = None,
) -> plt.Figure:
    """
    Plot the persistence path implied by a lagged dependent-variable coefficient.

    Parameters
    ----------
    phi:
        Estimated persistence coefficient, usually coefficient on L.y.
    periods:
        Number of periods after a unit shock.
    shock:
        Initial shock size.
    """
    th = _theme(style, preset)
    p = _PALETTES[th.style]

    if periods < 1:
        raise ValueError("periods must be >= 1")

    t = np.arange(0, periods + 1)
    response = shock * (float(phi) ** t)

    fig, ax = plt.subplots(figsize=_size("line", th))
    ax.plot(
        t,
        response,
        linewidth=2.2,
        marker="o" if periods <= 20 else None,
        color=p["primary"],
        markeredgecolor="white",
        markeredgewidth=0.7,
    )
    ax.axhline(0, linestyle="--", linewidth=1.0, color=p["secondary"], alpha=0.65)

    half_life = None
    if 0 < abs(float(phi)) < 1:
        half_life = math.log(0.5) / math.log(abs(float(phi)))
        if np.isfinite(half_life) and 0 <= half_life <= periods:
            ax.axvline(half_life, linestyle=":", linewidth=1.2, color=p["accent"], alpha=0.85)
            ax.text(
                half_life,
                max(response) * 0.55 if len(response) else 0,
                f"half-life ≈ {half_life:.2f}",
                rotation=90,
                va="center",
                ha="right",
                fontsize=8.5,
                color=p["accent"],
            )

    ax.set_xlabel("Periods after shock")
    ax.set_ylabel("Remaining effect")
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))

    subtitle = f"Shock decay implied by persistence coefficient phi = {float(phi):.3f}."
    _apply_theme(ax, th, title, subtitle)
    fig.tight_layout()
    return _save(fig, save, th)


def sgm_plot_bundle(
    result: Any,
    *,
    output_dir: str | Path,
    prefix: str = "model",
    style: str | PlotTheme = "sgm",
    preset: str = "paper",
) -> dict[str, Path]:
    """
    One-command SGM-Viz export bundle for handoff.

    Exports available model plots without failing the full workflow when
    a particular result object does not expose a required attribute.
    """
    return plot_all_diagnostics(
        result,
        output_dir=output_dir,
        style=style,
        preset=preset,
        prefix=prefix,
    )

def plot_all_diagnostics(
    result: Any,
    *,
    output_dir: str | Path,
    style: str | PlotTheme = "sgm",
    preset: str = "paper",
    prefix: str = "model",
) -> dict[str, Path]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    saved: dict[str, Path] = {}

    def attempt(name: str, fn: Any) -> None:
        path = out / f"{prefix}_{name}.png"
        try:
            fig = fn(path)
            plt.close(fig)
            saved[name] = path
        except Exception:
            pass

    attempt("coefplot", lambda path: coefficient_plot(result, style=style, preset=preset, save=path))

    fitted = _attr(result, ["fittedvalues", "fitted_values", "fitted"])
    residuals = _attr(result, ["resid", "residuals", "errors"])

    if fitted is not None and residuals is not None:
        attempt("residuals_vs_fitted", lambda path: residuals_vs_fitted_plot(result, style=style, preset=preset, save=path))

    if residuals is not None:
        attempt("qq_residuals", lambda path: qq_residual_plot(residuals, style=style, preset=preset, save=path))
        attempt("residual_histogram", lambda path: residual_histogram(residuals, style=style, preset=preset, save=path))

    diagnostics = {
        "Hansen": _attr(result, ["hansen_p", "hansen_p_value"]),
        "Sargan": _attr(result, ["sargan_p", "sargan_p_value"]),
        "AR(1)": _attr(result, ["ar1_p", "ar1_p_value"]),
        "AR(2)": _attr(result, ["ar2_p", "ar2_p_value"]),
    }

    if any(v is not None for v in diagnostics.values()):
        attempt("hansen_ar", lambda path: hansen_ar_diagnostic_plot(diagnostics, style=style, preset=preset, save=path))

    return saved


def export_postestimation_gallery(
    figures: Mapping[str, str | Path],
    *,
    output_html: str | Path,
    title: str = "Post-estimation graphics gallery",
    description: str = "Generated by systemgmmkit.",
) -> Path:
    output = Path(output_html)
    output.parent.mkdir(parents=True, exist_ok=True)

    cards = []
    for name, path in figures.items():
        p = Path(path)
        rel = p.name if p.parent == output.parent else str(p)
        cards.append(
            f"""
            <section class="card">
              <h2>{html.escape(str(name).replace("_", " ").title())}</h2>
              <img src="{html.escape(rel)}" alt="{html.escape(str(name))}">
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
  --text: #0f172a;
  --muted: #475569;
  --border: #e2e8f0;
}}
body {{
  margin: 0;
  font-family: Inter, Arial, sans-serif;
  background: var(--bg);
  color: var(--text);
}}
header {{
  padding: 32px 36px 18px 36px;
}}
h1 {{
  margin: 0 0 6px 0;
  font-size: 28px;
  letter-spacing: -0.03em;
}}
p {{
  margin: 0;
  color: var(--muted);
}}
.grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(420px, 1fr));
  gap: 18px;
  padding: 18px 36px 36px 36px;
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
  color: var(--text);
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
