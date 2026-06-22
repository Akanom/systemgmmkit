from __future__ import annotations

import math
from typing import Iterable

import numpy as np
import pandas as pd


def _clean_pair(y_true: Iterable[float], y_pred: Iterable[float]) -> tuple[np.ndarray, np.ndarray]:
    yt = np.asarray(list(y_true), dtype=float)
    yp = np.asarray(list(y_pred), dtype=float)

    if yt.shape != yp.shape:
        raise ValueError(f"Shape mismatch: y_true {yt.shape}, y_pred {yp.shape}")

    mask = np.isfinite(yt) & np.isfinite(yp)
    if not mask.any():
        raise ValueError("No finite observations available for metric calculation.")

    return yt[mask], yp[mask]


def regression_metrics(
    y_true: Iterable[float],
    y_pred: Iterable[float],
    *,
    prefix: str | None = None,
) -> dict[str, float]:
    """
    Standard ML-style regression metrics for econometric model evaluation.
    """
    yt, yp = _clean_pair(y_true, y_pred)
    err = yt - yp

    mae = float(np.mean(np.abs(err)))
    mse = float(np.mean(err ** 2))
    rmse = float(math.sqrt(mse))

    denom = np.where(np.abs(yt) < 1e-12, np.nan, np.abs(yt))
    mape = float(np.nanmean(np.abs(err) / denom) * 100.0)

    smape_denom = np.abs(yt) + np.abs(yp)
    smape = float(np.nanmean(2.0 * np.abs(err) / np.where(smape_denom < 1e-12, np.nan, smape_denom)) * 100.0)

    ss_res = float(np.sum(err ** 2))
    ss_tot = float(np.sum((yt - np.mean(yt)) ** 2))
    r2 = float(1.0 - ss_res / ss_tot) if ss_tot > 0 else float("nan")

    out = {
        "n": float(len(yt)),
        "mae": mae,
        "mse": mse,
        "rmse": rmse,
        "mape": mape,
        "smape": smape,
        "r2": r2,
    }

    if prefix:
        return {f"{prefix}_{k}": v for k, v in out.items()}

    return out
