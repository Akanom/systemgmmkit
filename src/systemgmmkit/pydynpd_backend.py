from __future__ import annotations

import contextlib
import importlib
import io
import json
import os
import re
import traceback
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .spec import DynamicPanelSpec, GMMStyle, IVStyle


@dataclass
class PydynpdGMMResult:
    """Structured adapter around a pydynpd Difference/System GMM run.

    pydynpd primarily prints estimation output and returns a raw ``abond`` object.
    This adapter gives downstream code a stable result surface while preserving the
    original object and printed output for debugging and auditability.
    """

    params: pd.Series
    std_errors: pd.Series
    pvalues: pd.Series
    nobs: int | None = None
    n_groups: int | None = None
    n_instruments: int | None = None
    hansen_p: float | None = None
    sargan_p: float | None = None
    ar1_p: float | None = None
    ar2_p: float | None = None
    command: str = ""
    backend: str = "pydynpd"
    raw_output: str = ""
    raw_result: Any | None = None
    error: str | None = None

    @property
    def succeeded(self) -> bool:
        return self.error is None

    def to_markdown(self) -> str:
        frame = pd.DataFrame(
            {
                "coef": self.params,
                "std_err": self.std_errors.reindex(self.params.index),
                "p_value": self.pvalues.reindex(self.params.index),
            }
        )
        return frame.to_markdown()


def _format_regressor(var: str) -> str:
    """Convert package lag notation to pydynpd notation."""
    if var.startswith("L") and "." in var:
        return var
    return var



def _valid_p_value(value: object) -> float | None:
    """Return a valid p-value in [0, 1], otherwise None.

    Some backend objects may expose non-p-value sentinels or malformed
    diagnostic values. Public result objects should not report impossible
    p-values such as 2.0.
    """

    if value is None:
        return None

    try:
        if isinstance(value, (list, tuple)) and len(value) == 1:
            value = value[0]
        out = float(value)
    except (TypeError, ValueError):
        return None

    if out != out:
        return None
    if out == float("inf") or out == float("-inf"):
        return None
    if out < 0.0 or out > 1.0:
        return None

    return out


def _format_gmm(block: GMMStyle, collapse: bool) -> str:
    """Format a pydynpd GMM block."""
    _ = collapse
    if block.eq is not None:
        raise NotImplementedError(
            "pydynpd command generation does not currently support eq() scoping."
        )
    lag = f"{block.min_lag}:{block.max_lag}"
    return f"gmm({block.variable}, {lag})"


def _format_iv_group(blocks: Sequence[IVStyle]) -> str:
    """Format all IV-style variables as one pydynpd iv(...) block.

    pydynpd is more robust when exogenous/IV-style variables are grouped in a
    single block instead of emitted as many adjacent ``iv(...)`` clauses.
    """
    if not blocks:
        return ""
    scoped = [block for block in blocks if block.eq is not None]
    if scoped:
        raise NotImplementedError(
            "pydynpd command generation does not currently support eq() scoping."
        )
    variables = " ".join(block.variable for block in blocks)
    return f"iv({variables})"


def build_pydynpd_command(spec: DynamicPanelSpec) -> str:
    """Build a pydynpd command string from a structured specification.

    pydynpd's command has the structure::

        y regressors | gmm(...) iv(...) | options

    ``system=True`` maps to pydynpd's level equation being included. ``system=False``
    appends ``nolevel``, giving Difference GMM.
    """

    left = " ".join([spec.dependent, *(_format_regressor(v) for v in spec.regressors)])
    gmm_blocks = [_format_gmm(g, spec.collapse) for g in spec.gmm]
    iv_block = _format_iv_group(spec.iv)
    instruments = " ".join([*gmm_blocks, *([iv_block] if iv_block else [])])
    options: list[str] = []

    if spec.time_dummies:
        options.append("timedumm")
    if not spec.system:
        options.append("nolevel")
    if spec.collapse:
        options.append("collapse")
    if spec.steps == "onestep":
        options.append("onestep")
    elif spec.steps == "iterated":
        options.append("iterated")

    return " | ".join([left, instruments, " ".join(options)]).strip()


def _apply_numpy_compatibility_shims() -> None:
    """Apply narrow compatibility shims needed by older pydynpd releases.

    Older pydynpd releases call ``float(...)`` / ``math.sqrt(...)`` on 1x1
    NumPy arrays in specification tests. Newer NumPy versions reject those
    conversions. These shims preserve pydynpd's formulas and only fix scalar
    extraction.
    """
    if not hasattr(np, "in1d"):
        np.in1d = np.isin  # type: ignore[attr-defined]

    try:
        specification_tests = importlib.import_module("pydynpd.specification_tests")
    except ModuleNotFoundError:
        return

    # Unit tests may monkeypatch importlib.import_module and return fake modules.
    required = (
        "hansen_overid",
        "hansen_test_info",
        "AR_test",
        "AR_test_info",
        "AR_get_diff_XR",
        "lag",
    )
    if not all(hasattr(specification_tests, attr) for attr in required):
        return

    if getattr(specification_tests, "_systemgmmkit_scalar_shims", False):
        return

    try:
        from scipy import stats
    except Exception:
        return

    hansen_test_info = specification_tests.hansen_test_info
    ar_test_info = specification_tests.AR_test_info
    ar_get_diff_xr = specification_tests.AR_get_diff_XR
    lag = specification_tests.lag

    def _scalarize(value: Any) -> float:
        arr = np.asarray(value)
        if arr.size != 1:
            raise TypeError(f"Expected scalar-compatible value, got shape {arr.shape}.")
        return float(arr.reshape(-1)[0])

    def hansen_overid_scalar_compat(
        W2_inv: Any,
        N: Any,
        zs: Any,
        num_instru: Any,
        num_indep: Any,
    ) -> Any:
        # Preserve pydynpd's original formula:
        # hansen_test = zs.T @ W2_inv @ zs * (1 / N)
        z_moments = np.asarray(zs, dtype=float)
        weight_inv = np.asarray(W2_inv, dtype=float)

        hansen_test = np.linalg.multi_dot([z_moments.transpose(), weight_inv, z_moments]) * (
            1.0 / int(N)
        )

        df = int(num_instru - num_indep)
        crit = float(stats.chi2.ppf(q=0.95, df=df))
        p_value = 1.0 - stats.chi2.cdf(hansen_test, df)

        return hansen_test_info(
            _scalarize(hansen_test),
            df,
            _scalarize(p_value),
            crit,
        )

    def ar_test_scalar_compat(model: Any, zs_list: Any, step: Any, m: Any) -> Any:
        # Preserve pydynpd's original AR_test formula while fixing scalar conversion.
        N = int(model.N)
        z_list = model.z_list
        z_height = int(z_list.shape[0] / N)

        current_step = model.step_results[int(step) - 1]

        ori_residual = current_step.residual
        r0_height = int(ori_residual.shape[0] / N)

        M_XZ_W = current_step._M_XZ_W
        vcov = current_step.vcov

        diff_x, diff_r = ar_get_diff_xr(model, current_step.beta, ori_residual, r0_height)
        r_height = int(diff_r.shape[0] / N)
        x_height = int(diff_x.shape[0] / N)

        ar_list = []
        temp = np.zeros((r_height * N, 1), np.float64)
        lag(diff_r, temp, N, 1, 0)

        for j in range(1, int(m) + 1):
            for i in range(N):
                r_i = diff_r[(r_height * i) : (r_height * i + r_height), 0:1]
                r_t_i = r_i.transpose()

                lag_res = np.ndarray((r_height, 1), dtype=np.float64)
                lag(r_i, lag_res, 1, j, 0)
                lag_res[np.isnan(lag_res)] = 0
                lag_res_t = lag_res.transpose()

                x = diff_x[(x_height * i) : (x_height * i + x_height), :]
                d0_temp = lag_res_t @ r_i
                d1_temp = d0_temp @ r_t_i @ lag_res
                EX_temp = lag_res_t @ x

                zs = zs_list[(z_height * i) : (z_height * i + z_height), :]
                temp3_temp = zs @ d0_temp.transpose()

                if i == 0:
                    d0 = d0_temp
                    d1 = d1_temp
                    EX = EX_temp
                    temp3 = temp3_temp
                else:
                    d0 += d0_temp
                    d1 += d1_temp
                    EX += EX_temp
                    temp3 += temp3_temp

            d2 = (-2) * np.linalg.multi_dot([EX, M_XZ_W, temp3])
            d3 = np.linalg.multi_dot([EX, vcov, EX.transpose()])

            denominator = _scalarize(d1 + d2 + d3)
            if denominator <= 0:
                raise Exception("AR test failed")

            ar_temp = _scalarize(d0) / float(np.sqrt(denominator))
            p_value = float(stats.norm.sf(abs(ar_temp)) * 2)

            ar_list.append(ar_test_info(j, ar_temp, p_value))

        return ar_list

    specification_tests.hansen_overid = hansen_overid_scalar_compat
    specification_tests.AR_test = ar_test_scalar_compat
    specification_tests._systemgmmkit_scalar_shims = True
    specification_tests._systemgmmkit_hansen_scalar_shim = True
    specification_tests._systemgmmkit_ar_scalar_shim = True

    # pydynpd.regression imports specification_tests as `tests`; patch that alias
    # too if it is already loaded or importable.
    try:
        regression = importlib.import_module("pydynpd.regression")
    except ModuleNotFoundError:
        return

    if hasattr(regression, "tests"):
        if hasattr(regression.tests, "hansen_overid"):
            regression.tests.hansen_overid = hansen_overid_scalar_compat
        if hasattr(regression.tests, "AR_test"):
            regression.tests.AR_test = ar_test_scalar_compat


def _to_float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        arr = np.asarray(value)
        if arr.size == 0:
            return None
        return float(arr.reshape(-1)[0])
    except Exception:
        try:
            return float(value)
        except Exception:
            return None


def _to_int_or_none(value: Any) -> int | None:
    converted = _to_float_or_none(value)
    if converted is None:
        return None
    return int(round(converted))


def _series_from_any(value: Any, *, names: Sequence[str] | None = None) -> pd.Series:
    if value is None:
        return pd.Series(dtype="float64")
    if isinstance(value, pd.Series):
        return pd.to_numeric(value, errors="coerce")
    if isinstance(value, dict):
        return pd.Series(value, dtype="float64")
    if isinstance(value, pd.DataFrame):
        if value.empty:
            return pd.Series(dtype="float64")
        return pd.to_numeric(value.iloc[:, 0], errors="coerce")
    try:
        arr = np.asarray(value, dtype=float).reshape(-1)
    except Exception:
        return pd.Series(dtype="float64")
    index = list(names[: len(arr)]) if names is not None else None
    return pd.Series(arr, index=index, dtype="float64")


def _first_existing_attr(obj: Any, names: Sequence[str]) -> Any:
    for name in names:
        if hasattr(obj, name):
            return getattr(obj, name)
    return None


def _coefficient_frame_from_raw(raw: Any) -> pd.DataFrame | None:
    candidates = [
        _first_existing_attr(raw, ["regression_table", "reg_table", "table", "summary_table"]),
        _first_existing_attr(raw, ["models", "models_list"]),
        _first_existing_attr(raw, ["step_results", "results"]),
    ]
    for candidate in candidates:
        if candidate is None:
            continue
        if isinstance(candidate, pd.DataFrame):
            return candidate
        if isinstance(candidate, (list, tuple)) and candidate:
            for item in reversed(candidate):
                frame = _coefficient_frame_from_raw(item)
                if frame is not None:
                    return frame
        if candidate is not raw:
            frame = _coefficient_frame_from_raw(candidate)
            if frame is not None:
                return frame
    return None


def _extract_from_frame(frame: pd.DataFrame) -> tuple[pd.Series, pd.Series, pd.Series]:
    lower = {str(c).strip().lower(): c for c in frame.columns}

    def pick(*names: str) -> Any | None:
        for name in names:
            if name in lower:
                return lower[name]
        for key, col in lower.items():
            if any(name in key for name in names):
                return col
        return None

    variable_col = pick("variable", "var", "name")
    coef_col = pick("coefficient", "coef", "estimate")
    se_col = pick("std err", "std_error", "stderr", "standard error")
    p_col = pick("p>|z|", "p-value", "pvalue", "p value", "p")

    index = frame[variable_col].astype(str).tolist() if variable_col is not None else frame.index
    params = (
        pd.to_numeric(frame[coef_col], errors="coerce")
        if coef_col is not None
        else pd.Series(dtype="float64")
    )
    ses = (
        pd.to_numeric(frame[se_col], errors="coerce")
        if se_col is not None
        else pd.Series(dtype="float64")
    )
    pvals = (
        pd.to_numeric(frame[p_col], errors="coerce")
        if p_col is not None
        else pd.Series(dtype="float64")
    )
    params.index = index[: len(params)]
    if len(ses):
        ses.index = index[: len(ses)]
    if len(pvals):
        pvals.index = index[: len(pvals)]
    return params, ses, pvals


def _extract_coefficients(raw: Any) -> tuple[pd.Series, pd.Series, pd.Series]:
    frame = _coefficient_frame_from_raw(raw)
    if frame is not None:
        return _extract_from_frame(frame)

    names = _first_existing_attr(raw, ["variables", "varnames", "regressors", "x_names"])
    params = _series_from_any(
        _first_existing_attr(raw, ["params", "coef", "coefs", "coefficients"]), names=names
    )
    ses = _series_from_any(
        _first_existing_attr(raw, ["std_errors", "stderr", "std_err", "se", "standard_errors"]),
        names=params.index if len(params) else names,
    )
    pvals = _series_from_any(
        _first_existing_attr(raw, ["pvalues", "p_values", "pvals", "p"]),
        names=params.index if len(params) else names,
    )
    return params, ses, pvals


def _extract_number_from_output(patterns: Sequence[str], output: str) -> float | None:
    for pattern in patterns:
        match = re.search(pattern, output, flags=re.IGNORECASE | re.MULTILINE)
        if match:
            return _to_float_or_none(match.group(1))
    return None


def _extract_metadata(raw: Any, output: str) -> dict[str, int | float | None]:
    nobs = _to_int_or_none(_first_existing_attr(raw, ["nobs", "n_obs", "N", "num_obs"]))

    n_groups = _to_int_or_none(
        _first_existing_attr(raw, ["n_groups", "N_g", "num_groups", "groups"])
    )

    n_instruments = _to_int_or_none(
        _first_existing_attr(
            raw,
            ["n_instruments", "num_instruments", "j", "instrument_count"],
        )
    )

    hansen_p = _valid_p_value(
        _to_float_or_none(
            _first_existing_attr(raw, ["hansen_p", "hansen", "hansen_pvalue"])
        )
    )

    sargan_p = _valid_p_value(
        _to_float_or_none(
            _first_existing_attr(raw, ["sargan_p", "sargan", "sargan_pvalue"])
        )
    )

    ar1_p = _valid_p_value(
        _to_float_or_none(
            _first_existing_attr(raw, ["ar1_p", "ar1", "ar1_pvalue", "m1_p", "m1_pvalue"])
        )
    )

    ar2_p = _valid_p_value(
        _to_float_or_none(
            _first_existing_attr(raw, ["ar2_p", "ar2", "ar2_pvalue", "m2_p", "m2_pvalue"])
        )
    )

    if nobs is None:
        nobs = _to_int_or_none(
            _extract_number_from_output(
                [
                    r"number of obs(?:ervations)?\s*[=:]\s*([0-9]+)",
                    r"obs(?:ervations)?\s*[=:]\s*([0-9]+)",
                ],
                output,
            )
        )

    if n_groups is None:
        n_groups = _to_int_or_none(
            _extract_number_from_output(
                [
                    r"number of groups\s*[=:]\s*([0-9]+)",
                    r"groups\s*[=:]\s*([0-9]+)",
                ],
                output,
            )
        )

    if n_instruments is None:
        n_instruments = _to_int_or_none(
            _extract_number_from_output(
                [
                    r"number of instruments\s*[=:]\s*([0-9]+)",
                    r"instruments\s*[=:]\s*([0-9]+)",
                ],
                output,
            )
        )

    if hansen_p is None:
        hansen_p = _valid_p_value(
            _extract_number_from_output(
                [r"hansen[^\n]*(?:p|prob|pr)[^0-9.]*([0-9]*\.?[0-9]+)"],
                output,
            )
        )

    if sargan_p is None:
        sargan_p = _valid_p_value(
            _extract_number_from_output(
                [r"sargan[^\n]*(?:p|prob|pr)[^0-9.]*([0-9]*\.?[0-9]+)"],
                output,
            )
        )

    if ar1_p is None:
        ar1_p = _valid_p_value(
            _extract_number_from_output(
                [r"ar\s*\(?1\)?[^\n]*(?:p|prob|pr)[^0-9.]*([0-9]*\.?[0-9]+)"],
                output,
            )
        )

    if ar2_p is None:
        ar2_p = _valid_p_value(
            _extract_number_from_output(
                [r"ar\s*\(?2\)?[^\n]*(?:p|prob|pr)[^0-9.]*([0-9]*\.?[0-9]+)"],
                output,
            )
        )

    return {
        "nobs": nobs,
        "n_groups": n_groups,
        "n_instruments": n_instruments,
        "hansen_p": _valid_p_value(hansen_p),
        "sargan_p": _valid_p_value(sargan_p),
        "ar1_p": _valid_p_value(ar1_p),
        "ar2_p": _valid_p_value(ar2_p),
    }

def _debug_summarize_pydynpd_value(value: Any, *, depth: int = 0, max_depth: int = 4) -> Any:
    """Return a JSON-safe structural summary of a pydynpd object/value."""
    if depth > max_depth:
        return {"type": type(value).__name__, "repr": repr(value)[:200]}

    if value is None or isinstance(value, (bool, int, float, str)):
        return value

    if isinstance(value, np.ndarray):
        flat = value.reshape(-1) if value.size else value
        sample = flat[:5].tolist() if value.size else []
        return {
            "type": "ndarray",
            "shape": list(value.shape),
            "dtype": str(value.dtype),
            "sample": sample,
        }

    if isinstance(value, pd.Series):
        return {
            "type": "Series",
            "shape": [int(value.shape[0])],
            "name": value.name,
            "dtype": str(value.dtype),
            "head": value.head(5).tolist(),
        }

    if isinstance(value, pd.DataFrame):
        return {
            "type": "DataFrame",
            "shape": list(value.shape),
            "columns": [str(c) for c in value.columns[:20]],
        }

    if isinstance(value, dict):
        return {
            "type": "dict",
            "len": len(value),
            "items": {
                str(k): _debug_summarize_pydynpd_value(v, depth=depth + 1, max_depth=max_depth)
                for k, v in list(value.items())[:20]
            },
        }

    if isinstance(value, (list, tuple)):
        return {
            "type": type(value).__name__,
            "len": len(value),
            "items": [
                _debug_summarize_pydynpd_value(v, depth=depth + 1, max_depth=max_depth)
                for v in list(value)[:10]
            ],
        }

    attrs = getattr(value, "__dict__", None)
    if isinstance(attrs, dict):
        public_attrs = {str(k): v for k, v in attrs.items() if not str(k).startswith("__")}
        return {
            "type": f"{type(value).__module__}.{type(value).__name__}",
            "attrs": {
                k: _debug_summarize_pydynpd_value(v, depth=depth + 1, max_depth=max_depth)
                for k, v in list(public_attrs.items())[:80]
            },
        }

    return {"type": type(value).__name__, "repr": repr(value)[:300]}


def _write_pydynpd_debug_dump(
    raw: Any,
    *,
    spec: DynamicPanelSpec,
    command: str,
    panel_ids: Sequence[str],
) -> None:
    """Write optional pydynpd raw-object structure for strict-parity diagnosis."""
    dump_dir_raw = os.getenv("SYSTEMGMMKIT_PYDYNPD_DEBUG_DIR")
    if not dump_dir_raw:
        return

    dump_dir = Path(dump_dir_raw)
    dump_dir.mkdir(parents=True, exist_ok=True)

    safe_name = "".join(ch if ch.isalnum() or ch in "-_." else "_" for ch in spec.name)
    out = dump_dir / f"{safe_name}.json"

    payload = {
        "spec": spec.name,
        "system": bool(spec.system),
        "command": command,
        "panel_ids": list(panel_ids),
        "raw_summary": _debug_summarize_pydynpd_value(raw),
    }

    out.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")

    # Also write selected numeric arrays for strict-parity matrix diagnostics.
    # This is intentionally inactive unless SYSTEMGMMKIT_PYDYNPD_DEBUG_DIR is set.
    arrays: dict[str, Any] = {}

    try:
        if hasattr(raw, "_zs_list"):
            arrays["raw__zs_list"] = raw._zs_list
        if raw.models:
            model = raw.models[0]

            if hasattr(model, "z_list"):
                arrays["model_z_list"] = model.z_list
            if hasattr(model, "_z_t_list"):
                arrays["model__z_t_list"] = model._z_t_list

            final_xy = getattr(model, "final_xy_tables", None)
            if isinstance(final_xy, dict):
                if "Cy" in final_xy:
                    arrays["model_Cy"] = final_xy["Cy"]
                if "Cx" in final_xy:
                    arrays["model_Cx"] = final_xy["Cx"]

            for idx, step in enumerate(getattr(model, "step_results", []) or []):
                for attr in (
                    "W",
                    "W_inv",
                    "_XZ_W",
                    "M",
                    "_M_XZ_W",
                    "beta",
                    "residual",
                    "_residual_t",
                    "SS",
                    "zs",
                    "ZuuZ",
                    "W_next",
                    "vcov",
                    "std_err",
                ):
                    if hasattr(step, attr):
                        arrays[f"step{idx}_{attr}"] = getattr(step, attr)

        if arrays:
            np.savez_compressed(dump_dir / f"{safe_name}.npz", **arrays)
    except Exception as exc:
        error_path = dump_dir / f"{safe_name}.npz_error.txt"
        error_path.write_text(repr(exc), encoding="utf-8")


def _adapt_pydynpd_result(raw: Any, *, command: str, raw_output: str) -> PydynpdGMMResult:
    params, std_errors, pvalues = _extract_coefficients(raw)
    meta = _extract_metadata(raw, raw_output)
    return PydynpdGMMResult(
        params=params,
        std_errors=std_errors,
        pvalues=pvalues,
        nobs=meta["nobs"],
        n_groups=meta["n_groups"],
        n_instruments=meta["n_instruments"],
        hansen_p=_valid_p_value(meta["hansen_p"]),
        sargan_p=_valid_p_value(meta["sargan_p"]),
        ar1_p=_valid_p_value(meta["ar1_p"]),
        ar2_p=_valid_p_value(meta["ar2_p"]),
        command=command,
        raw_output=raw_output,
        raw_result=raw,
    )


def run_pydynpd(
    spec: DynamicPanelSpec,
    data: pd.DataFrame,
    panel_ids: Sequence[str],
    *,
    command_override: str | None = None,
    return_errors: bool = False,
) -> PydynpdGMMResult:
    """Run a specification using pydynpd and return a structured adapter.

    Compatibility shims are applied inside ``systemgmmkit`` so users do not need
    to manually patch the installed ``pydynpd`` package in ``.venv``.
    """

    if len(panel_ids) != 2:
        raise ValueError("panel_ids must contain exactly [entity_id, time_id].")

    _apply_numpy_compatibility_shims()
    command = command_override or build_pydynpd_command(spec)

    try:
        regression = importlib.import_module("pydynpd.regression")
    except ModuleNotFoundError as exc:
        raise ImportError(
            "pydynpd is required for estimation. Install it with: "
            "python -m pip install 'systemgmmkit[pydynpd]'"
        ) from exc

    buffer = io.StringIO()
    try:
        with contextlib.redirect_stdout(buffer):
            raw = regression.abond(command, data.copy(), list(panel_ids))
        _write_pydynpd_debug_dump(raw, spec=spec, command=command, panel_ids=panel_ids)
        return _adapt_pydynpd_result(raw, command=command, raw_output=buffer.getvalue())
    except Exception as exc:
        output = buffer.getvalue()
        if return_errors:
            return PydynpdGMMResult(
                params=pd.Series(dtype="float64"),
                std_errors=pd.Series(dtype="float64"),
                pvalues=pd.Series(dtype="float64"),
                command=command,
                raw_output=output,
                error=f"{type(exc).__name__}: {exc}",
            )
        tb = traceback.format_exc()
        raise RuntimeError(
            "pydynpd estimation failed inside systemgmmkit. "
            f"Command: {command!r}. Original error: {type(exc).__name__}: {exc}\n"
            f"Traceback:\n{tb}"
        ) from exc
