from __future__ import annotations

from systemgmmkit import build_difference_gmm_spec, build_system_gmm_spec
from systemgmmkit.native_gmm import _native_pydynpd_compat_instrument_order
from systemgmmkit.pydynpd_backend import build_pydynpd_command


def _lag_window_spec(*, system: bool):
    builder = build_system_gmm_spec if system else build_difference_gmm_spec

    return builder(
        dependent="y",
        regressors=["x_endog", "x_pred", "x_exog"],
        endogenous=["x_endog"],
        predetermined=["x_pred"],
        exogenous=["x_exog"],
        gmm_lags=(2, 2),
        gmm_lags_by_role={
            "endogenous": (2, 4),
            "predetermined": (1, 3),
        },
        gmm_lags_by_variable={
            "y": (2, 3),
            "x_endog": (4, 5),
        },
        time_dummies=False,
        collapse=True,
    )


def _gmm_blocks(spec):
    return [
        (block.variable, block.min_lag, block.max_lag)
        for block in spec.gmm
    ]


def test_role_and_variable_lags_generate_expected_separate_gmm_blocks_system():
    spec = _lag_window_spec(system=True)

    assert spec.system is True
    assert _gmm_blocks(spec) == [
        ("y", 2, 3),
        ("x_endog", 4, 5),
        ("x_pred", 1, 3),
    ]

    command = build_pydynpd_command(spec)

    assert command == (
        "y L1.y x_endog x_pred x_exog | "
        "gmm(y, 2:3) gmm(x_endog, 4:5) gmm(x_pred, 1:3) iv(x_exog) | "
        "collapse"
    )
    assert command.count("gmm(") == 3
    assert command.count("iv(") == 1
    assert "gmm(x_exog" not in command
    assert "nolevel" not in command


def test_role_and_variable_lags_generate_expected_separate_gmm_blocks_difference():
    spec = _lag_window_spec(system=False)

    assert spec.system is False
    assert _gmm_blocks(spec) == [
        ("y", 2, 3),
        ("x_endog", 4, 5),
        ("x_pred", 1, 3),
    ]

    command = build_pydynpd_command(spec)

    assert command == (
        "y L1.y x_endog x_pred x_exog | "
        "gmm(y, 2:3) gmm(x_endog, 4:5) gmm(x_pred, 1:3) iv(x_exog) | "
        "nolevel collapse"
    )
    assert command.count("gmm(") == 3
    assert command.count("iv(") == 1
    assert "gmm(x_exog" not in command
    assert "nolevel" in command


def test_difference_gmm_expected_compact_instrument_names_and_count(monkeypatch):
    monkeypatch.setenv("SYSTEMGMMKIT_SYSTEM_IV_LAYOUT", "single_both")

    spec = _lag_window_spec(system=False)
    labels = _native_pydynpd_compat_instrument_order(spec)

    assert labels == [
        "D:y:L2",
        "D:y:L3",
        "D:x_endog:L4",
        "D:x_endog:L5",
        "D:x_pred:L1",
        "D:x_pred:L2",
        "D:x_pred:L3",
        "IV:x_exog",
    ]

    assert len(labels) == 8
    assert sum(label.startswith("D:") for label in labels) == 7
    assert sum(label.startswith("IV:") for label in labels) == 1
    assert not any("x_exog:L" in label for label in labels)


def test_system_gmm_expected_compact_instrument_names_and_count(monkeypatch):
    monkeypatch.setenv("SYSTEMGMMKIT_SYSTEM_IV_LAYOUT", "single_both")

    spec = _lag_window_spec(system=True)
    labels = _native_pydynpd_compat_instrument_order(spec)

    assert labels == [
        "D:y:L2",
        "D:y:L3",
        "D:x_endog:L4",
        "D:x_endog:L5",
        "D:x_pred:L1",
        "D:x_pred:L2",
        "D:x_pred:L3",
        "IV:x_exog",
        "L:diff:y:L1",
        "L:diff:x_endog:L3",
        "L:diff:x_pred:L0",
        "L:constant",
    ]

    assert len(labels) == 12
    assert sum(label.startswith("D:") for label in labels) == 7
    assert sum(label.startswith("IV:") for label in labels) == 1
    assert sum(label.startswith("L:diff:") for label in labels) == 3
    assert labels[-1] == "L:constant"
    assert not any(label == "L:iv:x_exog" for label in labels)


def test_variable_specific_lags_change_instrument_count_predictably(monkeypatch):
    monkeypatch.setenv("SYSTEMGMMKIT_SYSTEM_IV_LAYOUT", "single_both")

    base = build_difference_gmm_spec(
        dependent="y",
        regressors=["x_endog", "x_pred", "x_exog"],
        endogenous=["x_endog"],
        predetermined=["x_pred"],
        exogenous=["x_exog"],
        gmm_lags=(2, 2),
        time_dummies=False,
        collapse=True,
    )

    expanded = _lag_window_spec(system=False)

    base_labels = _native_pydynpd_compat_instrument_order(base)
    expanded_labels = _native_pydynpd_compat_instrument_order(expanded)

    assert len(base_labels) == 4
    assert base_labels == [
        "D:y:L2",
        "D:x_endog:L2",
        "D:x_pred:L2",
        "IV:x_exog",
    ]

    assert len(expanded_labels) == 8
    assert expanded_labels == [
        "D:y:L2",
        "D:y:L3",
        "D:x_endog:L4",
        "D:x_endog:L5",
        "D:x_pred:L1",
        "D:x_pred:L2",
        "D:x_pred:L3",
        "IV:x_exog",
    ]
