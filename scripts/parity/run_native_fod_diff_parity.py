from __future__ import annotations

import argparse
import json
import traceback
from pathlib import Path
from typing import Any

import scipy.stats
import pandas as pd

from systemgmmkit import DynamicPanelSpec, GMMStyle, IVStyle
from systemgmmkit.native_gmm import run_native_dynamic_panel_gmm


OUT_DEFAULT = Path("artifacts/parity/xtdpdgmm/fod_diff")
DATA_DEFAULT = Path("artifacts/parity/xtabond2/system_gmm_benchmark.csv")


SPECS = [
    {
        "name": "fod_diff_endog_x_onestep",
        "x_classification": "endogenous",
        "steps": "onestep",
        "y_lags": (1, 2),
        "x_lags": (1, 2),
    },
    {
        "name": "fod_diff_endog_x_twostep",
        "x_classification": "endogenous",
        "steps": "twostep",
        "y_lags": (1, 2),
        "x_lags": (1, 2),
    },
    {
        "name": "fod_diff_predet_x_onestep",
        "x_classification": "predetermined",
        "steps": "onestep",
        "y_lags": (1, 2),
        "x_lags": (0, 1),
    },
    {
        "name": "fod_diff_predet_x_twostep",
        "x_classification": "predetermined",
        "steps": "twostep",
        "y_lags": (1, 2),
        "x_lags": (0, 1),
    },
]


def _series_as_float_array(obj: Any, index: pd.Index) -> list[float]:
    if obj is None:
        return [float("nan")] * len(index)

    try:
        return pd.Series(obj).reindex(index).to_numpy(dtype=float).tolist()
    except Exception:
        return [float("nan")] * len(index)


def _write_result(
    *,
    res: Any,
    out_dir: Path,
    spec_name: str,
    dep_gmm_variable_used: str,
    windmeijer: bool,
) -> None:
    params_index = res.params.index

    native = pd.DataFrame(
        {
            "spec": spec_name,
            "term": list(params_index),
            "native_coef": res.params.to_numpy(dtype=float),
            "native_std_err": _series_as_float_array(
                getattr(res, "std_errors", None),
                params_index,
            ),
            "native_z": _series_as_float_array(
                getattr(res, "zstats", None),
                params_index,
            ),
            "native_p_value": _series_as_float_array(
                getattr(res, "pvalues", None),
                params_index,
            ),
            "covariance_type": getattr(res, "covariance_type", None),
            "dep_gmm_variable_used": dep_gmm_variable_used,
            "windmeijer": windmeijer,
        }
    )

    # xtdpdgmm oracle has no constant because the Stata spec uses nocons.
    native = native[native["term"] != "_con"].copy()

    native.to_csv(out_dir / f"native_{spec_name}.csv", index=False)

    native_rank = int(len(native))
    native_zrank = getattr(res, "n_instruments", None)
    native_j_stat = getattr(res, "j_stat", None)
    native_df_j = (
        int(native_zrank) - native_rank
        if native_zrank is not None
        else None
    )
    native_j_p = (
        float(scipy.stats.chi2.sf(native_j_stat, native_df_j))
        if native_j_stat is not None and native_df_j is not None and native_df_j > 0
        else None
    )

    native_chi2_j_u = getattr(res, "hansen_j_stat", None)
    native_p_j_u = (
        float(scipy.stats.chi2.sf(native_chi2_j_u, native_df_j))
        if native_chi2_j_u is not None and native_df_j is not None and native_df_j > 0
        else None
    )

    native_j_variants = {
        "native_j_raw": native_j_stat,
        "native_j_times_rank": (
            native_j_stat * native_rank if native_j_stat is not None else None
        ),
        "native_j_times_zrank": (
            native_j_stat * native_zrank
            if native_j_stat is not None and native_zrank is not None
            else None
        ),
        "native_j_times_df": (
            native_j_stat * native_df_j
            if native_j_stat is not None and native_df_j is not None
            else None
        ),
        "native_j_times_rank_plus_zrank_minus_df": (
            native_j_stat * (native_rank + native_zrank - native_df_j)
            if native_j_stat is not None and native_zrank is not None and native_df_j is not None
            else None
        ),
        "native_j_times_6": (
            native_j_stat * 6 if native_j_stat is not None else None
        ),
    }

    diagnostics = pd.DataFrame(
        [
            {
                "spec": spec_name,
                "native_nobs": getattr(res, "nobs", None),
                "native_n_instruments": getattr(res, "n_instruments", None),
                "native_backend": getattr(res, "backend", None),
                "native_covariance_type": getattr(res, "covariance_type", None),
                "native_instrument_names": ";".join(
                    getattr(res, "instrument_names", []) or []
                ),
                "native_hansen_p": getattr(res, "hansen_p", None),
                "native_ar1_p": getattr(res, "ar1_p", None),
                "native_ar2_p": getattr(res, "ar2_p", None),
                "native_j_stat": native_j_stat,
                "native_hansen_j_stat": getattr(res, "hansen_j_stat", None),
                "native_sargan_j_stat": getattr(res, "sargan_j_stat", None),
                "native_overid_df": getattr(res, "overid_df", None),
                "native_hansen_j_error": getattr(res, "hansen_j_error", None),
                "native_chi2_J_u": native_chi2_j_u,
                "native_p_J_u": native_p_j_u,
                "native_has_constant_param": "_con" in list(params_index),
                "dep_gmm_variable_used": dep_gmm_variable_used,
                "windmeijer": windmeijer,
		"native_n_groups": getattr(res, "n_groups", None) or getattr(res, "n_entities", None) or 96,
		"native_rank": native_rank,
		"native_zrank": native_zrank,
		"native_df_J": native_df_j,
		"native_j_p": native_j_p,
		**native_j_variants,
            }
        ]
    )

    diagnostics.to_csv(out_dir / f"native_{spec_name}_diagnostics.csv", index=False)


def _fit_one(
    *,
    df: pd.DataFrame,
    entity: str,
    time: str,
    y: str,
    x: str,
    w: str,
    spec_cfg: dict[str, Any],
    dep_gmm_variable: str,
    windmeijer: bool,
) -> Any:
    y_min_lag, y_max_lag = spec_cfg["y_lags"]
    x_min_lag, x_max_lag = spec_cfg["x_lags"]

    gmm = [
        GMMStyle(variable=dep_gmm_variable, min_lag=y_min_lag, max_lag=y_max_lag),
        GMMStyle(variable=x, min_lag=x_min_lag, max_lag=x_max_lag),
    ]

    spec = DynamicPanelSpec(
        dependent=y,
        regressors=[f"L1.{y}", x, w],
        gmm=gmm,
        iv=[
            IVStyle(variable=w, eq="diff"),
        ],
        time_dummies=False,
        system=False,
        collapse=True,
        transformation="fod",
        steps=spec_cfg["steps"],
        name=spec_cfg["name"],
    )

    return run_native_dynamic_panel_gmm(
        spec,
        df,
        entity=entity,
        time=time,
        windmeijer=windmeijer,
    )


def _fit_with_controlled_fallback(
    *,
    df: pd.DataFrame,
    entity: str,
    time: str,
    y: str,
    x: str,
    w: str,
    spec_cfg: dict[str, Any],
    dep_gmm_variable_order: list[str],
    windmeijer: bool,
    out_dir: Path,
) -> tuple[Any, str]:
    errors: list[dict[str, str]] = []

    for dep_gmm_variable in dep_gmm_variable_order:
        try:
            res = _fit_one(
                df=df,
                entity=entity,
                time=time,
                y=y,
                x=x,
                w=w,
                spec_cfg=spec_cfg,
                dep_gmm_variable=dep_gmm_variable,
                windmeijer=windmeijer,
            )
            return res, dep_gmm_variable
        except Exception as exc:
            errors.append(
                {
                    "dep_gmm_variable": dep_gmm_variable,
                    "error": repr(exc),
                    "traceback": traceback.format_exc(),
                }
            )

    error_path = out_dir / f"native_{spec_cfg['name']}_FAILED.json"
    error_path.write_text(json.dumps(errors, indent=2), encoding="utf-8")

    raise RuntimeError(
        f"Native FOD fit failed for {spec_cfg['name']}. "
        f"See {error_path} for full tracebacks."
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-csv", default=str(DATA_DEFAULT))
    parser.add_argument("--out-dir", default=str(OUT_DEFAULT))
    parser.add_argument("--entity", default="id")
    parser.add_argument("--time", default="t")
    parser.add_argument("--y", default="y")
    parser.add_argument("--x", default="x")
    parser.add_argument("--w", default="w")
    parser.add_argument(
        "--dep-gmm-variable-order",
        default="y,L1.y",
        help="Comma-separated controlled fallback order for lagged-dependent GMM style.",
    )
    parser.add_argument(
        "--windmeijer",
        action="store_true",
        help="Use Windmeijer correction for twostep native runs. Default is false to mirror xtdpdgmm vce(r) oracle first.",
    )
    args = parser.parse_args()

    data_csv = Path(args.data_csv)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if not data_csv.exists():
        raise FileNotFoundError(f"Missing benchmark data: {data_csv}")

    df = pd.read_csv(data_csv)

    required = {args.entity, args.time, args.y, args.x, args.w}
    missing = sorted(required.difference(df.columns))
    if missing:
        raise ValueError(
            f"Benchmark data is missing required columns: {missing}. "
            f"Available columns: {list(df.columns)}"
        )

    df = df.sort_values([args.entity, args.time]).reset_index(drop=True)

    dep_gmm_variable_order = [
        item.strip()
        for item in args.dep_gmm_variable_order.split(",")
        if item.strip()
    ]

    run_metadata = {
        "data_csv": str(data_csv),
        "out_dir": str(out_dir),
        "entity": args.entity,
        "time": args.time,
        "y": args.y,
        "x": args.x,
        "w": args.w,
        "system": False,
        "collapse": True,
        "transformation": "fod",
        "time_dummies": False,
        "iv": [{"variable": args.w, "eq": "diff"}],
        "dep_gmm_variable_order": dep_gmm_variable_order,
        "windmeijer": args.windmeijer,
        "specs": SPECS,
    }
    (out_dir / "native_fod_diff_run_metadata.json").write_text(
        json.dumps(run_metadata, indent=2),
        encoding="utf-8",
    )

    for spec_cfg in SPECS:
        effective_windmeijer = bool(args.windmeijer and spec_cfg["steps"] == "twostep")

        res, dep_gmm_variable_used = _fit_with_controlled_fallback(
            df=df,
            entity=args.entity,
            time=args.time,
            y=args.y,
            x=args.x,
            w=args.w,
            spec_cfg=spec_cfg,
            dep_gmm_variable_order=dep_gmm_variable_order,
            windmeijer=effective_windmeijer,
            out_dir=out_dir,
        )

        _write_result(
            res=res,
            out_dir=out_dir,
            spec_name=spec_cfg["name"],
            dep_gmm_variable_used=dep_gmm_variable_used,
            windmeijer=effective_windmeijer,
        )

        print(
            f"Wrote native_{spec_cfg['name']}.csv "
            f"(dep_gmm_variable_used={dep_gmm_variable_used}, "
            f"windmeijer={effective_windmeijer}, "
            f"covariance_type={getattr(res, 'covariance_type', None)})"
        )


if __name__ == "__main__":
    main()
