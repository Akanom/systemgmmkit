from __future__ import annotations


def test_parity_report_done_schema():
    from systemgmmkit.reporting import REQUIRED_PARITY_COLUMNS, ParityReport, ParityResult

    report = ParityReport(
        results=[
            ParityResult(
                spec="difference_gmm_baseline_controls",
                native_nobs=1152,
                native_n_instruments=21,
                pydynpd_nobs=1152,
                pydynpd_n_instruments=21,
                status="PASS_PARITY",
                original_status="PASS_STRICT",
                blocks_release=False,
                same_instrument_count=True,
                max_abs_coef_diff=0.000001,
            )
        ]
    )

    df = report.to_dataframe()

    assert list(df.columns) == REQUIRED_PARITY_COLUMNS
    assert df.loc[0, "spec"] == "difference_gmm_baseline_controls"
    assert df.loc[0, "status"] == "PASS_PARITY"


def test_classify_parity_result_done():
    from systemgmmkit.reporting import classify_parity_result

    result = classify_parity_result(
        spec="difference_gmm_baseline_controls",
        native_nobs=1152,
        pydynpd_nobs=1152,
        native_n_instruments=21,
        pydynpd_n_instruments=21,
        max_abs_coef_diff=1e-7,
    )

    assert result.status == "PASS_PARITY"
    assert result.original_status == "PASS_STRICT"
    assert result.blocks_release is False
