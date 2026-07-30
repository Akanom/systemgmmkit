from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import pandas as pd

TableFormat = Literal["markdown", "csv", "latex"]


def _format_p_value(value: Any, *, digits: int) -> str:
    if pd.isna(value):
        return ""
    p_value = float(value)
    threshold = 10.0**-digits
    if 0.0 <= p_value < threshold:
        return f"<{threshold:.{digits}f}"
    return f"{p_value:.{digits}f}"


def format_inference_frame(frame: pd.DataFrame, *, digits: int = 4) -> pd.DataFrame:
    """Return a compact, display-only view of an inferential result frame.

    The raw frame remains unchanged. Redundant generic, z, and t columns are
    collapsed to the statistic implied by ``distribution``; implementation
    fields such as the null value and alpha are omitted. Very small p-values
    are shown with a bound instead of being rounded to zero.
    """

    if digits < 1:
        raise ValueError("digits must be at least 1.")
    if not isinstance(frame, pd.DataFrame):
        raise TypeError("frame must be a pandas DataFrame.")

    distributions = {
        str(value).strip().lower()
        for value in frame.get("distribution", pd.Series(dtype=object)).dropna()
        if str(value).strip()
    }
    statistic = "statistic"
    if distributions == {"t"} or (not distributions and "t" in frame and frame["t"].notna().any()):
        statistic = "t"
    elif distributions == {"z"} or (
        not distributions and "z" in frame and frame["z"].notna().any()
    ):
        statistic = "z"

    output = pd.DataFrame(index=frame.index)
    for column in ("name", "estimate", "std_error"):
        if column in frame:
            output[column] = frame[column]

    source_statistic = statistic if statistic in frame else "statistic"
    if source_statistic in frame:
        output[statistic] = frame[source_statistic]

    if "p_value" in frame:
        output["p_value"] = frame["p_value"].map(
            lambda value: _format_p_value(value, digits=digits)
        )

    for column in ("ci_low", "ci_high"):
        if column in frame:
            output[column] = frame[column]
    if statistic == "t" and "df" in frame:
        output["df"] = frame["df"]
    if statistic == "statistic" and "distribution" in frame:
        output["distribution"] = frame["distribution"]

    numeric_columns = output.select_dtypes(include="number").columns
    output[numeric_columns] = output[numeric_columns].round(digits)
    return output.reset_index(drop=True)


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
