#!/usr/bin/env python3
"""Smoke-test an installed systemgmmkit distribution through public APIs."""

from __future__ import annotations

import argparse
import json
from importlib import metadata
from typing import Any

import numpy as np
import pandas as pd

import systemgmmkit
from systemgmmkit import (
    DynamicPanelSpec,
    FixedEffectsSpec,
    GMMStyle,
    OLSSpec,
    PanelIVSpec,
    run_fixed_effects,
    run_native_dynamic_panel_gmm,
    run_ols,
    run_panel_2sls,
)


def _panel(seed: int = 20260728) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows: list[dict[str, float | int]] = []
    for entity in range(16):
        alpha = float(rng.normal(scale=0.5))
        previous = float(rng.normal())
        for period in range(8):
            x1 = float(rng.normal())
            x2 = float(rng.normal())
            instrument = float(rng.normal())
            endogenous = 0.7 * instrument + 0.2 * alpha + float(rng.normal(scale=0.3))
            y = (
                0.35 * previous
                + 0.7 * x1
                - 0.25 * x2
                + 0.9 * endogenous
                + alpha
                + float(rng.normal(scale=0.25))
            )
            rows.append(
                {
                    "entity": entity,
                    "time": period,
                    "y": y,
                    "x1": x1,
                    "x2": x2,
                    "endogenous": endogenous,
                    "instrument": instrument,
                }
            )
            previous = y
    return pd.DataFrame(rows).sample(frac=1.0, random_state=31415)


def _equal(left: Any, right: Any, names: tuple[str, ...]) -> bool:
    return all(
        np.array_equal(
            np.asarray(getattr(left, name)),
            np.asarray(getattr(right, name)),
            equal_nan=True,
        )
        for name in names
    )


def run_smoke(expected_version: str) -> dict[str, Any]:
    if systemgmmkit.__version__ != expected_version:
        raise RuntimeError(
            f"Expected systemgmmkit {expected_version}, imported {systemgmmkit.__version__}."
        )
    distribution_version = metadata.version("systemgmmkit")
    if distribution_version != expected_version:
        raise RuntimeError(
            f"Expected installed distribution {expected_version}, found {distribution_version}."
        )

    data = _panel()
    ols = run_ols(OLSSpec("y", ["x1", "x2"], covariance="robust"), data)

    fe_spec = FixedEffectsSpec("y", ["x1", "x2"], entity_effects=True, time_effects=True)
    fe_reference = run_fixed_effects(
        fe_spec, data, entity="entity", time="time", preparation_engine="reference"
    )
    fe_accelerated = run_fixed_effects(
        fe_spec, data, entity="entity", time="time", preparation_engine="accelerated"
    )

    iv_spec = PanelIVSpec(
        "y",
        exog=["x1", "x2"],
        endogenous=["endogenous"],
        instruments=["instrument"],
        entity_effects=True,
        time_effects=True,
    )
    iv_reference = run_panel_2sls(
        iv_spec, data, entity="entity", time="time", preparation_engine="reference"
    )
    iv_accelerated = run_panel_2sls(
        iv_spec, data, entity="entity", time="time", preparation_engine="accelerated"
    )

    gmm_spec = DynamicPanelSpec(
        dependent="y",
        regressors=["L1.y", "x1", "x2"],
        gmm=[GMMStyle(variable="L1.y", min_lag=2, max_lag=3)],
        system=False,
        transformation="fd",
        steps="onestep",
        time_dummies=False,
    )
    gmm_reference = run_native_dynamic_panel_gmm(
        gmm_spec,
        data,
        entity="entity",
        time="time",
        preparation_engine="reference",
    )
    gmm_accelerated = run_native_dynamic_panel_gmm(
        gmm_spec,
        data,
        entity="entity",
        time="time",
        preparation_engine="accelerated",
    )

    checks = {
        "ols_finite": bool(np.isfinite(ols.params.to_numpy()).all()),
        "fixed_effects_exact": _equal(
            fe_reference,
            fe_accelerated,
            ("params", "std_errors", "residuals", "fitted_values"),
        ),
        "panel_iv_exact": _equal(
            iv_reference,
            iv_accelerated,
            ("params", "std_errors", "residuals", "fitted_values"),
        ),
        "native_gmm_exact": _equal(
            gmm_reference,
            gmm_accelerated,
            ("params", "std_errors", "residuals"),
        ),
    }
    if not all(checks.values()):
        raise RuntimeError(f"Installed-distribution smoke checks failed: {checks}")
    return {
        "version": systemgmmkit.__version__,
        "distribution_version": distribution_version,
        "checks": checks,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-version", required=True)
    args = parser.parse_args()
    print(json.dumps(run_smoke(args.expected_version), indent=2))


if __name__ == "__main__":
    main()
