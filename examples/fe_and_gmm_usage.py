"""Example: run FE as the main model and System GMM as robustness."""

from pathlib import Path

import pandas as pd

from systemgmmkit import model_card_markdown, run_fixed_effects, validate_panel
from systemgmmkit.presets import aid_growth_fe_techshare_spec, aid_growth_techshare_spec

DATA = Path("analysis_merged_data_copy.csv")


def main() -> None:
    df = pd.read_csv(DATA)

    fe_spec = aid_growth_fe_techshare_spec(include_controls=True, include_three_way=True)
    fe_report = validate_panel(df, entity="country_id", time="period4", variables=fe_spec.variables)
    print(fe_report.to_dict())

    fe_result = run_fixed_effects(fe_spec, df, entity="country_id", time="period4")
    print(fe_result.to_markdown())

    gmm_spec = aid_growth_techshare_spec(include_controls=True, include_three_way=True)
    print(model_card_markdown(gmm_spec, n_entities=fe_report.n_entities, n_time_dummies=13))


if __name__ == "__main__":
    main()
