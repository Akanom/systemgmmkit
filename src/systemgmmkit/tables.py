from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import pandas as pd

TableFormat = Literal["markdown", "csv", "latex"]


def result_to_frame(result: Any, *, model_name: str | None = None) -> pd.DataFrame:
    """Convert a supported result object into a tidy coefficient frame."""

    if not hasattr(result, "summary_frame"):
        raise TypeError("result must expose a summary_frame() method.")
    frame = result.summary_frame().copy()
    frame.insert(0, "term", frame.index.astype(str))
    frame.insert(
        0,
        "model",
        model_name or getattr(getattr(result, "spec", None), "name", result.__class__.__name__),
    )
    return frame.reset_index(drop=True)


def combine_result_frames(
    results: list[Any], *, model_names: list[str] | None = None
) -> pd.DataFrame:
    """Stack supported result summaries into one long-format DataFrame."""

    if model_names is not None and len(model_names) != len(results):
        raise ValueError("model_names must have the same length as results.")
    frames = []
    for i, result in enumerate(results):
        name = None if model_names is None else model_names[i]
        frames.append(result_to_frame(result, model_name=name))
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def export_regression_table(
    results: list[Any],
    path: str | Path,
    *,
    fmt: TableFormat | None = None,
    model_names: list[str] | None = None,
    digits: int = 4,
) -> Path:
    """Export supported regression result summaries to Markdown, CSV, or LaTeX."""

    out = Path(path)
    chosen = fmt or out.suffix.lower().lstrip(".")
    if chosen == "md":
        chosen = "markdown"
    if chosen not in {"markdown", "csv", "latex"}:
        raise ValueError("fmt must be one of: markdown, csv, latex")

    frame = combine_result_frames(results, model_names=model_names)
    numeric_cols = frame.select_dtypes(include="number").columns
    frame[numeric_cols] = frame[numeric_cols].round(digits)

    if chosen == "csv":
        frame.to_csv(out, index=False)
    elif chosen == "latex":
        out.write_text(frame.to_latex(index=False), encoding="utf-8")
    else:
        out.write_text(frame.to_markdown(index=False), encoding="utf-8")
    return out
