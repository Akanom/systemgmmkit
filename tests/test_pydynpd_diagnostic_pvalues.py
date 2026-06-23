from systemgmmkit.pydynpd_backend import _valid_p_value


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
