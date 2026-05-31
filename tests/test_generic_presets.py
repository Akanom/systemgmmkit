from systemgmmkit import (
    build_difference_gmm_spec,
    build_fixed_effects_spec,
    build_panel_model_suite,
    build_pydynpd_command,
    build_system_gmm_spec,
)


def test_generic_system_gmm_command_is_not_aid_specific() -> None:
    spec = build_system_gmm_spec(
        dependent="y",
        regressors=["x1", "x2"],
        controls=["c1"],
        interactions=["x1_x2"],
        endogenous=["x1"],
        predetermined=["x2"],
        exogenous=["c1", "x1_x2"],
        lag_limits={"y": (2, 3), "x1": (2, 2), "x2": (2, 2)},
        name="generic_system_gmm",
    )

    command = build_pydynpd_command(spec)

    assert command.startswith("y L1.y x1 x2 c1 x1_x2 |")
    assert "gmm(y, 2:3)" in command
    assert "gmm(x1, 2:2)" in command
    assert "gmm(x2, 2:2)" in command
    assert "iv(c1)" in command
    assert "iv(x1_x2)" in command
    assert "collapse" in command
    assert "nolevel" not in command


def test_generic_difference_gmm_emits_nolevel() -> None:
    spec = build_difference_gmm_spec(
        dependent="profit",
        regressors=["capital"],
        endogenous=["capital"],
        name="difference_gmm_test",
    )
    command = build_pydynpd_command(spec)
    assert command.startswith("profit L1.profit capital |")
    assert "nolevel" in command


def test_generic_fixed_effects_builder() -> None:
    spec = build_fixed_effects_spec(
        dependent="y",
        regressors=["x1"],
        controls=["c1"],
        interactions=["x1_c1"],
        entity_effects=True,
        time_effects=False,
        name="generic_fe",
    )
    assert spec.name == "generic_fe"
    assert spec.dependent == "y"
    assert spec.regressors == ["x1", "c1", "x1_c1"]
    assert spec.entity_effects is True
    assert spec.time_effects is False


def test_generic_suite_builder() -> None:
    suite = build_panel_model_suite(
        name="investment_model",
        dependent="investment",
        regressors=["q", "cashflow"],
        controls=["size"],
        endogenous=["q"],
        predetermined=["cashflow"],
        exogenous=["size"],
        system=True,
    )
    assert suite.name == "investment_model"
    assert suite.fixed_effects.dependent == "investment"
    assert suite.dynamic_gmm.system is True
