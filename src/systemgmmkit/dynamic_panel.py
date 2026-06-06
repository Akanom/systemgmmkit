from __future__ import annotations

import inspect
import warnings
from typing import Any, Literal

import pandas as pd


DynamicGMMBackend = Literal["auto", "validated", "native", "pydynpd"]


class DynamicPanelBackendError(RuntimeError):
    """Raised when dynamic-panel backend routing fails."""


def _is_system_gmm(spec: Any) -> bool:
    return bool(getattr(spec, "system", False))


def _append_result_note(result: Any, note: str) -> Any:
    """Best-effort note attachment without assuming a mutable result class."""
    try:
        notes = getattr(result, "notes", None)

        if notes is None:
            setattr(result, "notes", [note])
        elif isinstance(notes, list):
            if note not in notes:
                notes.append(note)
        elif isinstance(notes, tuple):
            if note not in notes:
                setattr(result, "notes", [*notes, note])
        else:
            setattr(result, "notes", [str(notes), note])
    except Exception:
        pass

    return result


def _set_result_attr(result: Any, name: str, value: Any) -> Any:
    """Best-effort result metadata attachment."""
    try:
        setattr(result, name, value)
    except Exception:
        pass

    return result


def _call_pydynpd_backend(
    spec: Any,
    data: pd.DataFrame,
    *,
    entity: str,
    time: str,
) -> Any:
    """Call the systemgmmkit pydynpd adapter across known signatures."""

    try:
        from systemgmmkit.pydynpd_backend import run_pydynpd
    except Exception as exc:
        raise DynamicPanelBackendError(
            "The pydynpd backend could not be imported. Install optional backend "
            "dependencies or use backend='native'."
        ) from exc

    signature = inspect.signature(run_pydynpd)
    params = signature.parameters

    if "panel_ids" in params:
        return run_pydynpd(spec, data, panel_ids=(entity, time))

    attempts = [
        ("panel_ids_tuple_positional", lambda: run_pydynpd(spec, data, (entity, time))),
        ("panel_ids_list_positional", lambda: run_pydynpd(spec, data, [entity, time])),
        ("keywords_entity_time", lambda: run_pydynpd(spec, data, entity=entity, time=time)),
        (
            "keywords_entity_col_time_col",
            lambda: run_pydynpd(spec, data, entity_col=entity, time_col=time),
        ),
        (
            "keywords_id_col_time_col",
            lambda: run_pydynpd(spec, data, id_col=entity, time_col=time),
        ),
        ("positional_entity_time", lambda: run_pydynpd(spec, data, entity, time)),
        ("spec_data_only", lambda: run_pydynpd(spec, data)),
    ]

    errors: list[str] = []

    for label, func in attempts:
        try:
            return func()
        except TypeError as exc:
            errors.append(f"{label}: {exc}")

    raise DynamicPanelBackendError(
        "Could not call the pydynpd backend with any supported adapter signature. "
        "Attempted signatures:\n" + "\n".join(errors)
    )


def _call_native_backend(
    spec: Any,
    data: pd.DataFrame,
    *,
    entity: str,
    time: str,
) -> Any:
    try:
        from systemgmmkit.native_gmm import run_native_dynamic_panel_gmm
    except Exception as exc:
        raise DynamicPanelBackendError(
            "The native GMM backend could not be imported."
        ) from exc

    return run_native_dynamic_panel_gmm(
        spec,
        data,
        entity=entity,
        time=time,
    )


def run_dynamic_panel_gmm(
    spec: Any,
    data: pd.DataFrame,
    *,
    entity: str,
    time: str,
    backend: DynamicGMMBackend = "auto",
) -> Any:
    """Run Difference or System GMM through the systemgmmkit public API.

    Backend policy
    --------------
    backend="auto"
        Difference GMM -> native validated backend.
        System GMM     -> validated pydynpd adapter through systemgmmkit.

    backend="validated"
        Same as "auto", but explicit.

    backend="native"
        Uses the native systemgmmkit backend. Native System GMM remains
        experimental until coefficient-level parity is certified.

    backend="pydynpd"
        Explicitly routes through the pydynpd adapter.

    This keeps systemgmmkit as the user-facing package while allowing a validated
    third-party backend internally where appropriate.
    """

    if backend not in {"auto", "validated", "native", "pydynpd"}:
        raise ValueError(
            "backend must be one of: 'auto', 'validated', 'native', 'pydynpd'."
        )

    is_system = _is_system_gmm(spec)

    if backend in {"auto", "validated"}:
        if is_system:
            result = _call_pydynpd_backend(spec, data, entity=entity, time=time)
            _set_result_attr(result, "backend", "pydynpd-via-systemgmmkit")
            _set_result_attr(result, "systemgmmkit_backend_policy", backend)
            _append_result_note(
                result,
                "System GMM routed through the validated pydynpd adapter by systemgmmkit.",
            )
            return result

        result = _call_native_backend(spec, data, entity=entity, time=time)
        _set_result_attr(result, "backend", "native-validated-via-systemgmmkit")
        _set_result_attr(result, "systemgmmkit_backend_policy", backend)
        _append_result_note(
            result,
            "Difference GMM routed through the validated native systemgmmkit backend.",
        )
        return result

    if backend == "pydynpd":
        result = _call_pydynpd_backend(spec, data, entity=entity, time=time)
        _set_result_attr(result, "backend", "pydynpd-via-systemgmmkit")
        _set_result_attr(result, "systemgmmkit_backend_policy", backend)
        return result

    result = _call_native_backend(spec, data, entity=entity, time=time)
    _set_result_attr(result, "backend", "native-via-systemgmmkit")
    _set_result_attr(result, "systemgmmkit_backend_policy", backend)

    if is_system:
        warnings.warn(
            "Native System GMM is experimental and not yet xtabond2-certified. "
            "Use backend='auto' or backend='validated' for empirical System GMM.",
            RuntimeWarning,
            stacklevel=2,
        )
        _append_result_note(
            result,
            "Native System GMM is experimental and not yet xtabond2-certified.",
        )

    return result


def run_system_gmm(
    spec: Any,
    data: pd.DataFrame,
    *,
    entity: str,
    time: str,
    backend: DynamicGMMBackend = "auto",
) -> Any:
    """Run a System GMM specification through systemgmmkit."""

    if not _is_system_gmm(spec):
        raise ValueError(
            "run_system_gmm() expects a System GMM spec with spec.system=True."
        )

    return run_dynamic_panel_gmm(
        spec,
        data,
        entity=entity,
        time=time,
        backend=backend,
    )


def run_difference_gmm(
    spec: Any,
    data: pd.DataFrame,
    *,
    entity: str,
    time: str,
    backend: DynamicGMMBackend = "auto",
) -> Any:
    """Run a Difference GMM specification through systemgmmkit."""

    if _is_system_gmm(spec):
        raise ValueError(
            "run_difference_gmm() expects a Difference GMM spec with spec.system=False."
        )

    return run_dynamic_panel_gmm(
        spec,
        data,
        entity=entity,
        time=time,
        backend=backend,
    )
