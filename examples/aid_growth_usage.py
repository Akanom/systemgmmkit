"""Example usage for aid-growth thesis System GMM specifications."""

from pathlib import Path

import pandas as pd

from systemgmmkit import model_card_markdown, run_pydynpd, validate_panel
from systemgmmkit.presets import aid_growth_ta_decomposition_spec, aid_growth_techshare_spec

DATA = Path("analysis_merged_data_copy.csv")


def main() -> None:
    df = pd.read_csv(DATA)

    spec = aid_growth_techshare_spec(include_controls=True, include_three_way=True)
    report = validate_panel(df, entity="country_id", time="period4", variables=spec.variables)
    print(
        model_card_markdown(
            spec, panel_report=report, n_entities=report.n_entities, n_time_dummies=13
        )
    )

    # Requires: python -m pip install systemgmmkit[pydynpd]
    result = run_pydynpd(spec, df, panel_ids=["country_id", "period4"])
    print(result)

    decomp = aid_growth_ta_decomposition_spec(include_controls=True, include_three_way=True)
    print(model_card_markdown(decomp, n_entities=report.n_entities, n_time_dummies=13))


if __name__ == "__main__":
    main()
