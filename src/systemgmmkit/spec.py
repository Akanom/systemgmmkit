from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Transformation = Literal["fd", "fod"]
Steps = Literal["onestep", "twostep", "iterated"]


@dataclass(frozen=True)
class GMMStyle:
    """A GMM-style instrument block.

    Parameters
    ----------
    variable:
        Variable to instrument internally.
    min_lag, max_lag:
        Lag window used as internal instruments. Conservative defaults are preferred.
    eq:
        Equation where instruments are applied. Keep as None for backend defaults.
    """

    variable: str
    min_lag: int = 2
    max_lag: int = 2
    eq: Literal["diff", "level"] | None = None

    def __post_init__(self) -> None:
        if self.min_lag < 0 or self.max_lag < 0:
            raise ValueError("Lag depths must be non-negative integers.")
        if self.max_lag < self.min_lag:
            raise ValueError("max_lag must be greater than or equal to min_lag.")
        if not self.variable:
            raise ValueError("GMMStyle.variable cannot be empty.")


@dataclass(frozen=True)
class IVStyle:
    """An IV-style, external, or assumed-exogenous instrument block."""

    variable: str
    eq: Literal["diff", "level"] | None = None

    def __post_init__(self) -> None:
        if not self.variable:
            raise ValueError("IVStyle.variable cannot be empty.")


@dataclass(frozen=True)
class DynamicPanelSpec:
    """Structured specification for a dynamic-panel GMM model."""

    dependent: str
    regressors: list[str]
    gmm: list[GMMStyle] = field(default_factory=list)
    iv: list[IVStyle] = field(default_factory=list)
    time_dummies: bool = True
    system: bool = True
    collapse: bool = True
    transformation: Transformation = "fod"
    steps: Steps = "twostep"
    name: str = "dynamic_panel_gmm"

    def __post_init__(self) -> None:
        if not self.dependent:
            raise ValueError("dependent cannot be empty.")
        if not self.regressors:
            raise ValueError("regressors cannot be empty.")
        if self.transformation not in {"fd", "fod"}:
            raise ValueError("transformation must be 'fd' or 'fod'.")
        if self.steps not in {"onestep", "twostep", "iterated"}:
            raise ValueError("steps must be 'onestep', 'twostep', or 'iterated'.")

    @property
    def variables(self) -> set[str]:
        """Return variables appearing in the specification, excluding lag notation wrappers."""

        def clean(v: str) -> str:
            if v.startswith("L") and "." in v:
                return v.split(".", 1)[1]
            return v

        out = {self.dependent}
        out.update(clean(v) for v in self.regressors)
        out.update(g.variable for g in self.gmm)
        out.update(iv.variable for iv in self.iv)
        return out

    def with_name(self, name: str) -> DynamicPanelSpec:
        return DynamicPanelSpec(
            dependent=self.dependent,
            regressors=list(self.regressors),
            gmm=list(self.gmm),
            iv=list(self.iv),
            time_dummies=self.time_dummies,
            system=self.system,
            collapse=self.collapse,
            transformation=self.transformation,
            steps=self.steps,
            name=name,
        )
