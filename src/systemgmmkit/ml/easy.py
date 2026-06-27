from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from .adapter import adapt_result
from .backtest import backtest_forecast
from .forecast import forecast
from .metrics import regression_metrics
from .prediction import fitted_values, predict, residuals

_DIAGNOSTIC_ATTRS = (
    "hansen_p",
    "sargan_p",
    "diff_hansen_p",
    "ar1_p",
    "ar2_p",
    "n_instruments",
    "n_groups",
    "nobs",
    "overid_df",
    "converged",
    "succeeded",
)


@dataclass(frozen=True)
class PostEstimationSummary:
    """Compact post-estimation bundle for common result inspection."""

    predictions: pd.Series | None = None
    fitted: pd.Series | None = None
    residuals: pd.Series | None = None
    metrics: dict[str, float] = field(default_factory=dict)
    confidence_intervals: pd.DataFrame | None = None
    marginal_effects: pd.DataFrame | None = None
    linear_combinations: pd.DataFrame | None = None
    wald_tests: pd.DataFrame | None = None
    covariance: pd.DataFrame | None = None
    diagnostics: dict[str, Any] = field(default_factory=dict)
    errors: dict[str, str] = field(default_factory=dict)

    def frames(self) -> dict[str, pd.DataFrame | pd.Series]:
        out: dict[str, pd.DataFrame | pd.Series] = {}
        for name in (
            "predictions",
            "fitted",
            "residuals",
            "confidence_intervals",
            "marginal_effects",
            "linear_combinations",
            "wald_tests",
            "covariance",
        ):
            value = getattr(self, name)
            if value is not None:
                out[name] = value
        return out

    def to_markdown(self) -> str:
        lines = ["# Post-estimation summary", ""]

        if self.metrics:
            lines.extend(["## Metrics", "", _dict_table(self.metrics), ""])

        if self.diagnostics:
            lines.extend(["## Diagnostics", "", _dict_table(self.diagnostics), ""])

        if self.confidence_intervals is not None:
            lines.extend([
                "## Confidence intervals",
                "",
                self.confidence_intervals.to_markdown(),
                "",
            ])

        if self.marginal_effects is not None:
            lines.extend([
                "## Marginal effects",
                "",
                self.marginal_effects.to_markdown(index=False),
                "",
            ])

        if self.linear_combinations is not None:
            lines.extend([
                "## Linear combinations",
                "",
                self.linear_combinations.to_markdown(index=False),
                "",
            ])

        if self.wald_tests is not None:
            lines.extend([
                "## Wald tests",
                "",
                self.wald_tests.to_markdown(index=False),
                "",
            ])

        if self.errors:
            lines.extend(["## Skipped items", "", _dict_table(self.errors), ""])

        return "\n".join(lines).rstrip()


@dataclass(frozen=True)
class ForecastSummary:
    """Compact forecast bundle with optional holdout metrics and backtest output."""

    forecast: pd.DataFrame
    metrics: dict[str, float] = field(default_factory=dict)
    backtest: pd.DataFrame | None = None
    errors: dict[str, str] = field(default_factory=dict)

    def to_markdown(self, *, max_rows: int = 10) -> str:
        lines = ["# Forecast summary", ""]

        if self.metrics:
            lines.extend(["## Metrics", "", _dict_table(self.metrics), ""])

        lines.extend([
            "## Forecast",
            "",
            self.forecast.head(max_rows).to_markdown(index=False),
            "",
        ])

        if self.backtest is not None:
            lines.extend([
                "## Backtest",
                "",
                self.backtest.head(max_rows).to_markdown(index=False),
                "",
            ])

        if self.errors:
            lines.extend(["## Skipped items", "", _dict_table(self.errors), ""])

        return "\n".join(lines).rstrip()


@dataclass(frozen=True)
class MLWorkflowSummary:
    """One object for the common evaluate-then-optionally-forecast workflow."""

    postestimation: PostEstimationSummary
    forecast: ForecastSummary | None = None

    @property
    def metrics(self) -> dict[str, float]:
        return dict(self.postestimation.metrics)

    def to_markdown(self) -> str:
        parts = [self.postestimation.to_markdown()]
        if self.forecast is not None:
            parts.append(self.forecast.to_markdown())
        return "\n\n".join(parts)


def quick_postestimation(
    result: Any,
    data: pd.DataFrame | None = None,
    *,
    y: str | None = None,
    alpha: float = 0.05,
    variables: Sequence[str] | None = None,
    lincoms: Mapping[str, Any] | Sequence[str] | str | None = None,
    wald_tests: Mapping[str, Any] | Sequence[str] | str | None = None,
    include_intervals: bool = True,
    include_effects: bool = True,
    include_vcov: bool = False,
    strict: bool = True,
    raise_on_error: bool = False,
) -> PostEstimationSummary:
    """Run common post-estimation calls in one wrapper-only step.

    This helper composes existing prediction, metrics, interval, marginal-effect,
    and diagnostics utilities. It does not estimate or modify a model.
    """

    errors: dict[str, str] = {}
    predictions = _try(
        "predictions",
        errors,
        raise_on_error,
        lambda: predict(result, data, strict=strict) if data is not None else None,
    )
    fitted = _try(
        "fitted",
        errors,
        raise_on_error,
        lambda: fitted_values(result, data, strict=strict) if data is not None else fitted_values(result),
    )
    resid = _try(
        "residuals",
        errors,
        raise_on_error,
        lambda: residuals(result, data, y=y, strict=strict)
        if data is not None and y is not None
        else residuals(result),
    )

    metrics: dict[str, float] = {}
    if data is not None and y is not None and predictions is not None:
        metric_result = _try(
            "metrics",
            errors,
            raise_on_error,
            lambda: regression_metrics(data[y], predictions),
        )
        if isinstance(metric_result, Mapping):
            metrics = dict(metric_result)

    diagnostics = _extract_diagnostics(result)

    confidence_intervals = None
    marginal_effect_frame = None
    lincom_frame = None
    wald_frame = None
    covariance = None

    if include_intervals:
        confidence_intervals = _try(
            "confidence_intervals",
            errors,
            raise_on_error,
            lambda: _postestimation_func("confint")(result, alpha=alpha),
        )

    if include_effects:
        marginal_effect_frame = _try(
            "marginal_effects",
            errors,
            raise_on_error,
            lambda: _postestimation_func("marginal_effects")(
                result,
                variables=variables,
                alpha=alpha,
            ),
        )

    if lincoms is not None:
        lincom_frame = _try(
            "linear_combinations",
            errors,
            raise_on_error,
            lambda: _lincom_frame(result, lincoms, alpha=alpha),
        )

    if wald_tests is not None:
        wald_frame = _try(
            "wald_tests",
            errors,
            raise_on_error,
            lambda: _wald_frame(result, wald_tests, alpha=alpha),
        )

    if include_vcov:
        covariance = _try(
            "covariance",
            errors,
            raise_on_error,
            lambda: _postestimation_func("vcov")(result),
        )

    return PostEstimationSummary(
        predictions=predictions if isinstance(predictions, pd.Series) else None,
        fitted=fitted if isinstance(fitted, pd.Series) else None,
        residuals=resid if isinstance(resid, pd.Series) else None,
        metrics=metrics,
        confidence_intervals=(
            confidence_intervals
            if isinstance(confidence_intervals, pd.DataFrame)
            else None
        ),
        marginal_effects=(
            marginal_effect_frame
            if isinstance(marginal_effect_frame, pd.DataFrame)
            else None
        ),
        linear_combinations=lincom_frame if isinstance(lincom_frame, pd.DataFrame) else None,
        wald_tests=wald_frame if isinstance(wald_frame, pd.DataFrame) else None,
        covariance=covariance if isinstance(covariance, pd.DataFrame) else None,
        diagnostics=diagnostics,
        errors=errors,
    )


def quick_forecast(
    result: Any,
    history: pd.DataFrame,
    *,
    y: str,
    entity: str,
    time: str,
    horizon: int = 1,
    future_exog: pd.DataFrame | None = None,
    actuals: pd.DataFrame | None = None,
    result_factory: Any | None = None,
    backtest: bool = False,
    backtest_kwargs: Mapping[str, Any] | None = None,
    forecast_kwargs: Mapping[str, Any] | None = None,
    strict: bool = True,
    raise_on_error: bool = False,
) -> ForecastSummary:
    """Forecast and optionally score/backtest with one wrapper-only call."""

    errors: dict[str, str] = {}
    forecast_kwargs = dict(forecast_kwargs or {})

    fc = _try(
        "forecast",
        errors,
        raise_on_error,
        lambda: forecast(
            result,
            history,
            y=y,
            entity=entity,
            time=time,
            horizon=horizon,
            future_exog=future_exog,
            strict=strict,
            **forecast_kwargs,
        ),
    )

    if not isinstance(fc, pd.DataFrame):
        fc = pd.DataFrame(columns=[entity, time, "horizon", "prediction"])

    score_data = actuals
    if score_data is None and future_exog is not None and y in future_exog.columns:
        score_data = future_exog

    metrics: dict[str, float] = {}
    if score_data is not None and not fc.empty:
        metric_result = _try(
            "forecast_metrics",
            errors,
            raise_on_error,
            lambda: _forecast_metrics(
                fc,
                score_data,
                y=y,
                entity=entity,
                time=time,
            ),
        )
        if isinstance(metric_result, Mapping):
            metrics = dict(metric_result)

    backtest_frame = None
    if backtest:
        if result_factory is None:
            errors["backtest"] = "result_factory is required when backtest=True."
        else:
            backtest_frame = _try(
                "backtest",
                errors,
                raise_on_error,
                lambda: backtest_forecast(
                    result_factory=result_factory,
                    data=history,
                    y=y,
                    entity=entity,
                    time=time,
                    horizon=horizon,
                    strict=strict,
                    **dict(backtest_kwargs or {}),
                ),
            )

    return ForecastSummary(
        forecast=fc,
        metrics=metrics,
        backtest=backtest_frame if isinstance(backtest_frame, pd.DataFrame) else None,
        errors=errors,
    )


def quick_ml(
    result: Any,
    data: pd.DataFrame,
    *,
    y: str,
    entity: str | None = None,
    time: str | None = None,
    horizon: int | None = None,
    future_exog: pd.DataFrame | None = None,
    postestimation_kwargs: Mapping[str, Any] | None = None,
    forecast_kwargs: Mapping[str, Any] | None = None,
) -> MLWorkflowSummary:
    """Evaluate a fitted result and optionally forecast in one easy workflow."""

    post = quick_postestimation(
        result,
        data,
        y=y,
        **dict(postestimation_kwargs or {}),
    )

    fc = None
    if horizon is not None and horizon > 0:
        if entity is None or time is None:
            errors = {
                "forecast": "entity and time are required when horizon is supplied."
            }
            fc = ForecastSummary(
                forecast=pd.DataFrame(columns=["horizon", "prediction"]),
                errors=errors,
            )
        else:
            fc = quick_forecast(
                result,
                data,
                y=y,
                entity=entity,
                time=time,
                horizon=horizon,
                future_exog=future_exog,
                **dict(forecast_kwargs or {}),
            )

    return MLWorkflowSummary(postestimation=post, forecast=fc)


def _try(
    name: str,
    errors: dict[str, str],
    raise_on_error: bool,
    func: Any,
) -> Any:
    try:
        return func()
    except Exception as exc:
        if raise_on_error:
            raise
        errors[name] = f"{type(exc).__name__}: {exc}"
        return None


def _extract_diagnostics(result: Any) -> dict[str, Any]:
    diagnostics: dict[str, Any] = {}

    try:
        adapter_diagnostics = adapt_result(result).diagnostics
    except Exception:
        adapter_diagnostics = {}

    if isinstance(adapter_diagnostics, Mapping):
        diagnostics.update(dict(adapter_diagnostics))

    if isinstance(result, Mapping):
        raw = result.get("diagnostics", {})
        if isinstance(raw, Mapping):
            diagnostics.update(dict(raw))
        for name in _DIAGNOSTIC_ATTRS:
            if name in result:
                diagnostics.setdefault(name, result[name])
    else:
        raw = getattr(result, "diagnostics", {})
        raw = raw() if callable(raw) else raw
        if isinstance(raw, Mapping):
            diagnostics.update(dict(raw))
        for name in _DIAGNOSTIC_ATTRS:
            if hasattr(result, name):
                value = getattr(result, name)
                diagnostics.setdefault(name, value() if callable(value) else value)

    return {
        str(key): value
        for key, value in diagnostics.items()
        if value is None or isinstance(value, (int, float, str, bool))
    }


def _postestimation_func(name: str) -> Any:
    import systemgmmkit.postestimation as postestimation

    return getattr(postestimation, name)


def _named_items(values: Mapping[str, Any] | Sequence[str] | str) -> list[tuple[str, Any]]:
    if isinstance(values, str):
        return [(values, values)]
    if isinstance(values, Mapping):
        return [(str(name), expression) for name, expression in values.items()]
    return [(str(expression), expression) for expression in values]


def _lincom_frame(
    result: Any,
    lincoms: Mapping[str, Any] | Sequence[str] | str,
    *,
    alpha: float,
) -> pd.DataFrame:
    lincom_func = _postestimation_func("lincom")
    rows: list[dict[str, Any]] = []

    for name, expression in _named_items(lincoms):
        row = {"name": name, **lincom_func(result, expression, alpha=alpha)}
        rows.append(row)

    return pd.DataFrame(rows)


def _wald_frame(
    result: Any,
    wald_tests: Mapping[str, Any] | Sequence[str] | str,
    *,
    alpha: float,
) -> pd.DataFrame:
    wald_func = _postestimation_func("wald_test")
    rows: list[dict[str, Any]] = []

    for name, expression in _named_items(wald_tests):
        row = {"name": name, **wald_func(result, expression, alpha=alpha)}
        rows.append(row)

    return pd.DataFrame(rows)


def _forecast_metrics(
    forecast_frame: pd.DataFrame,
    actuals: pd.DataFrame,
    *,
    y: str,
    entity: str,
    time: str,
) -> dict[str, float]:
    actual = actuals[[entity, time, y]].copy()
    merged = forecast_frame.merge(
        actual,
        on=[entity, time],
        how="inner",
        validate="one_to_one",
    )
    if merged.empty:
        raise ValueError("No matched forecast/actual rows were available.")
    return regression_metrics(merged[y], merged["prediction"])


def _dict_table(values: Mapping[str, Any]) -> str:
    frame = pd.DataFrame(
        [
            {
                "name": key,
                "value": _format_value(value),
            }
            for key, value in values.items()
        ]
    )
    return frame.to_markdown(index=False)


def _format_value(value: Any) -> Any:
    if isinstance(value, float):
        return f"{value:.4g}"
    return value
