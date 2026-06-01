from systemgmmkit.gmm_parity_policy import (
    EXPERIMENTAL_PARITY_PENDING,
    FAIL_PARITY,
    OPERATIONAL_ONLY,
    PASS_PARITY,
    classify_gmm_parity,
)


def test_pydynpd_gmm_execution_is_production_non_blocking():
    decision = classify_gmm_parity(
        estimator="system_gmm",
        backend="pydynpd",
        execution_passed=True,
        strict_parity_passed=False,
    )

    assert decision.status == OPERATIONAL_ONLY
    assert decision.blocks_release is False


def test_native_gmm_strict_parity_failure_is_experimental_not_blocking():
    decision = classify_gmm_parity(
        estimator="system_gmm",
        backend="native",
        comparison_backend="pydynpd",
        execution_passed=True,
        strict_parity_passed=False,
    )

    assert decision.status == EXPERIMENTAL_PARITY_PENDING
    assert decision.blocks_release is False


def test_native_gmm_execution_failure_blocks_release():
    decision = classify_gmm_parity(
        estimator="system_gmm",
        backend="native",
        comparison_backend="pydynpd",
        execution_passed=False,
        strict_parity_passed=False,
    )

    assert decision.status == FAIL_PARITY
    assert decision.blocks_release is True


def test_non_gmm_strict_parity_stays_strict():
    decision = classify_gmm_parity(
        estimator="fixed_effects",
        backend="native",
        execution_passed=True,
        strict_parity_passed=False,
    )

    assert decision.status == FAIL_PARITY
    assert decision.blocks_release is True


def test_non_gmm_strict_parity_passes_when_equal():
    decision = classify_gmm_parity(
        estimator="fixed_effects",
        backend="native",
        execution_passed=True,
        strict_parity_passed=True,
    )

    assert decision.status == PASS_PARITY
    assert decision.blocks_release is False
