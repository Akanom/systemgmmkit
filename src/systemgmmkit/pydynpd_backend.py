from __future__ import annotations

import importlib
from collections.abc import Sequence
from typing import Any

import pandas as pd

from .spec import DynamicPanelSpec, GMMStyle, IVStyle


def _format_regressor(var: str) -> str:
    """Convert package lag notation to pydynpd notation.

    Accepted examples
    -----------------
    - ``L1.y`` -> ``L1.y``
    - ``L(1:2).y`` -> unchanged
    - ``x`` -> unchanged
    """
    if var.startswith("L") and "." in var:
        return var
    return var


def _format_gmm(block: GMMStyle, collapse: bool) -> str:
    """Format a pydynpd GMM block.

    pydynpd applies ``collapse`` globally in command part 3, not inside each
    gmm() block. The ``collapse`` parameter is accepted for API stability but
    intentionally unused here.
    """
    _ = collapse
    if block.eq is not None:
        raise NotImplementedError(
            "pydynpd command generation does not currently support eq() scoping."
        )
    lag = f"{block.min_lag}:{block.max_lag}"
    return f"gmm({block.variable}, {lag})"


def _format_iv(block: IVStyle) -> str:
    if block.eq is not None:
        raise NotImplementedError(
            "pydynpd command generation does not currently support eq() scoping."
        )
    return f"iv({block.variable})"


def build_pydynpd_command(spec: DynamicPanelSpec) -> str:
    """Build a pydynpd command string from a structured specification.

    pydynpd's command has the structure::

        y regressors | gmm(...) iv(...) | options

    Notes
    -----
    ``system=True`` maps to pydynpd's level equation being included. ``system=False``
    appends ``nolevel``, giving Difference GMM.
    """

    left = " ".join([spec.dependent, *(_format_regressor(v) for v in spec.regressors)])
    instruments = " ".join(
        [*(_format_gmm(g, spec.collapse) for g in spec.gmm), *(_format_iv(v) for v in spec.iv)]
    )
    options: list[str] = []

    if spec.time_dummies:
        options.append("timedumm")
    if not spec.system:
        options.append("nolevel")
    # pydynpd defaults to two-step System GMM unless options request otherwise.
    # The public tutorial documents onestep, nolevel, iterated, timedumm, hqic, and collapse.
    # We therefore do not emit an undocumented transformation option here.
    if spec.collapse:
        options.append("collapse")
    if spec.steps == "onestep":
        options.append("onestep")
    elif spec.steps == "iterated":
        options.append("iterated")
    # twostep is pydynpd's default, so no explicit option is emitted.

    return " | ".join([left, instruments, " ".join(options)]).strip()


def run_pydynpd(
    spec: DynamicPanelSpec,
    data: pd.DataFrame,
    panel_ids: Sequence[str],
    *,
    command_override: str | None = None,
) -> Any:
    """Run a specification using pydynpd if installed.

    Parameters
    ----------
    spec:
        Structured dynamic-panel specification.
    data:
        Input DataFrame.
    panel_ids:
        Two columns: entity id and time id.
    command_override:
        Optional raw pydynpd command string.

    Returns
    -------
    Any
        The object returned by ``pydynpd.regression.abond``.
    """

    if len(panel_ids) != 2:
        raise ValueError("panel_ids must contain exactly [entity_id, time_id].")

    try:
        regression = importlib.import_module("pydynpd.regression")
    except ModuleNotFoundError as exc:
        raise ImportError(
            "pydynpd is required for estimation. Install it with: "
            "python -m pip install 'systemgmmkit[pydynpd]'"
        ) from exc

    command = command_override or build_pydynpd_command(spec)
    return regression.abond(command, data, list(panel_ids))
