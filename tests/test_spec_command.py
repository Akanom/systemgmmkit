from systemgmmkit import (
    DynamicPanelSpec,
    GMMStyle,
    IVStyle,
    build_difference_gmm_spec,
    build_pydynpd_command,
)


def test_build_command_contains_core_blocks():
    spec = DynamicPanelSpec(
        dependent="y",
        regressors=["L1.y", "x1", "x2"],
        gmm=[GMMStyle("y", 2, 3), GMMStyle("x1", 2, 2)],
        iv=[IVStyle("x2")],
        time_dummies=True,
        system=True,
        collapse=True,
        transformation="fod",
        steps="twostep",
    )

    command = build_pydynpd_command(spec)

    assert command.startswith("y L1.y x1 x2 |")
    assert "gmm(y, 2:3)" in command
    assert "gmm(x1, 2:2)" in command
    assert "iv(x2)" in command
    assert "timedumm" in command
    assert "collapse" in command
    assert "twostep" not in command
    assert "nolevel" not in command


def test_difference_gmm_adds_nolevel():
    spec = build_difference_gmm_spec(
        dependent="y",
        regressors=["x1", "x2"],
        endogenous=["x1"],
        predetermined=["x2"],
        exogenous=[],
        name="generic_difference_gmm",
    )

    command = build_pydynpd_command(spec)

    assert command.startswith("y L1.y x1 x2 |")
    assert "nolevel" in command
