from systemgmmkit import DynamicPanelSpec, GMMStyle, IVStyle, build_pydynpd_command
from systemgmmkit.presets import aid_growth_techshare_spec


def test_build_command_contains_core_blocks():
    spec = DynamicPanelSpec(
        dependent="growth_rate",
        regressors=["L1.growth_rate", "lPA", "x"],
        gmm=[GMMStyle("growth_rate", 2, 3), GMMStyle("lPA", 2, 2)],
        iv=[IVStyle("x")],
        time_dummies=True,
        system=True,
        collapse=True,
        transformation="fod",
        steps="twostep",
    )
    command = build_pydynpd_command(spec)
    assert command.startswith("growth_rate L1.growth_rate lPA x |")
    assert "gmm(growth_rate, 2:3)" in command
    assert "gmm(lPA, 2:2)" in command
    assert "iv(x)" in command
    assert "timedumm" in command
    assert "collapse" in command
    assert "twostep" not in command
    assert "nolevel" not in command


def test_difference_gmm_adds_nolevel():
    spec = aid_growth_techshare_spec(system=False)
    command = build_pydynpd_command(spec)
    assert "nolevel" in command
