from __future__ import annotations

import re
from pathlib import Path

path = Path("src/systemgmmkit/presets.py")
text = path.read_text(encoding="utf-8")

helper = r'''

def _validate_gmm_lag_window(name: str, value: object) -> tuple[int, int]:
    if not isinstance(value, tuple) or len(value) != 2:
        raise TypeError(f"{name} must be a tuple of two integers, for example (2, 4).")

    min_lag, max_lag = value

    if not isinstance(min_lag, int) or not isinstance(max_lag, int):
        raise TypeError(f"{name} must contain integer lag bounds.")

    if min_lag < 0 or max_lag < 0:
        raise ValueError(f"{name} cannot contain negative lag values.")

    if min_lag > max_lag:
        raise ValueError(f"{name} has min lag greater than max lag: {value!r}.")

    return min_lag, max_lag


def _normalise_gmm_lag_role(role: str) -> str:
    value = role.strip().lower()

    if value in {"endog", "endogenous"}:
        return "endogenous"

    if value in {"predet", "predetermined"}:
        return "predetermined"

    if value in {"exog", "exogenous"}:
        raise ValueError(
            "Exogenous variables are IV-style by default and should not be assigned "
            "GMM-style lag windows through gmm_lags_by_role. If a lagged exogenous "
            "variable belongs in the structural equation, create it as a column and "
            "include it in exogenous."
        )

    raise ValueError(
        f"Unknown GMM lag-window role {role!r}. "
        "Supported roles are 'endogenous' and 'predetermined'."
    )


def _normalise_gmm_lag_mapping(name: str, value: object) -> dict[str, tuple[int, int]]:
    if value is None:
        return {}

    if not isinstance(value, Mapping):
        raise TypeError(f"{name} must be a mapping of names to lag-window tuples.")

    out: dict[str, tuple[int, int]] = {}

    for key, window in value.items():
        if not isinstance(key, str) or not key.strip():
            raise ValueError(f"{name} keys must be non-empty strings.")

        out[key] = _validate_gmm_lag_window(f"{name}[{key!r}]", window)

    return out


def _prepare_dynamic_gmm_lag_kwargs(raw_kwargs: dict[str, object]) -> dict[str, object]:
    """Translate the new public lag-window API into the existing internal API.

    Public API:
        gmm_lags=(2, 4)
        gmm_lags_by_role={"endogenous": (2, 5), "predetermined": (1, 3)}
        gmm_lags_by_variable={"investment": (3, 5), "cashflow": (1, 2)}

    Internal API:
        default_lag
        lag_limits
        dependent_lag_limits

    Precedence:
        gmm_lags_by_variable > gmm_lags_by_role > gmm_lags
    """

    kwargs = dict(raw_kwargs)

    # Accepted for public API compatibility. The current spec builder does not
    # need to store this flag directly here.
    kwargs.pop("windmeijer", None)

    global_lag_value = kwargs.pop("gmm_lags", kwargs.get("default_lag", (2, 2)))
    global_lag = _validate_gmm_lag_window("gmm_lags", global_lag_value)

    role_lags_raw = kwargs.pop("gmm_lags_by_role", None)
    variable_lags_raw = kwargs.pop("gmm_lags_by_variable", None)

    legacy_lag_limits = _normalise_gmm_lag_mapping(
        "lag_limits",
        kwargs.get("lag_limits"),
    )
    variable_lags = _normalise_gmm_lag_mapping(
        "gmm_lags_by_variable",
        variable_lags_raw,
    )

    # Explicit new variable-specific lags override legacy lag_limits.
    lag_limits: dict[str, tuple[int, int]] = {
        **legacy_lag_limits,
        **variable_lags,
    }

    role_lags: dict[str, tuple[int, int]] = {}
    if role_lags_raw is not None:
        if not isinstance(role_lags_raw, Mapping):
            raise TypeError("gmm_lags_by_role must be a mapping of roles to lag-window tuples.")

        for role, window in role_lags_raw.items():
            if not isinstance(role, str):
                raise TypeError("gmm_lags_by_role keys must be strings.")

            normalised_role = _normalise_gmm_lag_role(role)
            role_lags[normalised_role] = _validate_gmm_lag_window(
                f"gmm_lags_by_role[{role!r}]",
                window,
            )

    for variable in _as_list(kwargs.get("endogenous")):
        if variable not in lag_limits and "endogenous" in role_lags:
            lag_limits[variable] = role_lags["endogenous"]

    for variable in _as_list(kwargs.get("predetermined")):
        if variable not in lag_limits and "predetermined" in role_lags:
            lag_limits[variable] = role_lags["predetermined"]

    dependent = kwargs.get("dependent")
    lagged_dependent = kwargs.get("lagged_dependent", True)

    if isinstance(dependent, str) and lagged_dependent:
        if dependent in lag_limits:
            kwargs["dependent_lag_limits"] = lag_limits[dependent]
        elif "endogenous" in role_lags:
            kwargs["dependent_lag_limits"] = role_lags["endogenous"]
        elif "dependent_lag_limits" not in kwargs:
            kwargs["dependent_lag_limits"] = global_lag

    kwargs["default_lag"] = global_lag
    kwargs["lag_limits"] = lag_limits or None

    return kwargs
'''

if "_prepare_dynamic_gmm_lag_kwargs" not in text:
    marker = "\ndef build_system_gmm_spec(**kwargs: object) -> DynamicPanelSpec:"
    if marker not in text:
        raise RuntimeError("Could not find build_system_gmm_spec marker in presets.py.")
    text = text.replace(marker, helper + marker)

pattern = re.compile(
    r"def build_system_gmm_spec\(\*\*kwargs: object\) -> DynamicPanelSpec:\n"
    r'    """Build a generic Blundell-Bond-style System GMM specification\."""\n\n'
    r"    return build_dynamic_panel_gmm_spec\(\*\*kwargs, system=True\)  # type: ignore\[arg-type\]\n\n\n"
    r"def build_difference_gmm_spec\(\*\*kwargs: object\) -> DynamicPanelSpec:\n"
    r'    """Build a generic Arellano-Bond-style Difference GMM specification\."""\n\n'
    r"    return build_dynamic_panel_gmm_spec\(\*\*kwargs, system=False\)  # type: ignore\[arg-type\]",
    re.MULTILINE,
)

replacement = '''def build_system_gmm_spec(**kwargs: object) -> DynamicPanelSpec:
    """Build a generic Blundell-Bond-style System GMM specification."""

    prepared_kwargs = _prepare_dynamic_gmm_lag_kwargs(kwargs)
    return build_dynamic_panel_gmm_spec(**prepared_kwargs, system=True)  # type: ignore[arg-type]


def build_difference_gmm_spec(**kwargs: object) -> DynamicPanelSpec:
    """Build a generic Arellano-Bond-style Difference GMM specification."""

    prepared_kwargs = _prepare_dynamic_gmm_lag_kwargs(kwargs)
    return build_dynamic_panel_gmm_spec(**prepared_kwargs, system=False)  # type: ignore[arg-type]'''

new_text, count = pattern.subn(replacement, text)

if count != 1:
    raise RuntimeError(
        f"Expected to replace wrapper functions exactly once, replaced {count} times."
    )

path.write_text(new_text, encoding="utf-8")
print("Patched src/systemgmmkit/presets.py")
