from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class PanelValidationReport:
    n_obs: int
    n_entities: int
    min_t: int
    median_t: float
    max_t: int
    balanced: bool
    duplicate_rows: int
    missing_by_variable: dict[str, int]
    warnings: list[str]

    @property
    def is_usable(self) -> bool:
        return self.duplicate_rows == 0 and self.n_entities > 1 and self.max_t >= 4

    def to_dict(self) -> dict[str, object]:
        return {
            "n_obs": self.n_obs,
            "n_entities": self.n_entities,
            "min_t": self.min_t,
            "median_t": self.median_t,
            "max_t": self.max_t,
            "balanced": self.balanced,
            "duplicate_rows": self.duplicate_rows,
            "missing_by_variable": self.missing_by_variable,
            "warnings": self.warnings,
            "is_usable": self.is_usable,
        }


def validate_panel(
    data: pd.DataFrame,
    *,
    entity: str,
    time: str,
    variables: Iterable[str] | None = None,
    min_recommended_t: int = 5,
) -> PanelValidationReport:
    """Validate core dynamic-panel requirements before GMM estimation."""

    required = [entity, time]
    if variables is not None:
        required.extend(list(variables))

    missing_columns = [c for c in required if c not in data.columns]
    if missing_columns:
        raise KeyError(f"Missing required columns: {missing_columns}")

    work = data[required].copy()
    duplicate_rows = int(work.duplicated([entity, time]).sum())

    counts = work.groupby(entity, observed=True)[time].nunique().astype(int)
    n_entities = int(counts.shape[0])
    min_t = int(counts.min()) if n_entities else 0
    median_t = float(counts.median()) if n_entities else float("nan")
    max_t = int(counts.max()) if n_entities else 0
    balanced = bool(counts.nunique() == 1) if n_entities else False

    variables_list = list(variables or [])
    missing_by_variable = {
        v: int(data[v].isna().sum()) for v in variables_list if v in data.columns
    }

    warnings: list[str] = []
    if duplicate_rows:
        warnings.append(
            "Duplicate entity-time rows found; estimation will be unreliable until resolved."
        )
    if min_t < min_recommended_t:
        warnings.append(
            f"At least one entity has T={min_t}. Dynamic GMM may have weak or unavailable lag instruments."
        )
    if n_entities < 30:
        warnings.append(
            "Small N detected. System GMM asymptotics may be weak; interpret diagnostics cautiously."
        )
    if not balanced:
        warnings.append(
            "Panel is unbalanced. Confirm that missingness is not systematically related to outcomes."
        )
    high_missing = {k: v for k, v in missing_by_variable.items() if v / max(len(data), 1) > 0.2}
    if high_missing:
        warnings.append(f"Variables with more than 20% missingness: {sorted(high_missing)}")

    return PanelValidationReport(
        n_obs=int(len(data)),
        n_entities=n_entities,
        min_t=min_t,
        median_t=median_t,
        max_t=max_t,
        balanced=balanced,
        duplicate_rows=duplicate_rows,
        missing_by_variable=missing_by_variable,
        warnings=warnings,
    )


def estimate_instrument_pressure(
    *,
    n_entities: int,
    gmm_blocks: Sequence[tuple[int, int]],
    n_iv: int = 0,
    n_time_dummies: int = 0,
    system: bool = True,
    collapse: bool = True,
) -> dict[str, float | int | str]:
    """Heuristic instrument-count pressure check.

    This is deliberately conservative and approximate. Exact counts depend on the backend,
    missingness, transformation, and instrument construction rules.
    """

    multiplier = 2 if system else 1
    if collapse:
        gmm_count = sum(max_lag - min_lag + 1 for min_lag, max_lag in gmm_blocks) * multiplier
    else:
        # Approximate upper bound for uncollapsed blocks.
        gmm_count = sum((max_lag - min_lag + 1) * 5 for min_lag, max_lag in gmm_blocks) * multiplier

    total = int(gmm_count + n_iv + n_time_dummies)
    ratio = total / max(n_entities, 1)
    if ratio <= 0.5:
        risk = "low"
    elif ratio <= 1.0:
        risk = "moderate"
    else:
        risk = "high"

    return {"approx_instruments": total, "entities": n_entities, "ratio": ratio, "risk": risk}
