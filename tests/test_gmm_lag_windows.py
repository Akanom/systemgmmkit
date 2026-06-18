from __future__ import annotations

import pytest

from systemgmmkit import build_difference_gmm_spec, build_system_gmm_spec


def _gmm_lag_map(spec):
    out = {}
    for block in spec.gmm:
        variable = getattr(block, "variable", None)
        min_lag = getattr(block, "min_lag", None)
        max_lag = getattr(block, "max_lag", None)

        if variable is None:
            variable = getattr(block, "var", None)
        if min_lag is None:
            min_lag = getattr(block, "lag_start", None)
        if max_lag is None:
            max_lag = getattr(block, "lag_end", None)

        out[variable] = (min_lag, max_lag)
    return out


def test_global_gmm_lags_remain_supported_system_gmm():
    spec = build_system_gmm_spec(
        dependent="y",
        regressors=["L1_y", "investment", "cashflow", "firm_size"],
        endogenous=["investment"],
        predetermined=["cashflow"],
        exogenous=["firm_size"],
        gmm_lags=(2, 4),
        collapse=True,
        windmeijer=True,
    )

    lag_map = _gmm_lag_map(spec)

    assert lag_map["y"] == (2, 4)
    assert lag_map["investment"] == (2, 4)
    assert lag_map["cashflow"] == (2, 4)


def test_role_specific_gmm_lags_system_gmm():
    spec = build_system_gmm_spec(
        dependent="y",
        regressors=["L1_y", "investment", "cashflow", "firm_size"],
        endogenous=["investment"],
        predetermined=["cashflow"],
        exogenous=["firm_size"],
        gmm_lags=(2, 4),
        gmm_lags_by_role={
            "endogenous": (2, 5),
            "predetermined": (1, 3),
        },
        collapse=True,
        windmeijer=True,
    )

    lag_map = _gmm_lag_map(spec)

    assert lag_map["y"] == (2, 5)
    assert lag_map["investment"] == (2, 5)
    assert lag_map["cashflow"] == (1, 3)


def test_variable_specific_gmm_lags_override_role_lags_system_gmm():
    spec = build_system_gmm_spec(
        dependent="y",
        regressors=[
            "L1_y",
            "investment",
            "L1_investment",
            "cashflow",
            "L1_cashflow",
            "firm_size",
        ],
        endogenous=["investment", "L1_investment"],
        predetermined=["cashflow", "L1_cashflow"],
        exogenous=["firm_size"],
        gmm_lags=(2, 4),
        gmm_lags_by_role={
            "endogenous": (2, 5),
            "predetermined": (1, 3),
        },
        gmm_lags_by_variable={
            "y": (2, 4),
            "investment": (3, 5),
            "L1_investment": (3, 6),
            "cashflow": (1, 2),
            "L1_cashflow": (2, 3),
        },
        collapse=True,
        windmeijer=True,
    )

    lag_map = _gmm_lag_map(spec)

    assert lag_map["y"] == (2, 4)
    assert lag_map["investment"] == (3, 5)
    assert lag_map["L1_investment"] == (3, 6)
    assert lag_map["cashflow"] == (1, 2)
    assert lag_map["L1_cashflow"] == (2, 3)


def test_role_specific_gmm_lags_difference_gmm():
    spec = build_difference_gmm_spec(
        dependent="y",
        regressors=["L1_y", "investment", "cashflow", "firm_size"],
        endogenous=["investment"],
        predetermined=["cashflow"],
        exogenous=["firm_size"],
        gmm_lags=(2, 4),
        gmm_lags_by_role={
            "endogenous": (2, 5),
            "predetermined": (1, 3),
        },
        collapse=True,
    )

    lag_map = _gmm_lag_map(spec)

    assert spec.system is False
    assert lag_map["y"] == (2, 5)
    assert lag_map["investment"] == (2, 5)
    assert lag_map["cashflow"] == (1, 3)


def test_legacy_lag_limits_still_work_as_variable_lag_alias():
    spec = build_system_gmm_spec(
        dependent="y",
        regressors=["L1_y", "investment", "cashflow", "firm_size"],
        endogenous=["investment"],
        predetermined=["cashflow"],
        exogenous=["firm_size"],
        gmm_lags=(2, 4),
        lag_limits={
            "investment": (3, 5),
            "cashflow": (1, 2),
        },
        collapse=True,
        windmeijer=True,
    )

    lag_map = _gmm_lag_map(spec)

    assert lag_map["investment"] == (3, 5)
    assert lag_map["cashflow"] == (1, 2)


def test_explicit_variable_lags_override_legacy_lag_limits():
    spec = build_system_gmm_spec(
        dependent="y",
        regressors=["L1_y", "investment", "cashflow", "firm_size"],
        endogenous=["investment"],
        predetermined=["cashflow"],
        exogenous=["firm_size"],
        gmm_lags=(2, 4),
        lag_limits={
            "investment": (2, 3),
        },
        gmm_lags_by_variable={
            "investment": (4, 6),
        },
        collapse=True,
        windmeijer=True,
    )

    lag_map = _gmm_lag_map(spec)

    assert lag_map["investment"] == (4, 6)


def test_exogenous_role_is_rejected_for_gmm_lag_windows():
    with pytest.raises(ValueError, match="Exogenous variables are IV-style"):
        build_system_gmm_spec(
            dependent="y",
            regressors=["L1_y", "investment", "firm_size"],
            endogenous=["investment"],
            exogenous=["firm_size"],
            gmm_lags_by_role={
                "exogenous": (0, 1),
            },
        )


@pytest.mark.parametrize(
    "bad_window",
    [
        (5, 2),
        (-1, 2),
        (2, -1),
    ],
)
def test_invalid_lag_windows_are_rejected(bad_window):
    with pytest.raises(ValueError):
        build_system_gmm_spec(
            dependent="y",
            regressors=["L1_y", "investment"],
            endogenous=["investment"],
            gmm_lags=bad_window,
        )
