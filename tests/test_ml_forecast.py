import pandas as pd

from systemgmmkit.ml import forecast


class DynamicResult:
    params = pd.Series(
        {
            "L1.y": 0.5,
            "x": 1.0,
            "_con": 0.0,
        }
    )


class DynamicTwoLagResult:
    params = pd.Series(
        {
            "L1.y": 0.5,
            "L2.y": 0.25,
            "x": 1.0,
            "_con": 0.0,
        }
    )


class StaticResult:
    params = pd.Series(
        {
            "x": 2.0,
            "_con": 1.0,
        }
    )


def test_forecast_dynamic_panel_recursive_one_lag():
    history = pd.DataFrame(
        {
            "id": [1, 1],
            "t": [1, 2],
            "y": [2.0, 4.0],
            "x": [10.0, 10.0],
        }
    )

    future = pd.DataFrame(
        {
            "id": [1, 1],
            "t": [3, 4],
            "x": [10.0, 10.0],
        }
    )

    out = forecast(
        DynamicResult(),
        history,
        y="y",
        entity="id",
        time="t",
        horizon=2,
        future_exog=future,
    )

    assert out["prediction"].round(8).tolist() == [12.0, 16.0]
    assert out["horizon"].tolist() == [1, 2]


def test_forecast_dynamic_panel_recursive_two_lags():
    history = pd.DataFrame(
        {
            "id": [1, 1, 1],
            "t": [1, 2, 3],
            "y": [2.0, 4.0, 8.0],
            "x": [10.0, 10.0, 10.0],
        }
    )

    future = pd.DataFrame(
        {
            "id": [1, 1],
            "t": [4, 5],
            "x": [10.0, 10.0],
        }
    )

    out = forecast(
        DynamicTwoLagResult(),
        history,
        y="y",
        entity="id",
        time="t",
        horizon=2,
        future_exog=future,
    )

    # h1 = 0.5*8 + 0.25*4 + 10 = 15
    # h2 = 0.5*15 + 0.25*8 + 10 = 19.5
    assert out["prediction"].round(8).tolist() == [15.0, 19.5]


def test_forecast_static_model_holds_latest_exog_constant_without_future_exog():
    history = pd.DataFrame(
        {
            "id": [1, 1, 2, 2],
            "t": [1, 2, 1, 2],
            "y": [3.0, 5.0, 4.0, 6.0],
            "x": [1.0, 2.0, 2.0, 3.0],
        }
    )

    out = forecast(
        StaticResult(),
        history,
        y="y",
        entity="id",
        time="t",
        horizon=2,
    )

    entity_1 = out.loc[out["id"] == 1, "prediction"].tolist()
    entity_2 = out.loc[out["id"] == 2, "prediction"].tolist()

    assert entity_1 == [5.0, 5.0]
    assert entity_2 == [7.0, 7.0]


def test_forecast_raises_on_missing_required_exog_when_strict():
    history = pd.DataFrame(
        {
            "id": [1, 1],
            "t": [1, 2],
            "y": [2.0, 4.0],
        }
    )

    try:
        forecast(
            StaticResult(),
            history,
            y="y",
            entity="id",
            time="t",
            horizon=1,
        )
    except KeyError as exc:
        assert "x" in str(exc)
    else:
        raise AssertionError("Expected missing exogenous column to raise KeyError.")
