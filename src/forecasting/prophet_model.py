
"""
Prophet forecasting model for the Supply Chain Demand
and Inventory Forecasting project.
"""

import pandas as pd
from prophet import Prophet


def prepare_prophet_data(df, date_col, target_col):
    """
    Convert the dataset into the format required by Prophet.

    Prophet requires:
    ds = date column
    y  = demand/target column
    """

    data = df[[date_col, target_col]].copy()

    data.columns = ["ds", "y"]

    data["ds"] = pd.to_datetime(data["ds"], errors="coerce")
    data["y"] = pd.to_numeric(data["y"], errors="coerce")

    data = data.dropna(subset=["ds", "y"])

    data = data.sort_values("ds").reset_index(drop=True)

    if data.empty:
        raise ValueError("No valid date and demand records found.")

    return data


def fit_prophet(
    train_df,
    yearly_seasonality="auto",
    weekly_seasonality="auto",
    daily_seasonality=False,
    seasonality_mode="additive"
):
    """
    Train the Prophet model using training data.
    """

    if not {"ds", "y"}.issubset(train_df.columns):
        raise ValueError("Training data must contain 'ds' and 'y' columns.")

    model = Prophet(
        yearly_seasonality=yearly_seasonality,
        weekly_seasonality=weekly_seasonality,
        daily_seasonality=daily_seasonality,
        seasonality_mode=seasonality_mode
    )

    model.fit(train_df[["ds", "y"]])

    return model


def make_forecast(model, future_dates):
    """
    Generate predictions for the supplied future dates.
    """

    future_df = pd.DataFrame({
        "ds": pd.to_datetime(future_dates)
    })

    forecast = model.predict(future_df)

    return forecast[
        ["ds", "yhat", "yhat_lower", "yhat_upper"]
    ].copy()
