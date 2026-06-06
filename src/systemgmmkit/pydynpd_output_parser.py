from __future__ import annotations

import re
from typing import Any

import pandas as pd


_NUMERIC_RE = re.compile(
    r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$"
)


_VAR_RE = re.compile(
    r"^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?$"
)


def _to_float(value: str) -> float | None:
    value = str(value).strip().replace(",", "")

    if value in {"", ".", "nan", "NaN", "None", "NA"}:
        return None

    if not _NUMERIC_RE.match(value):
        return None

    try:
        return float(value)
    except Exception:
        return None


def parse_pydynpd_output_table(text: str) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Parse coefficients, standard errors, and p-values from pydynpd text output.

    Expected table shape:

        | variable | coef. | Corrected Std. Err. | z | P>|z| | stars |

    Returns
    -------
    params, std_errors, pvalues
        Three pandas Series indexed by term name.
    """

    params: dict[str, float] = {}
    std_errors: dict[str, float] = {}
    pvalues: dict[str, float] = {}

    if not text:
        return (
            pd.Series(dtype=float, name="coefficient"),
            pd.Series(dtype=float, name="std_err"),
            pd.Series(dtype=float, name="p_value"),
        )

    for raw_line in str(text).splitlines():
        line = raw_line.strip()

        if not line or "|" not in line:
            continue

        # Split table rows like:
        # |  L1.growth_rate | 0.3293583 | 0.0511580 | 6.4380580 | 0.0000000 | *** |
        cells = [cell.strip() for cell in line.strip("|").split("|")]

        if len(cells) < 5:
            continue

        term = cells[0]

        if not _VAR_RE.match(term):
            continue

        coef = _to_float(cells[1])
        se = _to_float(cells[2])
        pvalue = _to_float(cells[4])

        if coef is None or se is None or pvalue is None:
            continue

        if se < 0:
            continue

        if not (0.0 <= pvalue <= 1.0):
            continue

        params[term] = coef
        std_errors[term] = se
        pvalues[term] = pvalue

    return (
        pd.Series(params, dtype=float, name="coefficient"),
        pd.Series(std_errors, dtype=float, name="std_err"),
        pd.Series(pvalues, dtype=float, name="p_value"),
    )


def enrich_result_with_parsed_standard_errors(result: Any) -> Any:
    """Attach parsed pydynpd standard errors to a result object when missing."""

    existing = getattr(result, "std_errors", None)

    try:
        existing_series = pd.Series(existing)
        if len(existing_series) > 0 and existing_series.notna().any():
            return result
    except Exception:
        pass

    raw_output = getattr(result, "raw_output", None)

    if not isinstance(raw_output, str) or not raw_output.strip():
        return result

    parsed_params, parsed_se, parsed_pvalues = parse_pydynpd_output_table(raw_output)

    if parsed_se.empty:
        return result

    current_params = getattr(result, "params", None)

    if current_params is not None:
        current_params = pd.Series(current_params)
        target_index = list(current_params.index)

        parsed_se = parsed_se.reindex(target_index)
        parsed_pvalues = parsed_pvalues.reindex(target_index)
        parsed_params = parsed_params.reindex(target_index)

    if parsed_se.notna().sum() == 0:
        return result

    try:
        setattr(result, "std_errors", parsed_se)
    except Exception:
        return result

    # Keep existing params/pvalues unless missing or empty.
    try:
        current_pvalues = pd.Series(getattr(result, "pvalues", None))
        if_pvalues = pd.Series(getattr(result, "pvalues", None))
        if len(current_pvalues) == 0 or current_pvalues.isna().all():
            setattr(result, "pvalues", parsed_pvalues)
    except Exception:
        setattr(result, "pvalues", parsed_pvalues)

    try:
        current_params = pd.Series(getattr(result, "params", None))
        if len(current_params) == 0 or current_params.isna().all():
            setattr(result, "params", parsed_params)
    except Exception:
        setattr(result, "params", parsed_params)

    notes = getattr(result, "notes", None)
    note = "Parsed direct pydynpd standard errors from raw backend output."

    try:
        if notes is None:
            setattr(result, "notes", [note])
        elif isinstance(notes, list):
            if note not in notes:
                notes.append(note)
        elif isinstance(notes, tuple):
            if note not in notes:
                setattr(result, "notes", [*notes, note])
    except Exception:
        pass

    return result
