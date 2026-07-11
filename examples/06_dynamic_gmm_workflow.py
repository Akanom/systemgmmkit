"""Dynamic panel workflow: native Difference GMM and native System GMM.

Run:
    python examples/06_dynamic_gmm_workflow.py
"""

from __future__ import annotations

import pandas as pd

from systemgmmkit import (
    build_difference_gmm_spec,
    build_system_gmm_spec,
    combine_result_frames,
    model_card_markdown,
    run_difference_gmm,
    run_system_gmm,
)

from _shared_panel_data import ensure_results_dir, make_dynamic_panel, write_table_pair


ENTITY = "entity_id"
TIME = "year"
Y = "y"


def diagnostic_row(name: str, result) -> dict[str, float | int | str | None]:
    return {
        "model": name,
        "backend": getattr(result, "backend", ""),
        "nobs": getattr(result, "nobs", None),
        "n_groups": getattr(result, "n_groups", None),
        "n_instruments": getattr(result, "n_instruments", None),
        "hansen_p": getattr(result, "hansen_p", None),
        "sargan_p": getattr(result, "sargan_p", None),
        "ar1_p": getattr(result, "ar1_p", None),
        "ar2_p": getattr(result, "ar2_p", None),
        "overid_df": getattr(result, "overid_df", None),
    }


def main() -> None:
    df = make_dynamic_panel()

    common_spec_kwargs = {
        "dependent": Y,
        "regressors": ["x1", "x2", "control"],
        "endogenous": ["x1"],
        "predetermined": ["x2"],
        "exogenous": ["control"],
        "lag_limits": {
            "y": (2, 3),
            "x1": (2, 2),
            "x2": (2, 2),
        },
        "collapse": True,
        "time_dummies": False,
        "steps": "twostep",
    }

    diff_spec = build_difference_gmm_spec(
        **common_spec_kwargs,
        transformation="fd",
        name="difference_gmm_native",
    )
    system_spec = build_system_gmm_spec(
        **common_spec_kwargs,
        transformation="fod",
        name="system_gmm_native",
    )

    diff = run_difference_gmm(
        diff_spec,
        df,
        entity=ENTITY,
        time=TIME,
        backend="native",
    )
    system = run_system_gmm(
        system_spec,
        df,
        entity=ENTITY,
        time=TIME,
        backend="native",
    )

    coefficients = combine_result_frames(
        [diff, system],
        model_names=["Difference GMM native", "System GMM native"],
    )
    write_table_pair(coefficients, "06_dynamic_gmm_coefficients")

    diagnostics = pd.DataFrame(
        [
            diagnostic_row("Difference GMM native", diff),
            diagnostic_row("System GMM native", system),
        ]
    )
    write_table_pair(diagnostics, "06_dynamic_gmm_diagnostics")

    results = ensure_results_dir()
    (results / "06_difference_gmm_native.md").write_text(diff.to_markdown(), encoding="utf-8")
    (results / "06_system_gmm_native.md").write_text(system.to_markdown(), encoding="utf-8")
    (results / "06_system_gmm_model_card.md").write_text(
        model_card_markdown(system_spec, n_entities=df[ENTITY].nunique()),
        encoding="utf-8",
    )

    print("Dynamic GMM diagnostics")
    print(diagnostics.round(4).to_string(index=False))
    print("\nWrote results under examples/results/06_dynamic_gmm_*")


if __name__ == "__main__":
    main()
