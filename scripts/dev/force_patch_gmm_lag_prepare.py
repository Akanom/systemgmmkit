from __future__ import annotations

import re
from pathlib import Path

path = Path("src/systemgmmkit/presets.py")
text = path.read_text(encoding="utf-8")

pattern = re.compile(
    r"def _prepare_dynamic_gmm_lag_kwargs\(raw_kwargs: dict\[str, object\]\) -> dict\[str, object\]:"
    r".*?"
    r"\n(?=def build_system_gmm_spec)",
    re.DOTALL,
)

replacement = r'''def _prepare_dynamic_gmm_lag_kwargs(raw_kwargs: dict[str, object]) -> dict[str, object]:
    """Translate the public lag-window API into the existing internal API.

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

    Backward compatibility:
        If no explicit gmm_lags/default_lag is supplied, the lagged dependent
        variable keeps the historical default dependent_lag_limits=(2, 3),
        while other GMM variables keep default_lag=(2, 2).
    """

    kwargs = dict(raw_kwargs)

    # Accepted for public API compatibility. This builder produces the model
    # specification; covariance details are handled downstream.
    kwargs.pop("windmeijer", None)

    has_explicit_global_lag = "gmm_lags" in kwargs or "default_lag" in kwargs

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
        elif has_explicit_global_lag:
            kwargs["dependent_lag_limits"] = global_lag
        else:
            # Historical default expected by existing parity tests.
            kwargs.setdefault("dependent_lag_limits", (2, 3))

    kwargs["default_lag"] = global_lag
    kwargs["lag_limits"] = lag_limits or None

    return kwargs


'''

new_text, count = pattern.subn(replacement, text)

if count != 1:
    raise RuntimeError(
        f"Expected to replace _prepare_dynamic_gmm_lag_kwargs once, replaced {count} times."
    )

path.write_text(new_text, encoding="utf-8")
print("Replaced _prepare_dynamic_gmm_lag_kwargs with backward-compatible version.")
