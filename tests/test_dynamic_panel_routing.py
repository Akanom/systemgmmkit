from __future__ import annotations

import builtins
import warnings
from types import SimpleNamespace

import pandas as pd
import pytest

import systemgmmkit.dynamic_panel as dynamic_panel
import systemgmmkit.native_gmm as native_gmm
import systemgmmkit.pydynpd_backend as pydynpd_backend


def _data() -> pd.DataFrame:
    return pd.DataFrame({"id": [1, 1], "time": [1, 2], "y": [1.0, 1.1]})


@pytest.mark.parametrize(
    ("steps", "expected"),
    [
        ("twostep", True),
        ("two-step", True),
        ("two_step", True),
        ("two step", True),
        ("2", True),
        ("iterated", True),
        ("onestep", False),
    ],
)
def test_twostep_detection_normalizes_supported_spellings(steps: str, expected: bool) -> None:
    assert dynamic_panel._is_twostep_like(SimpleNamespace(steps=steps)) is expected


def test_result_metadata_helpers_cover_supported_and_read_only_shapes() -> None:
    no_notes = SimpleNamespace()
    dynamic_panel._append_result_note(no_notes, "first")
    assert no_notes.notes == ["first"]

    list_notes = SimpleNamespace(notes=["first"])
    dynamic_panel._append_result_note(list_notes, "first")
    dynamic_panel._append_result_note(list_notes, "second")
    assert list_notes.notes == ["first", "second"]

    tuple_notes = SimpleNamespace(notes=("first",))
    dynamic_panel._append_result_note(tuple_notes, "first")
    assert tuple_notes.notes == ("first",)
    dynamic_panel._append_result_note(tuple_notes, "second")
    assert tuple_notes.notes == ["first", "second"]

    scalar_notes = SimpleNamespace(notes="first")
    dynamic_panel._append_result_note(scalar_notes, "second")
    assert scalar_notes.notes == ["first", "second"]

    immutable = object()
    assert dynamic_panel._append_result_note(immutable, "ignored") is immutable
    assert dynamic_panel._set_result_attr(immutable, "backend", "ignored") is immutable

    mutable = SimpleNamespace()
    assert dynamic_panel._set_result_attr(mutable, "backend", "native") is mutable
    assert mutable.backend == "native"


def test_pydynpd_adapter_prefers_named_panel_ids(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}
    expected = object()

    def fake_run(spec, data, *, panel_ids):
        captured.update(spec=spec, data=data, panel_ids=panel_ids)
        return expected

    monkeypatch.setattr(pydynpd_backend, "run_pydynpd", fake_run)
    spec = SimpleNamespace(system=True)
    data = _data()

    result = dynamic_panel._call_pydynpd_backend(
        spec,
        data,
        entity="id",
        time="time",
    )

    assert result is expected
    assert captured == {"spec": spec, "data": data, "panel_ids": ("id", "time")}


def test_pydynpd_adapter_falls_back_through_legacy_signatures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[tuple[object, ...], dict[str, object]]] = []
    expected = object()

    def fake_run(*args, **kwargs):
        calls.append((args, kwargs))
        if len(args) == 2 and not kwargs:
            return expected
        raise TypeError("unsupported legacy signature")

    monkeypatch.setattr(pydynpd_backend, "run_pydynpd", fake_run)

    result = dynamic_panel._call_pydynpd_backend(
        SimpleNamespace(system=True),
        _data(),
        entity="id",
        time="time",
    )

    assert result is expected
    assert len(calls) == 7


def test_pydynpd_adapter_reports_every_attempted_signature(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def always_fails(*args, **kwargs):
        raise TypeError("unsupported")

    monkeypatch.setattr(pydynpd_backend, "run_pydynpd", always_fails)

    with pytest.raises(dynamic_panel.DynamicPanelBackendError) as exc_info:
        dynamic_panel._call_pydynpd_backend(
            SimpleNamespace(system=True),
            _data(),
            entity="id",
            time="time",
        )

    message = str(exc_info.value)
    assert "panel_ids_tuple_positional" in message
    assert "keywords_entity_col_time_col" in message
    assert "spec_data_only" in message


@pytest.mark.parametrize(
    ("module_name", "call"),
    [
        (
            "systemgmmkit.pydynpd_backend",
            lambda: dynamic_panel._call_pydynpd_backend(
                SimpleNamespace(system=True),
                _data(),
                entity="id",
                time="time",
            ),
        ),
        (
            "systemgmmkit.native_gmm",
            lambda: dynamic_panel._call_native_backend(
                SimpleNamespace(system=False),
                _data(),
                entity="id",
                time="time",
            ),
        ),
    ],
)
def test_backend_import_failures_are_actionable(
    monkeypatch: pytest.MonkeyPatch,
    module_name: str,
    call,
) -> None:
    real_import = builtins.__import__

    def failing_import(name, *args, **kwargs):
        if name == module_name:
            raise ImportError("backend unavailable")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", failing_import)

    with pytest.raises(dynamic_panel.DynamicPanelBackendError, match="could not be imported"):
        call()


@pytest.mark.parametrize(
    ("system", "steps", "explicit", "environment", "expected"),
    [
        (True, "twostep", True, None, True),
        (True, "twostep", False, "true", False),
        (False, "onestep", None, "YES", True),
        (True, "twostep", None, "off", False),
        (True, "twostep", None, None, True),
        (False, "twostep", None, None, False),
    ],
)
def test_native_windmeijer_resolution_precedence(
    monkeypatch: pytest.MonkeyPatch,
    system: bool,
    steps: str,
    explicit: bool | None,
    environment: str | None,
    expected: bool,
) -> None:
    if environment is None:
        monkeypatch.delenv("SYSTEMGMMKIT_NATIVE_WINDMEIJER", raising=False)
    else:
        monkeypatch.setenv("SYSTEMGMMKIT_NATIVE_WINDMEIJER", environment)

    spec = SimpleNamespace(system=system, steps=steps)
    assert dynamic_panel._resolve_native_windmeijer(spec, explicit) is expected


def test_native_adapter_forwards_resolved_windmeijer(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}
    expected = object()

    def fake_run(spec, data, *, entity, time, windmeijer):
        captured.update(
            spec=spec,
            data=data,
            entity=entity,
            time=time,
            windmeijer=windmeijer,
        )
        return expected

    monkeypatch.setattr(native_gmm, "run_native_dynamic_panel_gmm", fake_run)
    spec = SimpleNamespace(system=True, steps="twostep")
    data = _data()

    result = dynamic_panel._call_native_backend(
        spec,
        data,
        entity="id",
        time="time",
    )

    assert result is expected
    assert captured == {
        "spec": spec,
        "data": data,
        "entity": "id",
        "time": "time",
        "windmeijer": True,
    }


@pytest.mark.parametrize("backend", ["auto", "validated"])
def test_auto_and_validated_system_gmm_use_external_adapter(
    monkeypatch: pytest.MonkeyPatch,
    backend: str,
) -> None:
    result = SimpleNamespace()
    parsed: list[object] = []
    monkeypatch.setattr(dynamic_panel, "_call_pydynpd_backend", lambda *args, **kwargs: result)
    monkeypatch.setattr(
        dynamic_panel,
        "enrich_result_with_parsed_standard_errors",
        lambda value: parsed.append(value) or value,
    )

    returned = dynamic_panel.run_dynamic_panel_gmm(
        SimpleNamespace(system=True),
        _data(),
        entity="id",
        time="time",
        backend=backend,
    )

    assert returned is result
    assert parsed == [result]
    assert result.backend == "pydynpd-via-systemgmmkit"
    assert result.systemgmmkit_backend_policy == backend
    assert result.notes == [
        "System GMM routed through the validated pydynpd adapter by systemgmmkit."
    ]


@pytest.mark.parametrize("backend", ["auto", "validated"])
def test_auto_and_validated_difference_gmm_use_native_backend(
    monkeypatch: pytest.MonkeyPatch,
    backend: str,
) -> None:
    result = SimpleNamespace()
    captured: dict[str, object] = {}

    def fake_native(spec, data, **kwargs):
        captured.update(kwargs)
        return result

    monkeypatch.setattr(dynamic_panel, "_call_native_backend", fake_native)

    returned = dynamic_panel.run_dynamic_panel_gmm(
        SimpleNamespace(system=False),
        _data(),
        entity="id",
        time="time",
        backend=backend,
        windmeijer=True,
    )

    assert returned is result
    assert captured == {"entity": "id", "time": "time", "windmeijer": True}
    assert result.backend == "native-validated-via-systemgmmkit"
    assert result.systemgmmkit_backend_policy == backend
    assert result.notes == [
        "Difference GMM routed through the validated native systemgmmkit backend."
    ]


def test_explicit_pydynpd_route_sets_policy_metadata(monkeypatch: pytest.MonkeyPatch) -> None:
    result = SimpleNamespace()
    monkeypatch.setattr(dynamic_panel, "_call_pydynpd_backend", lambda *args, **kwargs: result)
    monkeypatch.setattr(
        dynamic_panel,
        "enrich_result_with_parsed_standard_errors",
        lambda value: value,
    )

    returned = dynamic_panel.run_dynamic_panel_gmm(
        SimpleNamespace(system=False),
        _data(),
        entity="id",
        time="time",
        backend="pydynpd",
    )

    assert returned is result
    assert result.backend == "pydynpd-via-systemgmmkit"
    assert result.systemgmmkit_backend_policy == "pydynpd"


@pytest.mark.parametrize("system", [False, True])
def test_explicit_native_route_warns_only_for_system_gmm(
    monkeypatch: pytest.MonkeyPatch,
    system: bool,
) -> None:
    result = SimpleNamespace()
    monkeypatch.setattr(dynamic_panel, "_call_native_backend", lambda *args, **kwargs: result)

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        returned = dynamic_panel.run_dynamic_panel_gmm(
            SimpleNamespace(system=system),
            _data(),
            entity="id",
            time="time",
            backend="native",
        )

    assert returned is result
    assert result.backend == "native-via-systemgmmkit"
    assert result.systemgmmkit_backend_policy == "native"
    assert len(caught) == int(system)
    if system:
        assert "six maintained xtabond2 specifications" in str(caught[0].message)
        assert "signed AR diagnostic parity" in result.notes[0]
    else:
        assert not hasattr(result, "notes")


def test_dynamic_panel_rejects_unknown_backend_before_estimation() -> None:
    with pytest.raises(ValueError, match="backend must be one of"):
        dynamic_panel.run_dynamic_panel_gmm(
            SimpleNamespace(system=False),
            _data(),
            entity="id",
            time="time",
            backend="unknown",  # type: ignore[arg-type]
        )


def test_system_and_difference_wrappers_validate_and_forward(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[object, dict[str, object]]] = []
    expected = object()

    def fake_run(spec, data, **kwargs):
        calls.append((spec, kwargs))
        return expected

    monkeypatch.setattr(dynamic_panel, "run_dynamic_panel_gmm", fake_run)
    data = _data()
    system_spec = SimpleNamespace(system=True)
    difference_spec = SimpleNamespace(system=False)

    assert (
        dynamic_panel.run_system_gmm(
            system_spec,
            data,
            entity="id",
            time="time",
            backend="native",
            windmeijer=False,
        )
        is expected
    )
    assert (
        dynamic_panel.run_difference_gmm(
            difference_spec,
            data,
            entity="id",
            time="time",
            backend="validated",
            windmeijer=True,
        )
        is expected
    )

    assert calls == [
        (
            system_spec,
            {
                "entity": "id",
                "time": "time",
                "backend": "native",
                "windmeijer": False,
            },
        ),
        (
            difference_spec,
            {
                "entity": "id",
                "time": "time",
                "backend": "validated",
                "windmeijer": True,
            },
        ),
    ]

    with pytest.raises(ValueError, match="expects a System GMM spec"):
        dynamic_panel.run_system_gmm(
            difference_spec,
            data,
            entity="id",
            time="time",
        )

    with pytest.raises(ValueError, match="expects a Difference GMM spec"):
        dynamic_panel.run_difference_gmm(
            system_spec,
            data,
            entity="id",
            time="time",
        )
