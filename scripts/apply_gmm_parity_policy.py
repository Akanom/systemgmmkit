"""Reclassify panel-model parity outputs using systemgmmkit policy.

This script is intentionally conservative:

- FE / RE / IV strict parity failures remain release-blocking.
- pydynpd GMM execution failures remain release-blocking.
- Native GMM execution success with strict parity failure becomes
  EXPERIMENTAL_PARITY_PENDING and non-blocking.

Supported input: CSV with at least:
    estimator, backend, execution_passed, strict_parity_passed

Optional columns:
    comparison_backend, status, blocks_release, message

Example:
    python scripts/apply_gmm_parity_policy.py outputs/parity_summary.csv outputs/parity_summary_patched.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from systemgmmkit.gmm_parity_policy import classify_gmm_parity

TRUE_VALUES = {"1", "true", "yes", "y", "pass", "passed", "ok"}
FALSE_VALUES = {"0", "false", "no", "n", "fail", "failed", "bad", ""}


def _to_bool(value: object, *, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None or pd.isna(value):
        return default
    text = str(value).strip().lower()
    if text in TRUE_VALUES:
        return True
    if text in FALSE_VALUES:
        return False
    return default


def _first_present(row: pd.Series, names: list[str], default: str = "") -> str:
    for name in names:
        if name in row and not pd.isna(row[name]):
            value = str(row[name]).strip()
            if value:
                return value
    return default


def reclassify_file(input_path: Path, output_path: Path) -> pd.DataFrame:
    df = pd.read_csv(input_path)

    required_any = {"estimator", "model", "model_type"}
    if not any(col in df.columns for col in required_any):
        raise ValueError("Input CSV must contain one of: estimator, model, model_type.")

    if "backend" not in df.columns:
        raise ValueError("Input CSV must contain a backend column.")

    statuses: list[str] = []
    blocks: list[bool] = []
    messages: list[str] = []

    for _, row in df.iterrows():
        estimator = _first_present(row, ["estimator", "model", "model_type"])
        backend = _first_present(row, ["backend"])
        comparison_backend = _first_present(
            row, ["comparison_backend", "reference_backend"], default=""
        )

        execution_passed = _to_bool(
            row["execution_passed"]
            if "execution_passed" in row
            else row.get("execution_status", ""),
            default=True,
        )

        strict_parity_passed = _to_bool(
            row["strict_parity_passed"]
            if "strict_parity_passed" in row
            else row.get("parity_passed", ""),
            default=False,
        )

        decision = classify_gmm_parity(
            estimator=estimator,
            backend=backend,
            comparison_backend=comparison_backend or None,
            execution_passed=execution_passed,
            strict_parity_passed=strict_parity_passed,
        )

        statuses.append(decision.status)
        blocks.append(decision.blocks_release)
        messages.append(decision.message)

    df["policy_status"] = statuses
    df["blocks_release"] = blocks
    df["policy_message"] = messages

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    return df


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_csv", type=Path)
    parser.add_argument("output_csv", type=Path)
    args = parser.parse_args()

    df = reclassify_file(args.input_csv, args.output_csv)

    blocking = int(df["blocks_release"].sum())
    print(f"Wrote: {args.output_csv}")
    print(f"Rows: {len(df)}")
    print(f"Release-blocking rows: {blocking}")

    return 1 if blocking else 0


if __name__ == "__main__":
    raise SystemExit(main())
