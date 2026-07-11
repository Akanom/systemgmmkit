"""Shared reproducible panel data for the examples.

The examples intentionally use generated data so that they run anywhere without
private files. Validation against external software lives under ``artifacts/``.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

EXAMPLES_DIR = Path(__file__).resolve().parent
RESULTS_DIR = EXAMPLES_DIR / "results"


def ensure_results_dir(*parts: str) -> Path:
    """Create and return ``examples/results`` or a child directory."""

    out = RESULTS_DIR.joinpath(*parts)
    out.mkdir(parents=True, exist_ok=True)
    return out


def write_table_pair(frame: pd.DataFrame, stem: str, *, digits: int = 4) -> tuple[Path, Path]:
    """Write a dataframe to CSV and Markdown under ``examples/results``."""

    results = ensure_results_dir()
    clean = frame.copy()
    numeric_cols = clean.select_dtypes(include="number").columns
    clean[numeric_cols] = clean[numeric_cols].round(digits)

    csv_path = results / f"{stem}.csv"
    md_path = results / f"{stem}.md"
    clean.to_csv(csv_path, index=False)
    md_path.write_text(clean.to_markdown(index=False), encoding="utf-8")
    return csv_path, md_path


def make_static_panel(
    n_entities: int = 70,
    n_periods: int = 10,
    seed: int = 2026,
) -> pd.DataFrame:
    """Create a static panel suitable for OLS, FE, RE, and IV/2SLS examples."""

    rng = np.random.default_rng(seed)
    rows: list[dict[str, float | int]] = []

    for firm_id in range(n_entities):
        firm_effect = rng.normal(0.0, 0.8)
        size_base = rng.normal(3.0, 0.35)
        q_state = rng.normal()
        cash_state = rng.normal()

        for t in range(n_periods):
            year = 2010 + t
            cycle = np.sin(t / 2.0)
            demand_shock = rng.normal(0.0, 0.65)

            q_state = 0.60 * q_state + rng.normal(0.0, 0.75)
            cash_state = 0.45 * cash_state + rng.normal(0.0, 0.45)

            q = q_state + 0.15 * cycle
            cashflow = 0.35 * q + 0.40 * cash_state + rng.normal(0.0, 0.35)
            leverage = 0.45 - 0.08 * q + rng.normal(0.0, 0.12)
            size = size_base + 0.04 * t + rng.normal(0.0, 0.06)

            # investment is partly driven by a contemporaneous shock. The lagged
            # q instrument remains relevant through the persistent q process.
            investment = (
                0.65 * q
                + 0.45 * cashflow
                - 0.25 * leverage
                + 0.25 * firm_effect
                + 0.35 * demand_shock
                + rng.normal(0.0, 0.45)
            )

            growth = (
                0.70 * investment
                + 0.22 * cashflow
                - 0.18 * leverage
                + 0.10 * size
                + firm_effect
                + 0.12 * cycle
                + 0.45 * demand_shock
                + rng.normal(0.0, 0.55)
            )

            rows.append(
                {
                    "firm_id": firm_id,
                    "year": year,
                    "growth": growth,
                    "investment": investment,
                    "leverage": leverage,
                    "size": size,
                    "cashflow": cashflow,
                    "q": q,
                }
            )

    df = pd.DataFrame(rows).sort_values(["firm_id", "year"]).reset_index(drop=True)
    df["q_lag1"] = df.groupby("firm_id")["q"].shift(1)
    df["q_lag2"] = df.groupby("firm_id")["q"].shift(2)
    df["L1_growth"] = df.groupby("firm_id")["growth"].shift(1)
    return df


def make_dynamic_panel(
    n_entities: int = 90,
    n_periods: int = 11,
    seed: int = 10,
) -> pd.DataFrame:
    """Create a dynamic panel for Difference/System GMM examples."""

    rng = np.random.default_rng(seed)
    rows: list[dict[str, float | int]] = []

    for entity_id in range(n_entities):
        alpha = rng.normal(0.0, 0.9)
        y_lag = rng.normal()
        x1_state = rng.normal()
        x2_state = rng.normal()

        for t in range(n_periods):
            year = 2000 + t
            common = 0.15 * np.sin(t / 2.0)

            x1_state = 0.45 * x1_state + rng.normal(0.0, 0.80)
            x2_state = 0.55 * x2_state + rng.normal(0.0, 0.65)
            control = rng.normal(0.0, 1.0)
            innovation = rng.normal(0.0, 0.50)

            x1 = x1_state + 0.20 * y_lag + 0.20 * innovation
            x2 = x2_state + 0.15 * common
            y = (
                0.50 * y_lag
                + 0.55 * x1
                - 0.30 * x2
                + 0.20 * control
                + alpha
                + common
                + innovation
            )

            rows.append(
                {
                    "entity_id": entity_id,
                    "year": year,
                    "y": y,
                    "x1": x1,
                    "x2": x2,
                    "control": control,
                }
            )
            y_lag = y

    df = pd.DataFrame(rows).sort_values(["entity_id", "year"]).reset_index(drop=True)
    df["L1.y"] = df.groupby("entity_id")["y"].shift(1)
    return df
