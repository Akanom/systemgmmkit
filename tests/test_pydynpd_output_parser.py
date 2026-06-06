from __future__ import annotations

import pandas as pd

from systemgmmkit.pydynpd_output_parser import (
    enrich_result_with_parsed_standard_errors,
    parse_pydynpd_output_table,
)


def test_parse_pydynpd_output_table_extracts_corrected_standard_errors():
    text = """
+-----------------+------------+---------------------+------------+-----------+-----+
|   growth_rate   |   coef.    | Corrected Std. Err. |     z      |   P>|z|   |     |
+-----------------+------------+---------------------+------------+-----------+-----+
|  L1.growth_rate | 0.3293583  |      0.0511580      | 6.4380580  | 0.0000000 | *** |
|       lPA       | 0.0087622  |      0.0026726      | 3.2785909  | 0.0010433 |  ** |
|   s_techshare   | 0.0020376  |      0.0144527      | 0.1409805  | 0.8878854 |     |
+-----------------+------------+---------------------+------------+-----------+-----+
"""

    params, std_errors, pvalues = parse_pydynpd_output_table(text)

    assert abs(params["L1.growth_rate"] - 0.3293583) < 1e-12
    assert abs(std_errors["L1.growth_rate"] - 0.0511580) < 1e-12
    assert abs(std_errors["lPA"] - 0.0026726) < 1e-12
    assert abs(pvalues["lPA"] - 0.0010433) < 1e-12


def test_enrich_result_with_parsed_standard_errors_aligns_to_existing_params():
    class Result:
        pass

    result = Result()
    result.params = pd.Series(
        {
            "L1.growth_rate": 0.3293583,
            "lPA": 0.0087622,
        },
        name="coefficient",
    )
    result.std_errors = pd.Series(dtype=float)
    result.pvalues = pd.Series(
        {
            "L1.growth_rate": 0.0,
            "lPA": 0.0010433,
        },
        name="p_value",
    )
    result.raw_output = """
|  L1.growth_rate | 0.3293583  |      0.0511580      | 6.4380580  | 0.0000000 | *** |
|       lPA       | 0.0087622  |      0.0026726      | 3.2785909  | 0.0010433 |  ** |
|   s_techshare   | 0.0020376  |      0.0144527      | 0.1409805  | 0.8878854 |     |
"""

    enriched = enrich_result_with_parsed_standard_errors(result)

    assert list(enriched.std_errors.index) == ["L1.growth_rate", "lPA"]
    assert abs(enriched.std_errors["L1.growth_rate"] - 0.0511580) < 1e-12
    assert abs(enriched.std_errors["lPA"] - 0.0026726) < 1e-12


def test_parse_pydynpd_output_table_returns_empty_on_non_table_text():
    params, std_errors, pvalues = parse_pydynpd_output_table("Number of obs = 1152")

    assert len(params) == 0
    assert len(std_errors) == 0
    assert len(pvalues) == 0
