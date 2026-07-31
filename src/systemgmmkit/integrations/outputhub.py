"""Universal Output Hub adapter for systemgmmkit model results."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pandas as pd

_RESULT_PROFILES = {
    "LinearModelResult": ("Pooled OLS", "pooled_ols"),
    "FirstDifferenceResult": ("First-difference OLS", "first_difference_ols"),
    "FixedEffectsResult": ("Fixed effects", "fixed_effects"),
    "RandomEffectsResult": ("Random effects", "random_effects"),
    "PanelIVResult": ("Panel IV/2SLS", "panel_iv_2sls"),
    "PydynpdGMMResult": ("Dynamic-panel GMM", "dynamic_panel_gmm"),
}


def _regression_model_class() -> Any:
    try:
        from universal_output_hub import RegressionModel
    except ImportError as error:
        raise ImportError(
            "Universal Output Hub is required for this integration. "
            "Install systemgmmkit with the 'outputhub' extra."
        ) from error
    return RegressionModel


def _series(
    result: Any,
    attributes: tuple[str, ...],
    *,
    label: str,
    index: pd.Index | None = None,
) -> pd.Series:
    attribute = next(
        (candidate for candidate in attributes if getattr(result, candidate, None) is not None),
        attributes[0],
    )
    value = getattr(result, attribute, None)
    if value is None:
        choices = " or ".join(attributes)
        raise TypeError(f"result must expose {choices} for OutputHub {label}.")
    if isinstance(value, pd.Series):
        series = value.copy()
    elif isinstance(value, Mapping):
        series = pd.Series(dict(value))
    else:
        try:
            series = pd.Series(value, index=index)
        except Exception as error:
            raise TypeError(
                f"result.{attribute} cannot be converted to an OutputHub {label} series."
            ) from error
    if index is not None:
        if len(series) != len(index):
            raise ValueError(
                f"result.{attribute} has {len(series)} values but params has {len(index)}."
            )
        if not series.index.equals(index):
            if set(series.index) == set(index):
                series = series.reindex(index)
            else:
                series.index = index
    return series.astype(float)


def _result_profile(result: Any) -> tuple[str, str]:
    class_name = type(result).__name__
    if class_name == "NativeGMMResult":
        system = bool(getattr(getattr(result, "spec", None), "system", False))
        return ("System GMM", "system_gmm") if system else ("Difference GMM", "difference_gmm")
    return _RESULT_PROFILES.get(class_name, (class_name.removesuffix("Result"), "panel_model"))


def _clean_mapping(values: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in values.items() if value is not None}


def _model_statistics(result: Any) -> dict[str, Any]:
    return _clean_mapping(
        {
            "N": getattr(result, "nobs", None),
            "Entities": getattr(result, "n_entities", getattr(result, "n_groups", None)),
            "Instruments": getattr(result, "n_instruments", None),
            "Residual df": getattr(result, "df_resid", None),
            "R-squared": getattr(result, "r2", None),
            "Adjusted R-squared": getattr(result, "r2_adj", None),
            "Within R-squared": getattr(result, "r2_within", None),
        }
    )


def _model_diagnostics(result: Any) -> dict[str, Any]:
    diagnostics = _clean_mapping(
        {
            "Hansen p": getattr(result, "hansen_p", None),
            "Sargan p": getattr(result, "sargan_p", None),
            "Sargan statistic": getattr(result, "sargan_stat", None),
            "AR(1) p": getattr(result, "ar1_p", None),
            "AR(2) p": getattr(result, "ar2_p", None),
            "AR(1) z": getattr(result, "ar1_z", None),
            "AR(2) z": getattr(result, "ar2_z", None),
            "Hansen J": getattr(result, "hansen_j_stat", None),
            "Sargan J": getattr(result, "sargan_j_stat", None),
            "Overidentification df": getattr(result, "overid_df", None),
        }
    )
    first_stage = getattr(result, "first_stage_r2", None)
    if isinstance(first_stage, Mapping):
        diagnostics.update(
            {
                f"First-stage R-squared ({variable})": value
                for variable, value in first_stage.items()
            }
        )
    return diagnostics


def _model_metadata(result: Any, estimator: str) -> dict[str, Any]:
    spec = getattr(result, "spec", None)
    metadata = _clean_mapping(
        {
            "estimator": estimator,
            "result_class": type(result).__name__,
            "backend": getattr(result, "backend", None),
            "covariance_type": getattr(result, "covariance_type", None),
            "transformation": getattr(spec, "transformation", None),
            "steps": getattr(spec, "steps", None),
            "collapse": getattr(spec, "collapse", None),
            "system": getattr(spec, "system", None),
            "time_dummies": getattr(spec, "time_dummies", None),
        }
    )
    return metadata


def _default_name(result: Any, profile_name: str) -> str:
    model_name = getattr(result, "model_name", None)
    if isinstance(model_name, str) and model_name.strip():
        return model_name
    spec_name = getattr(getattr(result, "spec", None), "name", None)
    if isinstance(spec_name, str) and spec_name.strip():
        return spec_name.replace("_", " ").title()
    return profile_name


def _dependent_variable(result: Any, depvar: str | None) -> str | None:
    if depvar is not None:
        return depvar
    candidate = getattr(getattr(result, "spec", None), "dependent", None)
    if candidate is None:
        candidate = getattr(result, "y", None)
    return str(candidate) if candidate is not None else None


def to_outputhub_model(
    result: Any,
    *,
    name: str | None = None,
    depvar: str | None = None,
) -> Any:
    """Convert a fitted systemgmmkit result to OutputHub's canonical model."""
    params = _series(result, ("params",), label="parameter")
    std_errors = _series(
        result,
        ("std_errors", "standard_errors"),
        label="standard-error",
        index=params.index,
    )
    pvalues = _series(
        result,
        ("pvalues", "p_values"),
        label="p-value",
        index=params.index,
    )
    profile_name, estimator = _result_profile(result)
    RegressionModel = _regression_model_class()
    return RegressionModel(
        name=name or _default_name(result, profile_name),
        depvar=_dependent_variable(result, depvar),
        params=params.rename("coef"),
        std_errors=std_errors.rename("se"),
        pvalues=pvalues.rename("pvalue"),
        statistics=_model_statistics(result),
        diagnostics=_model_diagnostics(result),
        metadata=_model_metadata(result, estimator),
        source="systemgmmkit",
    )


def outputhub_diagnostics_frame(result: Any) -> pd.DataFrame:
    """Return model diagnostics in a tidy table suitable for OutputHub."""
    diagnostics = _model_diagnostics(result)
    return pd.DataFrame(
        [{"diagnostic": key, "value": value} for key, value in diagnostics.items()],
        columns=["diagnostic", "value"],
    )


def add_to_outputhub(
    hub: Any,
    result: Any,
    *,
    name: str | None = None,
    depvar: str | None = None,
    include_diagnostics: bool = False,
) -> Any:
    """Add a fitted model and, optionally, its diagnostics table to an OutputHub."""
    if not hasattr(hub, "add_model"):
        raise TypeError("hub must provide an OutputHub-compatible add_model method.")
    if include_diagnostics and not hasattr(hub, "add_table"):
        raise TypeError(
            "hub must provide an OutputHub-compatible add_table method when "
            "include_diagnostics=True."
        )
    model = to_outputhub_model(result, name=name, depvar=depvar)
    hub.add_model(model)
    if include_diagnostics:
        diagnostics = outputhub_diagnostics_frame(result)
        if not diagnostics.empty:
            hub.add_table(
                f"{model.name} diagnostics",
                diagnostics,
                caption="Estimator-specific diagnostics reported by systemgmmkit.",
                metadata={
                    "source": "systemgmmkit",
                    "estimator": model.metadata["estimator"],
                },
            )
    return model
