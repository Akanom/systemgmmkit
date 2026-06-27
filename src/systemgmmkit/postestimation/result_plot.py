from __future__ import annotations

import contextlib
import importlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np

from .sgm_viz_v2 import (
    HealthMetrics,
    InstrumentArchitecture,
    dynamic_persistence_dashboard_v2,
    effect_surface_dashboard_v2,
    export_sgm_viz_v2_gallery,
    instrument_architecture_dashboard_v2,
    model_health_dashboard_v2,
    publication_panel_v2,
)
from .standard_gallery import export_standard_postestimation_gallery


def _get(obj: Any, names: Sequence[str], default: Any = None) -> Any:
    if obj is None:
        return default
    for name in names:
        if isinstance(obj, Mapping) and name in obj:
            return obj[name]
        if hasattr(obj, name):
            return getattr(obj, name)
    return default


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except Exception:
        return None


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        out = float(value)
    except Exception:
        return None
    if not np.isfinite(out):
        return None
    return out


def _optional_bool(value: Any) -> bool | None:
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


def _safe_estimator_name(result: Any) -> str:
    value = _get(
        result,
        [
            "estimator",
            "estimator_name",
            "model_name",
            "method",
            "covariance_type",
            "model_type",
        ],
    )
    if value is None:
        return result.__class__.__name__ if result is not None else "Model"
    return str(value)


def extract_health_metrics(
    result: Any,
    *,
    estimator: str | None = None,
    collapsed: bool | None = None,
    transformation: str | None = None,
    covariance_type: str | None = None,
) -> HealthMetrics:
    params = _get(result, ["params", "coef", "coefficients", "coefs"])

    try:
        n_params = len(params) if params is not None else None
    except Exception:
        n_params = None

    return HealthMetrics(
        estimator=estimator or _safe_estimator_name(result),
        nobs=_optional_int(_get(result, ["nobs", "n_obs", "observations", "n"])),
        groups=_optional_int(_get(result, ["groups", "n_groups", "entities", "n_entities"])),
        instruments=_optional_int(
            _get(result, ["instruments", "n_instruments", "instrument_count", "j_instruments"])
        ),
        parameters=_optional_int(_get(result, ["parameters", "n_params", "k_params"], n_params)),
        collapsed=collapsed
        if collapsed is not None
        else _optional_bool(_get(result, ["collapsed", "collapse"])),
        transformation=transformation or _get(result, ["transformation", "transform"], None),
        covariance_type=covariance_type or _get(result, ["covariance_type", "cov_type"], None),
        hansen_p=_optional_float(_get(result, ["hansen_p", "hansen_p_value", "hansen"])),
        sargan_p=_optional_float(_get(result, ["sargan_p", "sargan_p_value", "sargan"])),
        ar1_stat=_optional_float(_get(result, ["ar1_stat", "ar1_z", "ar1"])),
        ar1_p=_optional_float(_get(result, ["ar1_p", "ar1_p_value"])),
        ar2_stat=_optional_float(_get(result, ["ar2_stat", "ar2_z", "ar2"])),
        ar2_p=_optional_float(_get(result, ["ar2_p", "ar2_p_value"])),
    )


def _params_as_mapping(result: Any) -> dict[str, float]:
    params = _get(result, ["params", "coef", "coefficients", "coefs"])
    if params is None:
        return {}

    if isinstance(params, Mapping):
        return {str(k): float(v) for k, v in params.items() if _optional_float(v) is not None}

    if hasattr(params, "index") and hasattr(params, "values"):
        out: dict[str, float] = {}
        for key, value in zip(params.index, params.values):
            v = _optional_float(value)
            if v is not None:
                out[str(key)] = v
        return out

    try:
        arr = np.asarray(params, dtype=float).ravel()
    except Exception:
        return {}

    return {f"x{i}": float(v) for i, v in enumerate(arr) if np.isfinite(v)}


def infer_persistence_phi(result: Any, *, default: float = 0.5) -> float:
    params = _params_as_mapping(result)

    preferred_patterns = [
        "l1.",
        "l.",
        "lag",
        "lagged",
        "L1.",
    ]

    for pattern in preferred_patterns:
        for term, value in params.items():
            lower = term.lower().replace(" ", "")
            if (pattern.lower() in lower or lower.startswith(pattern.lower())) and np.isfinite(
                value
            ):
                return float(value)

    return float(default)


def extract_instrument_architecture(
    result: Any | None = None,
    *,
    estimator: str | None = None,
    difference_equation: Sequence[str] | None = None,
    level_equation: Sequence[str] | None = None,
    standard_instruments: Sequence[str] | None = None,
    lag_range: tuple[int, int] | None = None,
    collapsed: bool | None = None,
    transformation: str | None = None,
    total_instruments: int | None = None,
    groups: int | None = None,
) -> InstrumentArchitecture:
    spec = _get(result, ["spec", "model_spec", "gmm_spec"], None)

    diff = difference_equation
    lev = level_equation
    standard = standard_instruments

    if diff is None:
        diff = _get(result, ["difference_equation_instruments", "diff_instruments"], None)
    if lev is None:
        lev = _get(result, ["level_equation_instruments", "level_instruments"], None)
    if standard is None:
        standard = _get(result, ["standard_instruments", "iv_instruments", "iv"], None)

    if diff is None and spec is not None:
        diff = _get(spec, ["difference_equation", "diff_instruments", "gmm_diff"], None)
    if lev is None and spec is not None:
        lev = _get(spec, ["level_equation", "level_instruments", "gmm_level"], None)
    if standard is None and spec is not None:
        standard = _get(spec, ["standard_instruments", "iv", "exog"], None)

    # Conservative default: do not invent too much; give readable placeholders
    # only when no instrument metadata exists.
    if diff is None:
        diff = ("L2.y", "L3.y")
    if lev is None:
        lev = ("D.y",)
    if standard is None:
        standard = tuple()

    if lag_range is None:
        lag_range = _get(result, ["lag_range", "gmm_lag_range"], None)
    if lag_range is None and spec is not None:
        lag_range = _get(spec, ["lag_range", "gmm_lag_range"], None)

    if collapsed is None:
        collapsed = _optional_bool(_get(result, ["collapsed", "collapse"]))
    if transformation is None:
        transformation = _get(result, ["transformation", "transform"], None)
    if total_instruments is None:
        total_instruments = _optional_int(
            _get(result, ["instruments", "n_instruments", "instrument_count", "j_instruments"])
        )
    if groups is None:
        groups = _optional_int(_get(result, ["groups", "n_groups", "entities", "n_entities"]))

    return InstrumentArchitecture(
        estimator=estimator or _safe_estimator_name(result),
        difference_equation=tuple(str(x) for x in diff),
        level_equation=tuple(str(x) for x in lev),
        standard_instruments=tuple(str(x) for x in standard),
        lag_range=lag_range,
        collapsed=collapsed,
        transformation=transformation,
        total_instruments=total_instruments,
        groups=groups,
    )


class ResultPlotAccessor:
    """
    Unified plotting interface for fitted model results.

    Examples
    --------
    result.plot.health(save="health.png")
    result.plot.persistence(save="persistence.png")
    result.plot.instruments(save="instruments.png")
    result.plot.publication_panel(save="panel.png")
    result.plot.export_all("outputs/model_figures")
    """

    def __init__(self, result: Any):
        self.result = result

    def health(
        self,
        *,
        metrics: HealthMetrics | Mapping[str, Any] | None = None,
        save: str | Path | None = None,
        **metric_overrides: Any,
    ):
        m = _coerce_metrics(self.result, metrics, **metric_overrides)
        return model_health_dashboard_v2(m, save=save)

    def persistence(
        self,
        *,
        phi: float | None = None,
        periods: int = 20,
        save: str | Path | None = None,
    ):
        if phi is None:
            phi = infer_persistence_phi(self.result)
        return dynamic_persistence_dashboard_v2(phi, periods=periods, save=save)

    def instruments(
        self,
        *,
        architecture: InstrumentArchitecture | Mapping[str, Any] | None = None,
        save: str | Path | None = None,
        **architecture_overrides: Any,
    ):
        arch = _coerce_architecture(self.result, architecture, **architecture_overrides)
        return instrument_architecture_dashboard_v2(arch, save=save)

    def effect_surface(
        self,
        x,
        y,
        z,
        *,
        x_label: str = "x",
        y_label: str = "y",
        z_label: str = "Predicted outcome",
        save: str | Path | None = None,
    ):
        return effect_surface_dashboard_v2(
            x,
            y,
            z,
            x_label=x_label,
            y_label=y_label,
            z_label=z_label,
            save=save,
        )

    def publication_panel(
        self,
        *,
        metrics: HealthMetrics | Mapping[str, Any] | None = None,
        architecture: InstrumentArchitecture | Mapping[str, Any] | None = None,
        phi: float | None = None,
        save: str | Path | None = None,
        **overrides: Any,
    ):
        m = _coerce_metrics(self.result, metrics)
        arch = _coerce_architecture(self.result, architecture)
        if phi is None:
            phi = infer_persistence_phi(self.result)

        return publication_panel_v2(
            metrics=m,
            phi=phi,
            instruments=arch,
            result=self.result,
            save=save,
        )

    def standard_gallery(
        self,
        output_dir: str | Path,
        *,
        prefix: str = "model",
        **kwargs: Any,
    ):
        """
        Export the standard R/Stata-style post-estimation plot gallery.

        This complements the SGM-Viz dashboard layer. Use this when the user
        wants the full gallery of coefficient, margins, interaction, residual,
        panel, instrument, and diagnostic plots.
        """
        return export_standard_postestimation_gallery(
            self.result,
            output_dir=output_dir,
            prefix=prefix,
            **kwargs,
        )

    def export_all(
        self,
        output_dir: str | Path,
        *,
        prefix: str = "model",
        metrics: HealthMetrics | Mapping[str, Any] | None = None,
        architecture: InstrumentArchitecture | Mapping[str, Any] | None = None,
        phi: float | None = None,
        surface: Mapping[str, Any] | None = None,
        include_gallery: bool = True,
        gallery_mode: str = "dashboard",
    ) -> dict[str, Path]:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)

        figures: dict[str, Path] = {}

        def put(name: str, fig) -> None:
            path = out / f"{prefix}_{name}.png"
            fig.savefig(path, dpi=300, bbox_inches="tight")
            try:
                import matplotlib.pyplot as plt

                plt.close(fig)
            except Exception:
                pass
            figures[name] = path

        m = _coerce_metrics(self.result, metrics)
        arch = _coerce_architecture(self.result, architecture)
        phi_value = infer_persistence_phi(self.result) if phi is None else float(phi)

        put("health_dashboard", model_health_dashboard_v2(m))
        put("dynamic_persistence", dynamic_persistence_dashboard_v2(phi_value))
        put("instrument_architecture", instrument_architecture_dashboard_v2(arch))
        put(
            "publication_panel",
            publication_panel_v2(metrics=m, phi=phi_value, instruments=arch, result=self.result),
        )

        if surface is not None:
            put(
                "effect_surface",
                effect_surface_dashboard_v2(
                    surface["x"],
                    surface["y"],
                    surface["z"],
                    x_label=surface.get("x_label", "x"),
                    y_label=surface.get("y_label", "y"),
                    z_label=surface.get("z_label", "Predicted outcome"),
                ),
            )

        manifest = {
            "prefix": prefix,
            "metrics": _dataclass_to_jsonable(m),
            "architecture": _dataclass_to_jsonable(arch),
            "phi": phi_value,
            "figures": {k: str(v) for k, v in figures.items()},
        }

        manifest_path = out / f"{prefix}_sgm_viz_manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        figures["manifest"] = manifest_path

        if include_gallery:
            gallery = export_sgm_viz_v2_gallery(
                {k: v for k, v in figures.items() if k != "manifest"},
                output_html=out / f"{prefix}_sgm_viz_gallery.html",
                title=f"{prefix} SGM-Viz report",
                description=(
                    "Model-health, persistence, instrument, effect-surface, and "
                    "publication-panel graphics."
                ),
                gallery_mode=gallery_mode,
            )
            figures["gallery"] = gallery

        return figures


def _dataclass_to_jsonable(obj: Any) -> dict[str, Any]:
    try:
        raw = asdict(obj)
    except Exception:
        return {}
    out: dict[str, Any] = {}
    for key, value in raw.items():
        if isinstance(value, tuple):
            out[key] = list(value)
        elif isinstance(value, Mapping):
            out[key] = dict(value)
        else:
            out[key] = value
    return out


def _coerce_metrics(
    result: Any,
    metrics: HealthMetrics | Mapping[str, Any] | None,
    **overrides: Any,
) -> HealthMetrics:
    if isinstance(metrics, HealthMetrics):
        base = asdict(metrics)
    elif isinstance(metrics, Mapping):
        base = dict(metrics)
    else:
        return extract_health_metrics(result, **overrides)

    base.update({k: v for k, v in overrides.items() if v is not None})
    return HealthMetrics(**base)


def _coerce_architecture(
    result: Any,
    architecture: InstrumentArchitecture | Mapping[str, Any] | None,
    **overrides: Any,
) -> InstrumentArchitecture:
    if isinstance(architecture, InstrumentArchitecture):
        base = asdict(architecture)
    elif isinstance(architecture, Mapping):
        base = dict(architecture)
    else:
        return extract_instrument_architecture(result, **overrides)

    base.update({k: v for k, v in overrides.items() if v is not None})
    return InstrumentArchitecture(**base)


def plot_accessor(result: Any) -> ResultPlotAccessor:
    return ResultPlotAccessor(result)


def attach_plot_accessor(result: Any) -> Any:
    """
    Attach a concrete .plot accessor to one result instance when possible.

    This is useful for objects that allow dynamic attributes. For frozen or
    slot-based classes, use plot_accessor(result) instead.
    """
    with contextlib.suppress(Exception):
        result.plot = ResultPlotAccessor(result)
    return result


def _patch_class_with_plot(cls: type) -> bool:
    try:
        current = getattr(cls, "plot", None)
        if isinstance(current, property):
            return False
        cls.plot = property(lambda self: ResultPlotAccessor(self))
        return True
    except Exception:
        return False


def install_result_plot_accessors() -> list[str]:
    """
    Best-effort installation of .plot properties on known systemgmmkit result classes.

    This function is intentionally defensive: import failures or missing classes
    do not break package import.
    """
    candidates = [
        ("systemgmmkit.linear", ["LinearModelResult"]),
        ("systemgmmkit.estimators.first_difference", ["FirstDifferenceResult"]),
        (
            "systemgmmkit.estimators.fixed_effects",
            ["FixedEffectsResult", "PanelFixedEffectsResult"],
        ),
        (
            "systemgmmkit.estimators.random_effects",
            ["RandomEffectsResult", "PanelRandomEffectsResult"],
        ),
        ("systemgmmkit.estimators.panel_iv", ["PanelIVResult", "Panel2SLSResult"]),
        ("systemgmmkit.gmm", ["DynamicPanelResult", "SystemGMMResult", "DifferenceGMMResult"]),
        ("systemgmmkit.dynamic", ["DynamicPanelResult", "SystemGMMResult", "DifferenceGMMResult"]),
        (
            "systemgmmkit.estimators.dynamic_panel",
            ["DynamicPanelResult", "SystemGMMResult", "DifferenceGMMResult"],
        ),
    ]

    patched: list[str] = []

    for module_name, class_names in candidates:
        try:
            module = importlib.import_module(module_name)
        except Exception:
            continue

        for class_name in class_names:
            cls = getattr(module, class_name, None)
            if isinstance(cls, type) and _patch_class_with_plot(cls):
                patched.append(f"{module_name}.{class_name}")

    return patched


def export_sgm_viz_report(
    result: Any,
    output_dir: str | Path,
    *,
    prefix: str = "model",
    metrics: HealthMetrics | Mapping[str, Any] | None = None,
    architecture: InstrumentArchitecture | Mapping[str, Any] | None = None,
    phi: float | None = None,
    surface: Mapping[str, Any] | None = None,
    include_gallery: bool = True,
    gallery_mode: str = "dashboard",
) -> dict[str, Path]:
    return ResultPlotAccessor(result).export_all(
        output_dir,
        prefix=prefix,
        metrics=metrics,
        architecture=architecture,
        phi=phi,
        surface=surface,
        include_gallery=include_gallery,
        gallery_mode=gallery_mode,
    )


def model_comparison_dashboard_v2(
    results: Sequence[Any],
    *,
    labels: Sequence[str] | None = None,
    save: str | Path | None = None,
):
    """
    Compare model-health diagnostics across multiple fitted models.

    This is intentionally compact: it is designed for screening alternative
    GMM specifications before choosing the preferred reported model.
    """
    import matplotlib.pyplot as plt

    if labels is None:
        labels = [f"Model {i + 1}" for i in range(len(results))]

    rows = []
    for label, result in zip(labels, results):
        m = extract_health_metrics(result)
        rows.append(
            {
                "label": label,
                "hansen": m.hansen_p,
                "sargan": m.sargan_p,
                "ar2": m.ar2_p,
                "ratio": m.instrument_group_ratio,
            }
        )

    fig, ax = plt.subplots(figsize=(9.5, max(3.6, 0.45 * len(rows) + 1.4)))
    ax.axis("off")
    fig.patch.set_facecolor("#F8FAFC")

    ax.text(
        0.02,
        0.95,
        "SGM-Viz model comparison dashboard",
        fontsize=14,
        fontweight="bold",
        ha="left",
        va="top",
    )
    ax.text(
        0.02,
        0.89,
        "Specification screening by Hansen, Sargan, AR(2), and instrument/group ratio.",
        fontsize=8.5,
        color="#52616B",
        ha="left",
        va="top",
    )

    headers = ["Model", "Hansen", "Sargan", "AR(2)", "Instr/Group"]
    xs = [0.03, 0.36, 0.51, 0.66, 0.81]

    y = 0.78
    for x, header in zip(xs, headers):
        ax.text(x, y, header, fontsize=9, fontweight="bold", ha="left", va="center")

    y -= 0.07

    for row in rows:
        values = [
            row["label"],
            _fmt(row["hansen"]),
            _fmt(row["sargan"]),
            _fmt(row["ar2"]),
            _fmt(row["ratio"]),
        ]
        for x, value in zip(xs, values):
            ax.text(x, y, value, fontsize=8.7, ha="left", va="center")
        y -= 0.055

    if save is not None:
        path = Path(save)
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, dpi=300, bbox_inches="tight")

    return fig


def _fmt(value: Any, digits: int = 3) -> str:
    if value is None:
        return "-"
    try:
        v = float(value)
    except Exception:
        return str(value)
    if not np.isfinite(v):
        return "-"
    return f"{v:.{digits}f}"
