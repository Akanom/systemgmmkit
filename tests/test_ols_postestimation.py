import numpy as np
import pandas as pd

from systemgmmkit import (
    OLSSpec,
    PooledOLSSpec,
    confint,
    estat_vce,
    fitted_values,
    lincom,
    marginal_effects,
    margins,
    predict,
    predict_stata,
    residuals,
    run_ols,
    run_pooled_ols,
    vcov,
    wald_test,
)


def make_data(n=80):
    rng = np.random.default_rng(12345)

    x = rng.normal(size=n)
    z = rng.normal(size=n)
    group = np.repeat(np.arange(10), n // 10)
    eps = rng.normal(scale=0.05, size=n)
    y = 1.0 + 2.0 * x - 0.5 * z + eps

    return pd.DataFrame(
        {
            "y": y,
            "x": x,
            "z": z,
            "entity": group,
            "time": np.tile(np.arange(n // 10), 10),
        }
    )


def test_run_ols_estimates_known_linear_model():
    df = make_data()

    spec = OLSSpec(
        dependent="y",
        regressors=["x", "z"],
        covariance="robust",
        name="ols_test",
    )

    result = run_ols(spec, df)

    assert result.nobs == len(df)
    assert "_con" in result.params.index
    assert abs(result.params["_con"] - 1.0) < 0.03
    assert abs(result.params["x"] - 2.0) < 0.03
    assert abs(result.params["z"] + 0.5) < 0.03
    assert result.r2 > 0.99


def test_run_pooled_ols_with_clustered_covariance():
    df = make_data()

    spec = PooledOLSSpec(
        dependent="y",
        regressors=["x", "z"],
        covariance="clustered",
        name="pooled_test",
    )

    result = run_pooled_ols(
        spec,
        df,
        entity="entity",
        time="time",
    )

    assert result.nobs == len(df)
    assert result.cluster == "entity"
    assert result.covariance.shape == (3, 3)
    assert np.isfinite(result.std_errors).all()


def test_postestimation_helpers():
    df = make_data()

    spec = OLSSpec(
        dependent="y",
        regressors=["x", "z"],
        covariance="robust",
    )

    result = run_ols(spec, df)

    pred = predict(result)
    fit = fitted_values(result)
    res = residuals(result)
    cov = vcov(result)
    ci = confint(result)
    me = marginal_effects(result)

    assert len(pred) == len(df)
    assert len(fit) == len(df)
    assert len(res) == len(df)
    assert cov.shape == (3, 3)
    assert set(ci.columns) == {"lower", "upper"}
    assert set(me["variable"]) == {"x", "z"}


def test_lincom_and_wald_test():
    df = make_data()

    spec = OLSSpec(
        dependent="y",
        regressors=["x", "z"],
        covariance="robust",
    )

    result = run_ols(spec, df)

    lc = lincom(result, {"x": 1.0, "z": 1.0})

    assert "estimate" in lc
    assert "p_value" in lc
    assert abs(lc["estimate"] - 1.5) < 0.06

    R = [
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
    ]

    wt = wald_test(result, R=R)

    assert wt["df_constraints"] == 2.0
    assert wt["p_value"] < 0.001


def test_lincom_and_wald_test_accept_simple_strings():
    df = make_data()

    spec = OLSSpec(
        dependent="y",
        regressors=["x", "z"],
        covariance="robust",
    )

    result = run_ols(spec, df)

    lc = lincom(result, "x + z")
    lc_with_null = lincom(result, "x + z = 1.5")

    assert abs(lc["estimate"] - 1.5) < 0.06
    assert abs(lc_with_null["value"] - 1.5) < 1e-12
    assert abs(lc_with_null["statistic"]) < 3.0
    assert lc["distribution"] == "t"
    assert lc["df_resid"] == float(result.df_inference)

    wt = wald_test(result, "x = 0, z = 0")
    wt_parentheses = wald_test(result, "test (x = 0) (z = 0)")
    wt_combo = wald_test(result, "x + z = 1.5")

    assert wt["df_constraints"] == 2.0
    assert wt["distribution"] == "F"
    assert wt["df_denom"] == float(result.df_inference)
    assert wt["p_value"] < 0.001
    assert wt_parentheses["df_constraints"] == 2.0
    assert wt_parentheses["distribution"] == "F"
    assert wt_combo["df_constraints"] == 1.0


def test_stata_style_postestimation_aliases_and_level_option():
    df = make_data()

    spec = OLSSpec(
        dependent="y",
        regressors=["x", "z"],
        covariance="robust",
    )

    result = run_ols(spec, df)

    ci95 = confint(result, level=95)
    ci90 = confint(result, level=90)

    assert (ci90["upper"] - ci90["lower"]).lt(ci95["upper"] - ci95["lower"]).all()
    assert estat_vce(result).equals(vcov(result))

    xb = predict_stata(result, option="xb")
    fit = predict_stata(result, option="fitted")
    resid = predict_stata(result, option="resid")

    assert len(xb) == len(df)
    assert np.allclose(xb, fit)
    assert np.allclose(resid, residuals(result))

    me = margins(result, dydx=["x"], level=90)
    assert me["variable"].tolist() == ["x"]
    assert "dy_dx" in me.columns

    lc90 = lincom(result, "x + z", level=90)
    assert abs(lc90["alpha"] - 0.1) < 1e-12


def test_predict_new_data():
    df = make_data()

    spec = OLSSpec(
        dependent="y",
        regressors=["x", "z"],
    )

    result = run_ols(spec, df)

    new = pd.DataFrame({"x": [0.0, 1.0], "z": [0.0, 2.0]})
    pred = result.predict(new)

    assert len(pred) == 2
    assert np.isfinite(pred).all()
