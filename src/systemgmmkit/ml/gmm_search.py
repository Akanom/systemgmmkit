from __future__ import annotations

import math
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from itertools import product
from pathlib import Path
from typing import Any

import pandas as pd

from .metrics import regression_metrics
from .prediction import predict
from .split import panel_train_test_split

LagWindow = tuple[int, int]
DiagnosticRule = tuple[str, float]
DiagnosticPolicy = str

_SCALAR_TYPES = (int, float, str, bool)
_DIAGNOSTIC_ATTRS = (
    "hansen_p",
    "sargan_p",
    "diff_hansen_p",
    "ar1_p",
    "ar2_p",
    "n_instruments",
    "n_groups",
    "nobs",
    "n_obs",
    "overid_df",
    "j_stat",
    "hansen_j_stat",
    "sargan_j_stat",
    "converged",
    "succeeded",
    "success",
)


@dataclass(frozen=True)
class GMMValidityRules:
    """Conservative validity rules for dynamic-panel GMM specification search.

    The rules only inspect diagnostics exposed by already-fitted result objects.
    They do not alter estimator behavior, instrument construction, covariance
    logic, or result semantics.
    """

    min_hansen_p: float | None = 0.05
    max_hansen_p: float | None = 0.99
    min_ar2_p: float | None = 0.05
    max_instrument_ratio: float | None = 1.0
    max_instruments: int | None = None
    require_hansen: bool = True
    require_ar2: bool = True
    require_convergence: bool = True
    convergence_keys: tuple[str, ...] = ("converged", "succeeded", "success")
    diagnostic_policy: DiagnosticPolicy = "strict"

    def rejection_reasons(
        self,
        diagnostics: Mapping[str, Any],
        *,
        candidate: Mapping[str, Any] | None = None,
    ) -> list[str]:
        reasons: list[str] = []
        policy = _normalise_diagnostic_policy(self.diagnostic_policy)
        system_candidate = _is_system_candidate(candidate=candidate, diagnostics=diagnostics)
        require_hansen = self.require_hansen and policy != "reported"
        require_ar2 = self.require_ar2 and policy != "reported"

        if policy == "system_ar2_relaxed" and system_candidate:
            require_ar2 = False

        if self.require_convergence:
            converged = _first_present(diagnostics, self.convergence_keys)
            if converged is not None and not _truthy(converged):
                reasons.append("convergence_failed")

        hansen_p = _diagnostic_float(diagnostics, "hansen_p")
        if hansen_p is None:
            if require_hansen:
                reasons.append("missing_hansen_p")
        else:
            if self.min_hansen_p is not None and hansen_p <= self.min_hansen_p:
                reasons.append("hansen_p_too_low")
            if self.max_hansen_p is not None and hansen_p >= self.max_hansen_p:
                reasons.append("hansen_p_too_high")

        ar2_p = _diagnostic_float(diagnostics, "ar2_p")
        if ar2_p is None:
            if require_ar2:
                reasons.append("missing_ar2_p")
        elif self.min_ar2_p is not None and ar2_p <= self.min_ar2_p:
            reasons.append("ar2_p_too_low")

        n_instruments = _diagnostic_int(diagnostics, "n_instruments")
        n_groups = _diagnostic_int(diagnostics, "n_groups")

        if (
            self.max_instruments is not None
            and n_instruments is not None
            and n_instruments > self.max_instruments
        ):
            reasons.append("too_many_instruments")

        if (
            self.max_instrument_ratio is not None
            and n_instruments is not None
            and n_groups is not None
            and n_groups > 0
            and n_instruments > self.max_instrument_ratio * n_groups
        ):
            reasons.append("instrument_count_exceeds_groups")

        return reasons

    def diagnostic_availability(
        self,
        diagnostics: Mapping[str, Any],
        *,
        candidate: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Return backend-aware diagnostic availability metadata.

        This is deliberately separate from rejection reasons: a diagnostic can
        be unreported without being treated as failed under a non-strict policy.
        """

        policy = _normalise_diagnostic_policy(self.diagnostic_policy)
        system_candidate = _is_system_candidate(candidate=candidate, diagnostics=diagnostics)
        available = [
            key
            for key in ("hansen_p", "sargan_p", "ar1_p", "ar2_p")
            if _diagnostic_float(diagnostics, key) is not None
        ]
        missing = [
            key
            for key in ("hansen_p", "ar2_p")
            if _diagnostic_float(diagnostics, key) is None
        ]

        required: list[str] = []
        if policy != "reported":
            if self.require_hansen:
                required.append("hansen_p")
            if self.require_ar2 and not (policy == "system_ar2_relaxed" and system_candidate):
                required.append("ar2_p")

        missing_required = [key for key in required if key in missing]

        return {
            "diagnostic_policy": policy,
            "system_gmm_candidate": system_candidate,
            "available_diagnostics": ";".join(available),
            "missing_diagnostics": ";".join(missing),
            "required_diagnostics": ";".join(required),
            "missing_required_diagnostics": ";".join(missing_required),
        }


@dataclass(frozen=True)
class GMMRankingWeights:
    """Weights for ranking valid candidate specifications.

    Validity filtering happens before ranking. The composite score is therefore
    a tie-breaker among defensible candidates, not a substitute for diagnostics.
    Lower scores are better.
    """

    prediction: float = 1.0
    instruments: float = 0.20
    hansen: float = 0.15
    ar2: float = 0.10


@dataclass(frozen=True)
class GMMSearchResult:
    results: pd.DataFrame
    best_result: Any | None
    best_spec: dict[str, Any] | None
    best_row: dict[str, Any] | None = None
    selection_metric: str = "rmse"
    report: str = ""

    def to_markdown(self, *, max_rows: int = 10) -> str:
        """Return a compact optimizer report in Markdown."""

        if max_rows == 10 and self.report:
            return self.report
        return _build_search_report(
            self.results,
            best_row=self.best_row,
            selection_metric=self.selection_metric,
            max_rows=max_rows,
        )

    def write_report(self, path: str | Path, *, max_rows: int = 25) -> Path:
        """Write the optimizer report to disk and return the resolved path."""

        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(self.to_markdown(max_rows=max_rows), encoding="utf-8")
        return out


def dynamic_gmm_candidate_grid(
    *,
    models: Sequence[str] = ("system", "difference"),
    steps: Sequence[str] = ("twostep", "onestep"),
    lag_windows: Sequence[LagWindow] = ((2, 2), (2, 3), (2, 4), (3, 4)),
    transformations: Sequence[str] = ("fod", "fd"),
    collapse_options: Sequence[bool] = (True,),
    windmeijer_options: Sequence[bool | None] = (None,),
    time_effects_options: Sequence[bool] = (False,),
    backend_options: Sequence[str] = ("auto",),
    extra_grid: Mapping[str, Sequence[Any]] | None = None,
    skip_invalid: bool = True,
) -> list[dict[str, Any]]:
    """Generate candidate parameter dictionaries for the Dynamic GMM loop.

    The generated candidates are intended for the public easy API wrappers. The
    function only builds orchestration metadata; it does not construct
    instruments or estimate a model.
    """

    model_values = _as_tuple(models, name="models")
    step_values = _as_tuple(steps, name="steps")
    lag_values = _as_tuple(lag_windows, name="lag_windows")
    transformation_values = _as_tuple(transformations, name="transformations")
    collapse_values = _as_tuple(collapse_options, name="collapse_options")
    windmeijer_values = _as_tuple(windmeijer_options, name="windmeijer_options")
    time_effect_values = _as_tuple(time_effects_options, name="time_effects_options")
    backend_values = _as_tuple(backend_options, name="backend_options")

    extra_keys = list(extra_grid or {})
    extra_values = [
        _as_tuple((extra_grid or {})[key], name=f"extra_grid[{key!r}]")
        for key in extra_keys
    ]

    candidates: list[dict[str, Any]] = []

    for combo in product(
        model_values,
        step_values,
        lag_values,
        transformation_values,
        collapse_values,
        windmeijer_values,
        time_effect_values,
        backend_values,
        *extra_values,
    ):
        (
            model,
            step,
            lag_window,
            transformation,
            collapse,
            windmeijer,
            time_effects,
            backend,
            *extra,
        ) = combo

        model = str(model).strip().lower()
        step = str(step).strip().lower()
        transformation = str(transformation).strip().lower()

        if model not in {"system", "difference"}:
            raise ValueError("models must contain only 'system' and/or 'difference'.")
        if step not in {"onestep", "twostep", "iterated"}:
            raise ValueError("steps must contain only 'onestep', 'twostep', or 'iterated'.")
        if transformation not in {"fd", "fod"}:
            raise ValueError("transformations must contain only 'fd' and/or 'fod'.")

        lag_window = _validate_lag_window(lag_window)

        if skip_invalid and windmeijer is True and step == "onestep":
            continue

        candidate = {
            "model": model,
            "steps": step,
            "gmm_lags": lag_window,
            "transformation": transformation,
            "collapse": bool(collapse),
            "windmeijer": windmeijer,
            "time_effects": bool(time_effects),
            "backend": backend,
        }

        for key, value in zip(extra_keys, extra):
            candidate[key] = value

        candidates.append(candidate)

    return candidates


class GMMGridSearch:
    """
    GMM specification search around an existing estimator.

    This class does NOT implement GMM estimation. It repeatedly calls the
    existing validated estimator builder/runner supplied by the user, evaluates
    diagnostics and prediction metrics, then ranks surviving specifications.
    """

    def __init__(
        self,
        *,
        build_spec: Callable[..., Any],
        run_model: Callable[..., Any],
        param_grid: Iterable[dict[str, Any]],
        y: str,
        entity: str,
        time: str,
        selection_metric: str = "rmse",
        minimize: bool = True,
        test_size: float | int = 0.2,
        diagnostic_rules: dict[str, DiagnosticRule] | None = None,
        validity_rules: GMMValidityRules | None = None,
        ranking_weights: GMMRankingWeights | None = None,
        predict_kwargs: Mapping[str, Any] | None = None,
    ) -> None:
        self.build_spec = build_spec
        self.run_model = run_model
        self.param_grid = list(param_grid)
        self.y = y
        self.entity = entity
        self.time = time
        self.selection_metric = selection_metric
        self.minimize = minimize
        self.test_size = test_size
        self.diagnostic_rules = diagnostic_rules or {}
        self.validity_rules = validity_rules
        self.ranking_weights = ranking_weights
        self.predict_kwargs = {"strict": False, **dict(predict_kwargs or {})}

    def _passes_diagnostics(self, diagnostics: Mapping[str, Any]) -> bool:
        return not _diagnostic_rule_failures(diagnostics, self.diagnostic_rules)

    def fit(self, data: pd.DataFrame) -> GMMSearchResult:
        train, test = panel_train_test_split(
            data,
            time=self.time,
            test_size=self.test_size,
        )

        rows: list[dict[str, Any]] = []
        stored_by_id: dict[int, tuple[dict[str, Any], Any]] = {}

        for i, params in enumerate(self.param_grid, start=1):
            row: dict[str, Any] = {"spec_id": i, **params}

            try:
                spec = self.build_spec(**params)
                result = self.run_model(
                    spec,
                    train,
                    entity=self.entity,
                    time=self.time,
                )

                y_pred = predict(result, test, **self.predict_kwargs)
                row.update(regression_metrics(test[self.y], y_pred))

                diagnostics = _extract_diagnostics(result)
                for key, value in diagnostics.items():
                    if _is_scalar(value):
                        row[f"diag_{key}"] = _coerce_scalar(value)

                reasons = _diagnostic_rule_failures(diagnostics, self.diagnostic_rules)
                if self.validity_rules is not None:
                    availability = self.validity_rules.diagnostic_availability(
                        diagnostics,
                        candidate=params,
                    )
                    row.update(availability)
                    reasons.extend(
                        self.validity_rules.rejection_reasons(
                            diagnostics,
                            candidate=params,
                        )
                    )

                row["passes_diagnostics"] = not reasons
                row["rejection_reason"] = "; ".join(dict.fromkeys(reasons))
                row["error"] = ""
                stored_by_id[i] = (dict(params), result)

            except Exception as exc:
                row["passes_diagnostics"] = False
                row["rejection_reason"] = "estimation_error"
                row["error"] = f"{type(exc).__name__}: {exc}"

            rows.append(row)

        table = pd.DataFrame(rows)
        table = _add_rank_scores(
            table,
            selection_metric=self.selection_metric,
            minimize=self.minimize,
            ranking_weights=self.ranking_weights,
        )

        candidates = table.loc[
            (table["error"].fillna("") == "")
            & (table["passes_diagnostics"].astype(bool))
        ].copy()

        if candidates.empty:
            return GMMSearchResult(
                results=table,
                best_result=None,
                best_spec=None,
                best_row=None,
                selection_metric=self.selection_metric,
                report=_build_search_report(
                    table,
                    best_row=None,
                    selection_metric=self.selection_metric,
                ),
            )

        if "rank_score" in candidates.columns and candidates["rank_score"].notna().any():
            candidates = candidates.sort_values("rank_score", ascending=True)
        elif self.selection_metric in candidates.columns:
            candidates = candidates.sort_values(
                self.selection_metric,
                ascending=self.minimize,
            )
        else:
            return GMMSearchResult(
                results=table,
                best_result=None,
                best_spec=None,
                best_row=None,
                selection_metric=self.selection_metric,
                report=_build_search_report(
                    table,
                    best_row=None,
                    selection_metric=self.selection_metric,
                ),
            )

        best_id = int(candidates.iloc[0]["spec_id"])
        best_spec, best_result = stored_by_id[best_id]
        best_row = candidates.iloc[0].to_dict()

        return GMMSearchResult(
            results=table,
            best_result=best_result,
            best_spec=best_spec,
            best_row=best_row,
            selection_metric=self.selection_metric,
            report=_build_search_report(
                table,
                best_row=best_row,
                selection_metric=self.selection_metric,
            ),
        )


class DynamicGMMHybridSearch:
    """Automatic Dynamic GMM specification search using public package APIs.

    The hybrid loop composes the existing easy API, diagnostics, prediction
    metrics, validity filtering, ranking, and reporting. It intentionally leaves
    estimator math and model internals untouched.
    """

    def __init__(
        self,
        *,
        y: str,
        entity: str,
        time: str,
        regressors: Sequence[str] | None = None,
        controls: Sequence[str] | None = None,
        endogenous: Sequence[str] | None = None,
        predetermined: Sequence[str] | None = None,
        exogenous: Sequence[str] | None = None,
        lagged_dependent: int | None = 1,
        lagged_dependent_role: str = "endogenous",
        param_grid: Iterable[Mapping[str, Any]] | None = None,
        models: Sequence[str] = ("system", "difference"),
        steps: Sequence[str] = ("twostep", "onestep"),
        lag_windows: Sequence[LagWindow] = ((2, 2), (2, 3), (2, 4), (3, 4)),
        transformations: Sequence[str] = ("fod", "fd"),
        collapse_options: Sequence[bool] = (True,),
        windmeijer_options: Sequence[bool | None] = (None,),
        time_effects_options: Sequence[bool] = (False,),
        backend_options: Sequence[str] = ("auto",),
        extra_grid: Mapping[str, Sequence[Any]] | None = None,
        selection_metric: str = "rmse",
        minimize: bool = True,
        test_size: float | int = 0.2,
        diagnostic_rules: dict[str, DiagnosticRule] | None = None,
        validity_rules: GMMValidityRules | None = None,
        ranking_weights: GMMRankingWeights | None = None,
        predict_kwargs: Mapping[str, Any] | None = None,
        model_options: Mapping[str, Any] | None = None,
    ) -> None:
        self.y = y
        self.entity = entity
        self.time = time
        self.regressors = tuple(regressors or ())
        self.controls = tuple(controls or ())
        self.endogenous = tuple(endogenous or ())
        self.predetermined = tuple(predetermined or ())
        self.exogenous = tuple(exogenous or ())
        self.lagged_dependent = lagged_dependent
        self.lagged_dependent_role = lagged_dependent_role
        self.param_grid = [
            dict(params)
            for params in (
                param_grid
                if param_grid is not None
                else dynamic_gmm_candidate_grid(
                    models=models,
                    steps=steps,
                    lag_windows=lag_windows,
                    transformations=transformations,
                    collapse_options=collapse_options,
                    windmeijer_options=windmeijer_options,
                    time_effects_options=time_effects_options,
                    backend_options=backend_options,
                    extra_grid=extra_grid,
                )
            )
        ]
        self.selection_metric = selection_metric
        self.minimize = minimize
        self.test_size = test_size
        self.diagnostic_rules = diagnostic_rules
        self.validity_rules = validity_rules or GMMValidityRules()
        self.ranking_weights = ranking_weights or GMMRankingWeights()
        self.predict_kwargs = dict(predict_kwargs or {})
        self.model_options = dict(model_options or {})

    def fit(self, data: pd.DataFrame) -> GMMSearchResult:
        search = GMMGridSearch(
            build_spec=lambda **params: dict(params),
            run_model=self._run_candidate,
            param_grid=self.param_grid,
            y=self.y,
            entity=self.entity,
            time=self.time,
            selection_metric=self.selection_metric,
            minimize=self.minimize,
            test_size=self.test_size,
            diagnostic_rules=self.diagnostic_rules,
            validity_rules=self.validity_rules,
            ranking_weights=self.ranking_weights,
            predict_kwargs=self.predict_kwargs,
        )
        return search.fit(data)

    def _run_candidate(
        self,
        spec: Mapping[str, Any],
        data: pd.DataFrame,
        *,
        entity: str,
        time: str,
    ) -> Any:
        from systemgmmkit import easy as easy_api

        params = dict(spec)
        model = str(params.pop("model", "system")).strip().lower()

        if "lag_window" in params and "gmm_lags" not in params:
            params["gmm_lags"] = params.pop("lag_window")

        if model == "system":
            runner = easy_api.system_gmm
        elif model == "difference":
            runner = easy_api.difference_gmm
        else:
            raise ValueError("candidate model must be 'system' or 'difference'.")

        kwargs: dict[str, Any] = {
            "data": data,
            "entity": entity,
            "time": time,
            "dependent": self.y,
            "regressors": list(self.regressors),
            "controls": list(self.controls),
            "endogenous": list(self.endogenous),
            "predetermined": list(self.predetermined),
            "exogenous": list(self.exogenous),
            "lagged_dependent": self.lagged_dependent,
            "lagged_dependent_role": self.lagged_dependent_role,
            "return_workflow": True,
        }
        kwargs.update(self.model_options)
        kwargs.update(params)
        kwargs["return_workflow"] = True

        workflow_or_result = runner(**kwargs)
        return getattr(workflow_or_result, "result", workflow_or_result)


def auto_dynamic_gmm(
    data: pd.DataFrame,
    *,
    y: str,
    entity: str,
    time: str,
    regressors: Sequence[str] | None = None,
    controls: Sequence[str] | None = None,
    endogenous: Sequence[str] | None = None,
    predetermined: Sequence[str] | None = None,
    exogenous: Sequence[str] | None = None,
    lagged_dependent: int | None = 1,
    lagged_dependent_role: str = "endogenous",
    param_grid: Iterable[Mapping[str, Any]] | None = None,
    test_size: float | int = 0.2,
    validity_rules: GMMValidityRules | None = None,
    ranking_weights: GMMRankingWeights | None = None,
    predict_kwargs: Mapping[str, Any] | None = None,
    model_options: Mapping[str, Any] | None = None,
    **search_options: Any,
) -> GMMSearchResult:
    """Run the Dynamic GMM Hybrid Loop with a compact one-call API.

    This is a convenience wrapper over ``DynamicGMMHybridSearch(...).fit(data)``.
    It does not implement estimation and does not touch model internals.
    Advanced search dimensions such as ``models``, ``steps``, ``lag_windows``,
    and ``transformations`` can be passed through ``search_options``.
    """

    search = DynamicGMMHybridSearch(
        y=y,
        entity=entity,
        time=time,
        regressors=regressors,
        controls=controls,
        endogenous=endogenous,
        predetermined=predetermined,
        exogenous=exogenous,
        lagged_dependent=lagged_dependent,
        lagged_dependent_role=lagged_dependent_role,
        param_grid=param_grid,
        test_size=test_size,
        validity_rules=validity_rules,
        ranking_weights=ranking_weights,
        predict_kwargs=predict_kwargs,
        model_options=model_options,
        **search_options,
    )
    return search.fit(data)


def _as_tuple(values: Sequence[Any], *, name: str) -> tuple[Any, ...]:
    if isinstance(values, str):
        return (values,)
    out = tuple(values)
    if not out:
        raise ValueError(f"{name} cannot be empty.")
    return out


def _validate_lag_window(value: Any) -> LagWindow:
    if not isinstance(value, tuple) or len(value) != 2:
        raise TypeError("lag windows must be tuples like (2, 4).")
    start, stop = int(value[0]), int(value[1])
    if start < 0 or stop < 0:
        raise ValueError("lag-window bounds must be non-negative.")
    if stop < start:
        raise ValueError("lag-window stop must be greater than or equal to start.")
    return start, stop


def _extract_diagnostics(result: Any) -> dict[str, Any]:
    diagnostics: dict[str, Any] = {}

    raw = getattr(result, "diagnostics", {})
    raw = raw() if callable(raw) else raw
    if isinstance(raw, Mapping):
        diagnostics.update(dict(raw))

    if isinstance(result, Mapping):
        raw = result.get("diagnostics", {})
        if isinstance(raw, Mapping):
            diagnostics.update(dict(raw))
        for name in _DIAGNOSTIC_ATTRS:
            if name in result:
                diagnostics.setdefault(name, result[name])
    else:
        for name in _DIAGNOSTIC_ATTRS:
            if hasattr(result, name):
                value = getattr(result, name)
                diagnostics.setdefault(name, value() if callable(value) else value)

    return diagnostics


def _diagnostic_float(diagnostics: Mapping[str, Any], key: str) -> float | None:
    value = diagnostics.get(key)
    if value is None:
        return None
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(out):
        return None
    return out


def _diagnostic_int(diagnostics: Mapping[str, Any], key: str) -> int | None:
    value = _diagnostic_float(diagnostics, key)
    return None if value is None else int(value)


def _first_present(diagnostics: Mapping[str, Any], keys: Sequence[str]) -> Any | None:
    for key in keys:
        if key in diagnostics:
            return diagnostics[key]
    return None


def _truthy(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() not in {"0", "false", "no", "failed", "failure"}
    return bool(value)


def _normalise_diagnostic_policy(value: str) -> str:
    policy = str(value).strip().lower().replace("-", "_")
    aliases = {
        "backend_reported": "reported",
        "available": "reported",
        "reported_only": "reported",
        "system_missing_ar2_ok": "system_ar2_relaxed",
        "system_ar2_optional": "system_ar2_relaxed",
    }
    policy = aliases.get(policy, policy)
    if policy not in {"strict", "reported", "system_ar2_relaxed"}:
        raise ValueError(
            "diagnostic_policy must be one of 'strict', 'reported', "
            "or 'system_ar2_relaxed'."
        )
    return policy


def _is_system_candidate(
    *,
    candidate: Mapping[str, Any] | None,
    diagnostics: Mapping[str, Any],
) -> bool:
    candidates = []

    if candidate is not None:
        candidates.extend(
            [
                candidate.get("model"),
                candidate.get("estimator"),
                candidate.get("gmm_estimator"),
                candidate.get("system"),
            ]
        )

    candidates.extend(
        [
            diagnostics.get("model"),
            diagnostics.get("estimator"),
            diagnostics.get("gmm_estimator"),
            diagnostics.get("system"),
        ]
    )

    for value in candidates:
        if isinstance(value, bool):
            if value:
                return True
            continue
        text = str(value).strip().lower()
        if text in {"system", "system_gmm", "true", "1"}:
            return True
    return False


def _diagnostic_rule_failures(
    diagnostics: Mapping[str, Any],
    diagnostic_rules: Mapping[str, DiagnosticRule],
) -> list[str]:
    reasons: list[str] = []

    for key, (op, threshold) in diagnostic_rules.items():
        value = _diagnostic_float(diagnostics, key)
        if value is None:
            reasons.append(f"missing_{key}")
            continue

        if op == ">" and not value > threshold:
            reasons.append(f"{key}_not_gt_{threshold:g}")
        elif op == ">=" and not value >= threshold:
            reasons.append(f"{key}_not_gte_{threshold:g}")
        elif op == "<" and not value < threshold:
            reasons.append(f"{key}_not_lt_{threshold:g}")
        elif op == "<=" and not value <= threshold:
            reasons.append(f"{key}_not_lte_{threshold:g}")
        elif op == "==" and value != threshold:
            reasons.append(f"{key}_not_eq_{threshold:g}")
        elif op not in {">", ">=", "<", "<=", "=="}:
            raise ValueError(f"Unsupported diagnostic rule operator {op!r}.")

    return reasons


def _is_scalar(value: Any) -> bool:
    return value is None or isinstance(value, _SCALAR_TYPES)


def _coerce_scalar(value: Any) -> Any:
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, (int, float)):
        return float(value)
    return value


def _add_rank_scores(
    table: pd.DataFrame,
    *,
    selection_metric: str,
    minimize: bool,
    ranking_weights: GMMRankingWeights | None,
) -> pd.DataFrame:
    out = table.copy()
    out["rank_score"] = math.nan

    if out.empty or "passes_diagnostics" not in out.columns or "error" not in out.columns:
        return out

    eligible = (out["error"].fillna("") == "") & out["passes_diagnostics"].astype(bool)
    if not eligible.any():
        return out

    if ranking_weights is None:
        if selection_metric in out.columns:
            metric_values = pd.to_numeric(
                out.loc[eligible, selection_metric],
                errors="coerce",
            )
            out.loc[eligible, "rank_score"] = (
                metric_values if minimize else -metric_values
            )
        return out

    score = pd.Series(0.0, index=out.index, dtype=float)

    score += ranking_weights.prediction * _rank_component(
        out,
        eligible=eligible,
        column=selection_metric,
        ascending=minimize,
    )
    score += ranking_weights.instruments * _rank_component(
        out,
        eligible=eligible,
        column="diag_n_instruments",
        ascending=True,
    )
    score += ranking_weights.hansen * _hansen_component(out, eligible=eligible)
    score += ranking_weights.ar2 * _rank_component(
        out,
        eligible=eligible,
        column="diag_ar2_p",
        ascending=False,
    )

    out.loc[eligible, "rank_score"] = score.loc[eligible]
    return out


def _rank_component(
    table: pd.DataFrame,
    *,
    eligible: pd.Series,
    column: str,
    ascending: bool,
) -> pd.Series:
    component = pd.Series(1.0, index=table.index, dtype=float)

    if column not in table.columns:
        return component

    values = pd.to_numeric(table.loc[eligible, column], errors="coerce")
    if values.notna().any():
        component.loc[eligible] = values.rank(
            ascending=ascending,
            pct=True,
            method="average",
        ).fillna(1.0)

    return component


def _hansen_component(table: pd.DataFrame, *, eligible: pd.Series) -> pd.Series:
    component = pd.Series(1.0, index=table.index, dtype=float)

    if "diag_hansen_p" not in table.columns:
        return component

    values = pd.to_numeric(table.loc[eligible, "diag_hansen_p"], errors="coerce")
    distance = (values - 0.50).abs()
    if distance.notna().any():
        component.loc[eligible] = distance.rank(
            ascending=True,
            pct=True,
            method="average",
        ).fillna(1.0)

    return component


def _build_search_report(
    table: pd.DataFrame,
    *,
    best_row: Mapping[str, Any] | None,
    selection_metric: str,
    max_rows: int = 10,
) -> str:
    total = int(len(table))
    passed = int(table.get("passes_diagnostics", pd.Series(dtype=bool)).fillna(False).sum())
    failed = int(table.get("error", pd.Series(dtype=str)).fillna("").ne("").sum())
    rejected = total - passed - failed

    lines = [
        "# Dynamic GMM specification search report",
        "",
        f"- Candidates evaluated: {total}",
        f"- Passed diagnostics: {passed}",
        f"- Rejected by diagnostics: {max(rejected, 0)}",
        f"- Failed during estimation/evaluation: {failed}",
        f"- Selection metric: `{selection_metric}`",
        "",
    ]

    if best_row is None:
        lines.append("No candidate passed the configured validity rules.")
    else:
        lines.extend(
            [
                "## Recommended specification",
                "",
                f"- Candidate: `{_format_value(best_row.get('spec_id'))}`",
                f"- Model: `{_format_value(best_row.get('model', 'custom'))}`",
                f"- Rank score: `{_format_value(best_row.get('rank_score'))}`",
                f"- {selection_metric}: `{_format_value(best_row.get(selection_metric))}`",
                "",
            ]
        )

    if total:
        display = table.copy()
        display = display.sort_values(
            ["passes_diagnostics", "rank_score"],
            ascending=[False, True],
            na_position="last",
        ).head(max_rows)
        columns = [
            "spec_id",
            "model",
            "steps",
            "gmm_lags",
            "collapse",
            "transformation",
            "windmeijer",
            "rank_score",
            selection_metric,
            "diag_hansen_p",
            "diag_ar2_p",
            "diag_n_instruments",
            "diag_n_groups",
            "diagnostic_policy",
            "missing_required_diagnostics",
            "passes_diagnostics",
            "rejection_reason",
            "error",
        ]
        columns = [col for col in columns if col in display.columns]
        lines.extend(
            [
                "## Candidate table",
                "",
                _markdown_table(display.loc[:, columns]),
            ]
        )

    return "\n".join(lines)


def _markdown_table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return ""

    headers = list(frame.columns)
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]

    for _, row in frame.iterrows():
        lines.append(
            "| " + " | ".join(_format_value(row[col]) for col in headers) + " |"
        )

    return "\n".join(lines)


def _format_value(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    if isinstance(value, float):
        return f"{value:.4g}"
    return str(value).replace("|", "\\|")
