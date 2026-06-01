import pandas as pd

from scripts.apply_gmm_parity_policy import reclassify_file


def test_reclassify_native_gmm_parity_failure_as_non_blocking(tmp_path):
    input_csv = tmp_path / "input.csv"
    output_csv = tmp_path / "output.csv"

    pd.DataFrame(
        [
            {
                "estimator": "system_gmm",
                "backend": "native",
                "comparison_backend": "pydynpd",
                "execution_passed": True,
                "strict_parity_passed": False,
            },
            {
                "estimator": "fixed_effects",
                "backend": "native",
                "execution_passed": True,
                "strict_parity_passed": False,
            },
        ]
    ).to_csv(input_csv, index=False)

    result = reclassify_file(input_csv, output_csv)

    assert result.loc[0, "policy_status"] == "EXPERIMENTAL_PARITY_PENDING"
    assert bool(result.loc[0, "blocks_release"]) is False

    assert result.loc[1, "policy_status"] == "FAIL_PARITY"
    assert bool(result.loc[1, "blocks_release"]) is True
