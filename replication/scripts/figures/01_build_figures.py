"""Generate every figure included in the JSS manuscript."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402  (backend must be selected first)

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "results" / "comparisons" / "auto_gmm_search_results.csv"
ARTIFACT_DIR = ROOT / "artifacts" / "jss" / "figures"
PAPER_DIR = ROOT / "paper_jss" / "figures"
SEED = 20260724


def main() -> int:
    if not SOURCE.exists():
        raise FileNotFoundError(
            "Automatic-search results are missing. Run 11_auto_gmm_search.py first."
        )
    frame = pd.read_csv(SOURCE)
    required = {"candidate_id", "estimator", "lag_window", "valid", "rmse"}
    missing = required.difference(frame.columns)
    if missing:
        raise RuntimeError(f"Figure source is missing columns: {sorted(missing)}")
    if len(frame) != 4 or frame["rmse"].isna().any():
        raise RuntimeError("Figure source must contain four complete search candidates.")

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    PAPER_DIR.mkdir(parents=True, exist_ok=True)

    plot = frame.sort_values("candidate_id", ascending=False).copy()
    labels = [
        f"{estimator}, lags {lag_window}"
        for estimator, lag_window in zip(plot["estimator"], plot["lag_window"], strict=True)
    ]
    valid = plot["valid"].astype(bool)
    colors = ["#2F6690" if value else "#B9B9B9" for value in valid]

    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.size": 9,
            "axes.labelsize": 9,
            "xtick.labelsize": 8.5,
            "ytick.labelsize": 8.5,
        }
    )
    fig, ax = plt.subplots(figsize=(6.4, 3.15), constrained_layout=True)
    bars = ax.barh(labels, plot["rmse"], color=colors, edgecolor="#303030", linewidth=0.5)
    ax.set_xlabel("Cycle-ordered holdout RMSE (lower is better)")
    ax.set_xlim(left=0)
    ax.grid(axis="x", color="#D8D8D8", linewidth=0.5)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)

    for bar, value, is_valid in zip(bars, plot["rmse"], valid, strict=True):
        suffix = "" if is_valid else "  rejected"
        ax.text(
            float(value) + 0.025,
            bar.get_y() + bar.get_height() / 2,
            f"{float(value):.3f}{suffix}",
            va="center",
            ha="left",
            fontsize=8.5,
        )
    ax.set_xlim(0, float(plot["rmse"].max()) * 1.32)

    outputs = []
    for directory in (ARTIFACT_DIR, PAPER_DIR):
        for extension, options in (
            ("pdf", {}),
            ("png", {"dpi": 180}),
        ):
            path = directory / f"01_auto_gmm_search_holdout.{extension}"
            fig.savefig(path, bbox_inches="tight", **options)
            outputs.append(str(path.relative_to(ROOT)).replace("\\", "/"))
    plt.close(fig)

    status = {
        "status": "PASS",
        "generated_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "seed": SEED,
        "source": str(SOURCE.relative_to(ROOT)).replace("\\", "/"),
        "outputs": outputs,
        "matplotlib_version": matplotlib.__version__,
    }
    (ARTIFACT_DIR / "figure_generation_status.json").write_text(
        json.dumps(status, indent=2), encoding="utf-8"
    )
    print(json.dumps(status, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
