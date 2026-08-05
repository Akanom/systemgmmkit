from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from systemgmmkit import DynamicPanelSpec, GMMStyle, IVStyle

SOURCE_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
REPOSITORY_ROOT = Path(".")
BASE = REPOSITORY_ROOT / "artifacts" / "parity" / "xtabond2"
SPEC_ROOT = BASE / "specs"
SOURCE_DATA_REFERENCE = Path("artifacts/parity/xtabond2/system_gmm_benchmark.csv")
SOURCE_DATA = SOURCE_REPOSITORY_ROOT / SOURCE_DATA_REFERENCE


@dataclass(frozen=True)
class ExtensionSpec:
    spec_id: str
    fixture: Path
    do_file: Path
    output_dir: Path


def extension_specs() -> tuple[ExtensionSpec, ...]:
    ids = ("system_gmm_unbalanced_panel", "system_gmm_variable_missing")
    return tuple(
        ExtensionSpec(
            spec_id=spec_id,
            fixture=SPEC_ROOT / spec_id / "fixture.csv",
            do_file=SPEC_ROOT / spec_id / f"{spec_id}.do",
            output_dir=SPEC_ROOT / spec_id,
        )
        for spec_id in ids
    )


def build_native_spec(spec_id: str) -> DynamicPanelSpec:
    return DynamicPanelSpec(
        dependent="y",
        regressors=["L1.y", "x", "w"],
        gmm=[
            GMMStyle(variable="L1.y", min_lag=2, max_lag=3),
            GMMStyle(variable="x", min_lag=2, max_lag=3),
        ],
        iv=[IVStyle(variable="w", eq="level")],
        time_dummies=False,
        system=True,
        collapse=True,
        transformation="fd",
        steps="twostep",
        name=spec_id,
    )


def derive_fixture(spec_id: str, source: pd.DataFrame) -> pd.DataFrame:
    required = {"id", "t", "y", "x", "w"}
    missing = required - set(source.columns)
    if missing:
        raise ValueError(f"Source benchmark is missing columns: {sorted(missing)}")

    fixture = source.loc[:, ["id", "t", "y", "x", "w"]].copy()
    if spec_id == "system_gmm_unbalanced_panel":
        removed = ((fixture["id"] % 7 == 0) & fixture["t"].isin([4, 8])) | (
            (fixture["id"] % 11 == 0) & (fixture["t"] == 6)
        )
        fixture = fixture.loc[~removed].copy()
    elif spec_id == "system_gmm_variable_missing":
        x_missing = (fixture["id"] % 8 == 0) & fixture["t"].isin([5, 9])
        w_missing = (fixture["id"] % 13 == 0) & (fixture["t"] == 7)
        fixture.loc[x_missing, "x"] = float("nan")
        fixture.loc[w_missing, "w"] = float("nan")
    else:
        raise ValueError(f"Unknown extension specification: {spec_id}")

    return fixture.sort_values(["id", "t"]).reset_index(drop=True)
