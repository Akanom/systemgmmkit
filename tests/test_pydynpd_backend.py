from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

import systemgmmkit.pydynpd_backend as backend
from systemgmmkit import (
    DynamicPanelSpec,
    GMMStyle,
    IVStyle,
    PydynpdGMMResult,
    build_pydynpd_command,
)


@dataclass
class FakeRegressionModule:
    raw: object
    command_seen: str | None = None

    def abond(self, command, data, panel_ids):
        self.command_seen = command
        print("Number of obs = 42")
        print("Number of groups = 7")
        print("Number of instruments = 5")
        print("Hansen test p = 0.321")
        print("AR(1) test p = 0.041")
        print("AR(2) test p = 0.552")
        return self.raw


def test_build_pydynpd_command_groups_iv_variables():
    spec = DynamicPanelSpec(
        dependent="y",
        regressors=["L1.y", "x1", "x2", "c1", "c2"],
        gmm=[GMMStyle("y", 2, 3), GMMStyle("x1", 2, 2)],
        iv=[IVStyle("x2"), IVStyle("c1"), IVStyle("c2")],
        time_dummies=True,
        system=True,
        collapse=True,
    )

    command = build_pydynpd_command(spec)

    assert "gmm(y, 2:3)" in command
    assert "gmm(x1, 2:2)" in command
    assert "iv(x2 c1 c2)" in command
    assert command.count("iv(") == 1


def test_apply_numpy_compatibility_shim(monkeypatch):
    original = getattr(np, "in1d", None)
    monkeypatch.delattr(np, "in1d", raising=False)

    backend._apply_numpy_compatibility_shims()

    assert hasattr(np, "in1d")
    assert np.in1d is np.isin
    if original is not None:
        monkeypatch.setattr(np, "in1d", original, raising=False)


def test_run_pydynpd_returns_structured_result(monkeypatch):
    raw = SimpleNamespace(
        params={"L1.y": 0.4, "x1": 1.2},
        std_errors={"L1.y": 0.1, "x1": 0.2},
        pvalues={"L1.y": 0.01, "x1": 0.03},
    )
    fake = FakeRegressionModule(raw=raw)
    monkeypatch.setattr(backend.importlib, "import_module", lambda name: fake)

    spec = DynamicPanelSpec(
        dependent="y",
        regressors=["L1.y", "x1", "x2"],
        gmm=[GMMStyle("y", 2, 3), GMMStyle("x1", 2, 2)],
        iv=[IVStyle("x2")],
    )
    df = pd.DataFrame({"id": [1, 1, 2, 2], "t": [1, 2, 1, 2], "y": [1, 2, 3, 4]})

    result = backend.run_pydynpd(spec, df, panel_ids=["id", "t"])

    assert isinstance(result, PydynpdGMMResult)
    assert result.succeeded is True
    assert result.params["x1"] == 1.2
    assert result.std_errors["x1"] == 0.2
    assert result.pvalues["x1"] == 0.03
    assert result.nobs == 42
    assert result.n_groups == 7
    assert result.n_instruments == 5
    assert result.hansen_p == pytest.approx(0.321)
    assert result.ar1_p == pytest.approx(0.041)
    assert result.ar2_p == pytest.approx(0.552)
    assert result.command == fake.command_seen


def test_run_pydynpd_can_return_structured_error(monkeypatch):
    class FailingRegressionModule:
        def abond(self, command, data, panel_ids):
            print("partial output")
            raise ValueError("backend failed")

    monkeypatch.setattr(backend.importlib, "import_module", lambda name: FailingRegressionModule())

    spec = DynamicPanelSpec(
        dependent="y",
        regressors=["L1.y"],
        gmm=[GMMStyle("y", 2, 3)],
    )
    df = pd.DataFrame({"id": [1, 1], "t": [1, 2], "y": [1, 2]})

    result = backend.run_pydynpd(spec, df, panel_ids=["id", "t"], return_errors=True)

    assert isinstance(result, PydynpdGMMResult)
    assert result.succeeded is False
    assert "ValueError: backend failed" in result.error
    assert "partial output" in result.raw_output
