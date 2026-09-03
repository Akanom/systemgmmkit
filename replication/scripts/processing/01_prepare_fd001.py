"""Download, validate, and prepare the official NASA C-MAPSS FD001 panel."""

from __future__ import annotations

import hashlib
import io
import json
import os
import urllib.request
import zipfile
from contextlib import suppress
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
RAW_DIR = ROOT / "data" / "raw" / "fd001"
PROCESSED_DIR = ROOT / "data" / "processed"
REPORT_DIR = ROOT / "artifacts" / "jss" / "reproducibility"
REPORT_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

RAW_CANDIDATES = [
    RAW_DIR / "train_FD001.txt",
    RAW_DIR / "train_FD001.csv",
    RAW_DIR / "FD001.txt",
]
DOWNLOAD_URL = (
    "https://phm-datasets.s3.amazonaws.com/NASA/"
    "6.+Turbofan+Engine+Degradation+Simulation+Data+Set.zip"
)
DOWNLOAD_PATH = RAW_DIR / "CMAPSSData.zip"
SEED = 20260724


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _extract_fd001_bytes(archive_path: Path) -> tuple[bytes, str]:
    with zipfile.ZipFile(archive_path) as archive:
        direct = [name for name in archive.namelist() if name.endswith("train_FD001.txt")]
        if len(direct) == 1:
            return archive.read(direct[0]), direct[0]
        if direct:
            raise RuntimeError("NASA archive contains ambiguous train_FD001.txt entries.")

        nested_archives = [
            name for name in archive.namelist() if name.lower().endswith("cmapssdata.zip")
        ]
        if len(nested_archives) != 1:
            raise RuntimeError("NASA archive does not contain a unique C-MAPSS data archive.")
        nested_name = nested_archives[0]
        with zipfile.ZipFile(io.BytesIO(archive.read(nested_name))) as nested:
            matches = [name for name in nested.namelist() if name.endswith("train_FD001.txt")]
            if len(matches) != 1:
                raise RuntimeError(
                    "Nested NASA C-MAPSS archive does not contain exactly one train_FD001.txt."
                )
            member = f"{nested_name}!/{matches[0]}"
            return nested.read(matches[0]), member


def _download_raw() -> tuple[Path, str]:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    if not DOWNLOAD_PATH.exists():
        urllib.request.urlretrieve(DOWNLOAD_URL, DOWNLOAD_PATH)
    payload, member = _extract_fd001_bytes(DOWNLOAD_PATH)
    target = RAW_DIR / "train_FD001.txt"
    target.write_bytes(payload)
    return target, member


def _read_raw() -> pd.DataFrame | None:
    for path in RAW_CANDIDATES:
        if not path.exists():
            continue
        for opts in ({"sep": r"\s+", "header": None}, {"sep": ",", "header": 0}):
            try:
                df = pd.read_csv(path, **opts)
                if df.shape[1] < 2:
                    continue
                if opts.get("header") is None:
                    if df.shape[1] != 26:
                        continue
                    df.columns = [
                        "entity",
                        "time",
                        "op_setting1",
                        "op_setting2",
                        "op_setting3",
                        *[f"sensor_{index}" for index in range(1, 22)],
                    ]
                return df
            except Exception:
                continue
    return None


def _coerce_panel(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    frame.columns = [str(c).strip().lower() for c in frame.columns]

    if "unit" in frame.columns and "entity" not in frame.columns:
        frame = frame.rename(columns={"unit": "entity"})
    if "cycle" in frame.columns and "time" not in frame.columns:
        frame = frame.rename(columns={"cycle": "time"})
    if "y" in frame.columns and "risk" not in frame.columns:
        frame = frame.rename(columns={"y": "risk"})
    if "unit_id" in frame.columns and "entity" not in frame.columns:
        frame = frame.rename(columns={"unit_id": "entity"})

    # Keep a compact canonical set for paper estimators.
    if "time" not in frame.columns:
        frame = frame.reset_index().rename(columns={"index": "time"})
    if "entity" not in frame.columns:
        frame["entity"] = 0

    for col in frame.columns:
        if col in {"entity", "time", "risk"}:
            continue
        with suppress(Exception):
            frame[col] = pd.to_numeric(frame[col], errors="coerce")

    frame = frame.sort_values(["entity", "time"]).reset_index(drop=True)
    if "risk" not in frame.columns:
        maximum_cycle = frame.groupby("entity")["time"].transform("max")
        frame["rul"] = maximum_cycle - frame["time"]
        frame["risk"] = frame["time"] / maximum_cycle

    frame["L1_risk"] = frame.groupby("entity")["risk"].shift(1)
    for col in [
        "degradation_index",
        "sensor_mean",
        "sensor_mean_z",
        "pc2",
        "op_setting1",
        "op_setting2",
        "op_setting3",
        "op_setting4",
    ]:
        if col in frame.columns:
            std = frame[col].std(ddof=0)
            if pd.isna(std) or std == 0:
                frame[f"z_{col}"] = 0.0
            else:
                frame[f"z_{col}"] = (frame[col] - frame[col].mean()) / std

    return frame


def _synthetic_panel() -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    rows = []
    n_entities = 12
    n_periods = 20
    for entity in range(n_entities):
        y_prev = rng.normal()
        for period in range(1, n_periods + 1):
            x = rng.normal(size=3)
            risk = 0.65 * y_prev + 0.1 * x[0] + 0.3 * x[1] + 0.05 * rng.normal()
            rows.append(
                {
                    "entity": f"u{entity:02d}",
                    "time": period,
                    "risk": risk,
                    "degradation_index": rng.normal(),
                    "sensor_mean_z": rng.normal(),
                    "pc2": rng.normal(),
                    "op_setting1": rng.normal(),
                    "op_setting2": rng.normal(),
                    "op_setting3": rng.normal(),
                    "op_setting4": rng.normal(),
                    "Fc": rng.normal(),
                    "hs": rng.normal(),
                }
            )
            y_prev = risk
    return _coerce_panel(pd.DataFrame(rows))


def main() -> int:
    frame = _read_raw()
    source = "raw"
    archive_member = None
    if frame is None:
        mode = os.environ.get("SYSTEMGMMKIT_REPLICATION_MODE", "open")
        if mode == "smoke":
            frame = _synthetic_panel()
            source = "synthetic"
        else:
            _, archive_member = _download_raw()
            frame = _read_raw()
            source = "NASA C-MAPSS FD001 download"
    elif DOWNLOAD_PATH.exists() and (RAW_DIR / "train_FD001.txt").exists():
        expected, archive_member = _extract_fd001_bytes(DOWNLOAD_PATH)
        if hashlib.sha256(expected).hexdigest() == _sha256(RAW_DIR / "train_FD001.txt"):
            source = "NASA C-MAPSS FD001 download"

    if not isinstance(frame, pd.DataFrame) or frame.empty:
        return 2

    out_csv = PROCESSED_DIR / "fd001_panel.csv"
    out_parquet = PROCESSED_DIR / "fd001_panel.parquet"
    frame.to_csv(out_csv, index=False)
    # Parquet is an optional convenience artifact; CSV is the required output.
    with suppress(Exception):
        frame.to_parquet(out_parquet, index=False)

    by_entity = frame.groupby("entity").size()
    report = {
        "source": source,
        "rows": int(len(frame)),
        "units": int(frame["entity"].nunique()),
        "time_min": float(frame["time"].min()),
        "time_max": float(frame["time"].max()),
        "avg_periods_per_unit": float(by_entity.mean()),
        "min_periods_per_unit": int(by_entity.min()),
        "max_periods_per_unit": int(by_entity.max()),
        "missing_in_panel": int(frame.isna().any(axis=1).sum()),
        "seed": SEED,
        "download_url": DOWNLOAD_URL if source != "synthetic" else None,
        "archive_member": archive_member,
        "download_sha256": (_sha256(DOWNLOAD_PATH) if DOWNLOAD_PATH.exists() else None),
        "raw_sha256": (
            _sha256(RAW_DIR / "train_FD001.txt") if (RAW_DIR / "train_FD001.txt").exists() else None
        ),
    }
    (REPORT_DIR / "fd001_preprocessing_report.json").write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
