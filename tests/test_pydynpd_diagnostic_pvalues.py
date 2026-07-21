from systemgmmkit.pydynpd_backend import _extract_metadata, _valid_p_value


def test_valid_p_value_accepts_real_p_values():
    assert _valid_p_value(0.0) == 0.0
    assert _valid_p_value(0.5) == 0.5
    assert _valid_p_value(1.0) == 1.0


def test_valid_p_value_rejects_invalid_backend_values():
    assert _valid_p_value(2.0) is None
    assert _valid_p_value(-0.1) is None
    assert _valid_p_value(float("nan")) is None
    assert _valid_p_value(float("inf")) is None
    assert _valid_p_value(None) is None


def test_valid_p_value_unwraps_singleton_values():
    assert _valid_p_value([0.25]) == 0.25
    assert _valid_p_value((0.75,)) == 0.75


def test_extract_metadata_parses_pydynpd_overid_prob_chi2_lines():
    raw_output = """
 Dynamic panel-data estimation, two-step system GMM
 Group variable: id                              Number of obs = 245
 Time variable: t                                Min obs per group: 0
 Number of instruments = 7                       Max obs per group: 7
 Number of groups = 45                           Avg obs per group: 5.44
Hansen test of overid. restrictions: chi(3) = 0.980 Prob > Chi2 = 0.806
Sargan test of overid. restrictions: chi(3) = 1.230 Prob > Chi2 = 0.745
Arellano-Bond test for AR(1) in first differences: z = -2.85 Pr > z =0.004
Arellano-Bond test for AR(2) in first differences: z = 0.76 Pr > z =0.446
"""

    metadata = _extract_metadata(raw=object(), output=raw_output)

    assert metadata["nobs"] == 245
    assert metadata["n_groups"] == 45
    assert metadata["n_instruments"] == 7
    assert metadata["hansen_p"] == 0.806
    assert metadata["sargan_p"] == 0.745
    assert metadata["ar1_p"] == 0.004
    assert metadata["ar2_p"] == 0.446
