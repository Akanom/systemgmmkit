from __future__ import annotations

import html
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg", force=True)
import matplotlib.pyplot as plt

from .plots import (
    coefficient_plot,
    conditional_effects_plot,
    counterfactual_scenario_plot,
    fixed_effects_plot,
    hansen_ar_diagnostic_plot,
    instrument_count_plot,
    interaction_plot,
    marginal_effects_plot,
    margins_prediction_plot,
    panel_spaghetti_plot,
    qq_residual_plot,
    residual_histogram,
    residuals_vs_fitted_plot,
    surface_3d_plot,
)


@dataclass
class StandardGalleryResult:
    figures: dict[str, Path] = field(default_factory=dict)
    skipped: dict[str, str] = field(default_factory=dict)
    gallery: Path | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "figures": {k: str(v) for k, v in self.figures.items()},
            "skipped": dict(self.skipped),
            "gallery": str(self.gallery) if self.gallery else None,
        }


def _get(obj: Any, names: Sequence[str], default: Any = None) -> Any:
    if obj is None:
        return default
    for name in names:
        if isinstance(obj, Mapping) and name in obj:
            return obj[name]
        if hasattr(obj, name):
            return getattr(obj, name)
    return default


def _has_rows(data: Any) -> bool:
    if data is None:
        return False
    if isinstance(data, pd.DataFrame):
        return not data.empty
    if isinstance(data, Mapping):
        return bool(data)
    try:
        return len(data) > 0
    except Exception:
        return False


def _diagnostics_from_result(result: Any) -> dict[str, float]:
    out: dict[str, float] = {}

    candidates = {
        "Hansen": ["hansen_p", "hansen_p_value"],
        "Sargan": ["sargan_p", "sargan_p_value"],
        "AR(1)": ["ar1_p", "ar1_p_value"],
        "AR(2)": ["ar2_p", "ar2_p_value"],
    }

    for label, names in candidates.items():
        value = _get(result, names)
        if value is None:
            continue
        try:
            value_f = float(value)
        except Exception:
            continue
        if np.isfinite(value_f):
            out[label] = value_f

    return out


def _write_gallery_html(
    figures: Mapping[str, Path],
    skipped: Mapping[str, str],
    *,
    output_html: str | Path,
    title: str,
    description: str,
) -> Path:
    output = Path(output_html)
    output.parent.mkdir(parents=True, exist_ok=True)

    cards: list[str] = []

    for name, path in figures.items():
        p = Path(path)
        rel = p.name if p.parent.resolve() == output.parent.resolve() else str(p)
        label = name.replace("_", " ").title()

        cards.append(
            f"""
            <section class="card">
              <div class="card-header">{html.escape(label)}</div>
              <img src="{html.escape(rel)}" alt="{html.escape(label)}">
            </section>
            """
        )

    skipped_html = ""
    if skipped:
        rows = "\n".join(
            f"<tr><td>{html.escape(k)}</td><td>{html.escape(v)}</td></tr>"
            for k, v in skipped.items()
        )
        skipped_html = f"""
        <section class="skipped">
          <h2>Skipped plots</h2>
          <p>These plots were skipped because the required post-estimation object or data grid was not supplied.</p>
          <table>
            <thead><tr><th>Plot</th><th>Reason</th></tr></thead>
            <tbody>{rows}</tbody>
          </table>
        </section>
        """

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
  --blue: #0F3D5E;
}}
body {{
  margin: 0;
  font-family: Arial, sans-serif;
  background: var(--bg);
  color: var(--text);
}}
header {{
  padding: 28px 34px 16px 34px;
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
  grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
  gap: 16px;
  padding: 18px 34px 34px 34px;
}}
.card {{
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 14px;
  box-shadow: 0 8px 22px rgba(15, 23, 42, 0.06);
}}
.card-header {{
  font-size: 14px;
  font-weight: 700;
  margin: 0 0 10px 0;
  color: var(--text);
}}
.card img {{
  width: 100%;
  height: auto;
  display: block;
  border-radius: 8px;
}}
.skipped {{
  margin: 0 34px 34px 34px;
  padding: 18px;
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 14px;
}}
.skipped h2 {{
  margin-top: 0;
}}
table {{
  border-collapse: collapse;
  width: 100%;
  margin-top: 12px;
}}
th, td {{
  border-bottom: 1px solid var(--border);
  text-align: left;
  padding: 8px;
  font-size: 13px;
}}
@media print {{
  @page {{
    size: A4 landscape;
    margin: 10mm;
  }}
  body {{
    background: #fff !important;
  }}
  header {{
    display: none !important;
  }}
  .grid {{
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 8mm;
    padding: 0;
  }}
  .card {{
    box-shadow: none;
    page-break-inside: avoid;
    break-inside: avoid;
  }}
  .card img {{
    max-height: 82mm;
    object-fit: contain;
  }}
}}
</style>
</head>
<body>
<header>
  <h1>{html.escape(title)}</h1>
  <p>{html.escape(description)}</p>
</header>
<main class="grid">
{"".join(cards)}
</main>
{skipped_html}
</body>
</html>
"""

    output.write_text(doc, encoding="utf-8")
    return output


def export_standard_postestimation_gallery(
    result: Any | None = None,
    *,
    output_dir: str | Path,
    prefix: str = "model",
    style: str = "sgm",
    preset: str = "paper",
    effects: Any | None = None,
    margins: Any | None = None,
    conditional: Any | None = None,
    interaction: Any | None = None,
    panel: Any | None = None,
    fixed_effects: Any | None = None,
    instruments: Any | None = None,
    diagnostics: Mapping[str, float] | None = None,
    counterfactual: Any | None = None,
    surface: Mapping[str, Any] | None = None,
    entity: str = "entity",
    time: str = "time",
    outcome: str = "y",
    x: str = "x",
    y: str = "y",
    lower: str = "lo",
    upper: str = "hi",
    group: str = "group",
    effect: str = "effect",
    condition: str = "condition",
    scenario: str = "scenario",
    skip_missing: bool = True,
    title: str = "Standard post-estimation plot gallery",
    description: str = "Coefficient, marginal effects, prediction, interaction, residual, panel, instrument, and diagnostic plots.",
) -> StandardGalleryResult:
    """
    Export the standard post-estimation plot gallery.

    This is the R/Stata/Java-style gallery layer. It is intentionally separate
    from SGM-Viz v2 flagship dashboards, which are higher-level diagnostic
    summaries.
    """

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    result_obj = StandardGalleryResult()

    def attempt(order: int, key: str, fn) -> None:
        path = out / f"{prefix}_{order:02d}_{key}.png"
        try:
            fig = fn(path)
            plt.close(fig)
            result_obj.figures[key] = path
        except Exception as exc:
            if not skip_missing:
                raise
            result_obj.skipped[key] = str(exc)

    # 1. Coefficients
    if result is not None:
        attempt(
            1,
            "coefficient_plot",
            lambda path: coefficient_plot(
                result,
                style=style,
                preset=preset,
                title="Coefficient plot",
                subtitle="Dot-whisker coefficient estimates with 95% confidence intervals.",
                save=path,
            ),
        )
    else:
        result_obj.skipped["coefficient_plot"] = "No result object supplied."

    # 2. Marginal effects
    if _has_rows(effects):
        attempt(
            2,
            "marginal_effects_plot",
            lambda path: marginal_effects_plot(
                effects,
                style=style,
                preset=preset,
                title="Marginal effects plot",
                subtitle="Average marginal effects with confidence intervals.",
                save=path,
            ),
        )
    else:
        result_obj.skipped["marginal_effects_plot"] = "No marginal-effects table supplied."

    # 3. Margins / prediction
    if _has_rows(margins):
        attempt(
            3,
            "margins_prediction_plot",
            lambda path: margins_prediction_plot(
                margins,
                x=x,
                y=y,
                lower=lower,
                upper=upper,
                group=group if group in pd.DataFrame(margins).columns else None,
                style=style,
                preset=preset,
                title="Margins / prediction plot",
                subtitle="Predictive margins with optional confidence intervals.",
                save=path,
            ),
        )
    else:
        result_obj.skipped["margins_prediction_plot"] = "No margins/prediction grid supplied."

    # 4. Conditional effects
    if _has_rows(conditional):
        attempt(
            4,
            "conditional_effects_plot",
            lambda path: conditional_effects_plot(
                conditional,
                x=x,
                effect=effect,
                condition=condition,
                lower=lower,
                upper=upper,
                style=style,
                preset=preset,
                title="Conditional effects plot",
                subtitle="Marginal effects across conditioning values.",
                save=path,
            ),
        )
    else:
        result_obj.skipped["conditional_effects_plot"] = "No conditional-effects grid supplied."

    # 5. Interaction
    if _has_rows(interaction):
        attempt(
            5,
            "interaction_plot",
            lambda path: interaction_plot(
                interaction,
                x=x,
                y=y,
                moderator=group,
                lower=lower,
                upper=upper,
                style=style,
                preset=preset,
                title="Interaction plot",
                subtitle="Predicted outcome across a moderator.",
                save=path,
            ),
        )
    else:
        result_obj.skipped["interaction_plot"] = "No interaction grid supplied."

    # 6. 3D / effect surface
    if surface:
        attempt(
            6,
            "effect_surface_plot",
            lambda path: surface_3d_plot(
                surface["data"],
                x=surface.get("x", x),
                y=surface.get("y", "z"),
                z=surface.get("z", y),
                style=style,
                preset=preset,
                title="3D effect surface plot",
                save=path,
            ),
        )
    else:
        result_obj.skipped["effect_surface_plot"] = "No effect-surface data supplied."

    # Residual data
    fitted = _get(result, ["fitted_values", "fittedvalues", "fitted"])
    resid = _get(result, ["residuals", "resid", "errors"])

    # 7. Residuals vs fitted
    if fitted is not None and resid is not None:
        attempt(
            7,
            "residuals_vs_fitted",
            lambda path: residuals_vs_fitted_plot(
                result,
                style=style,
                preset=preset,
                title="Residuals vs fitted",
                subtitle="Residual structure and possible nonlinearity.",
                save=path,
            ),
        )
    else:
        result_obj.skipped["residuals_vs_fitted"] = (
            "Result object does not expose fitted values and residuals."
        )

    # 8. QQ plot
    if resid is not None:
        attempt(
            8,
            "qq_residual_plot",
            lambda path: qq_residual_plot(
                resid,
                style=style,
                preset=preset,
                title="QQ plot of residuals",
                subtitle="Residual quantiles against normal quantiles.",
                save=path,
            ),
        )
    else:
        result_obj.skipped["qq_residual_plot"] = "Result object does not expose residuals."

    # 9. Residual histogram
    if resid is not None:
        attempt(
            9,
            "residual_histogram",
            lambda path: residual_histogram(
                resid,
                style=style,
                preset=preset,
                title="Histogram of residuals",
                subtitle="Residual density profile.",
                save=path,
            ),
        )
    else:
        result_obj.skipped["residual_histogram"] = "Result object does not expose residuals."

    # 10. Panel trajectory
    if _has_rows(panel):
        attempt(
            10,
            "panel_trajectory_plot",
            lambda path: panel_spaghetti_plot(
                panel,
                entity=entity,
                time=time,
                y=outcome,
                highlight=list(pd.DataFrame(panel)[entity].dropna().unique()[:3])
                if entity in pd.DataFrame(panel).columns
                else None,
                style=style,
                preset=preset,
                title="Panel trajectory plot",
                subtitle="Panel trajectories over time with selected units highlighted.",
                save=path,
            ),
        )
    else:
        result_obj.skipped["panel_trajectory_plot"] = "No panel data supplied."

    # 11. Fixed effects
    if _has_rows(fixed_effects):
        attempt(
            11,
            "fixed_effects_plot",
            lambda path: fixed_effects_plot(
                fixed_effects,
                style=style,
                preset=preset,
                title="Fixed effects plot",
                subtitle="Estimated unit effects with optional intervals.",
                save=path,
            ),
        )
    else:
        result_obj.skipped["fixed_effects_plot"] = "No fixed-effects table supplied."

    # 12. Instrument count
    if _has_rows(instruments):
        attempt(
            12,
            "instrument_count_plot",
            lambda path: instrument_count_plot(
                instruments,
                style=style,
                preset=preset,
                title="Instrument count plot",
                subtitle="Instrument growth by lag depth.",
                save=path,
            ),
        )
    else:
        result_obj.skipped["instrument_count_plot"] = "No instrument-count table supplied."

    # 13. Counterfactual scenario
    if _has_rows(counterfactual):
        attempt(
            13,
            "counterfactual_scenario_plot",
            lambda path: counterfactual_scenario_plot(
                counterfactual,
                time=time,
                y=y,
                scenario=scenario,
                style=style,
                preset=preset,
                title="Counterfactual scenario plot",
                subtitle="Predicted outcome under alternative scenarios.",
                save=path,
            ),
        )
    else:
        result_obj.skipped["counterfactual_scenario_plot"] = (
            "No counterfactual scenario grid supplied."
        )

    # 14. Hansen / AR diagnostics
    diag = dict(diagnostics or _diagnostics_from_result(result))
    if diag:
        attempt(
            14,
            "hansen_ar_diagnostic_plot",
            lambda path: hansen_ar_diagnostic_plot(
                diag,
                style=style,
                preset=preset,
                title="Hansen and AR diagnostic p-values",
                subtitle="Overidentification and serial-correlation diagnostics.",
                save=path,
            ),
        )
    else:
        result_obj.skipped["hansen_ar_diagnostic_plot"] = (
            "No Hansen/Sargan/AR diagnostics supplied."
        )

    gallery = _write_gallery_html(
        result_obj.figures,
        result_obj.skipped,
        output_html=out / f"{prefix}_standard_postestimation_gallery.html",
        title=title,
        description=description,
    )

    result_obj.gallery = gallery
    return result_obj
