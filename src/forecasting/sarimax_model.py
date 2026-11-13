
"""
SARIMAX Demand Forecasting Model
Member 2: Chandana

This module includes:
- Naive forecasting baseline
- SARIMAX model
- Seasonal parameter tuning
- Chronological train-test split
- Forecast prediction intervals
- MAE, RMSE and WAPE evaluation
- CSV export
"""

import warnings
import itertools
from pathlib import Path

import numpy as np
import pandas as pd
from statsmodels.tsa.statespace.sarimax import SARIMAX

warnings.filterwarnings("ignore")


# 1. Prepare daily demand data

def prepare_daily_data(data, date_col="date", demand_col="demand"):

    df = data[[date_col, demand_col]].copy()

    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df[demand_col] = pd.to_numeric(df[demand_col], errors="coerce")

    df = df.dropna()
    df = df.sort_values(date_col)

    daily_data = df.groupby(date_col)[demand_col].sum()
    daily_data = daily_data.asfreq("D").fillna(0)

    if len(daily_data) < 30:
        raise ValueError("At least 30 daily observations are required.")

    if (daily_data < 0).any():
        raise ValueError("Demand cannot be negative.")

    return daily_data


# 2. Naive forecasting baseline

def naive_forecast(train_data, forecast_steps):

    last_value = train_data.iloc[-1]

    return np.repeat(last_value, forecast_steps)


# 3. Evaluation metrics

def calculate_metrics(actual, predicted):

    actual = np.asarray(actual, dtype=float)
    predicted = np.asarray(predicted, dtype=float)

    mae = np.mean(np.abs(actual - predicted))

    rmse = np.sqrt(np.mean((actual - predicted) ** 2))

    denominator = np.sum(np.abs(actual))

    wape = (
        np.sum(np.abs(actual - predicted)) / denominator * 100
        if denominator != 0 else np.nan
    )

    return {
        "MAE": mae,
        "RMSE": rmse,
        "WAPE": wape
    }


# 4. Tune SARIMAX parameters using training data only

def tune_sarimax(train_data, seasonal_period=7):

    validation_size = max(7, int(len(train_data) * 0.15))

    fitting_data = train_data.iloc[:-validation_size]
    validation_data = train_data.iloc[-validation_size:]

    orders = [
        (0, 0, 0),
        (1, 0, 0),
        (0, 1, 1),
        (1, 1, 1)
    ]

    seasonal_orders = [
        (0, 0, 0),
        (1, 0, 0),
        (0, 1, 1)
    ]

    best_score = float("inf")
    best_order = None
    best_seasonal_order = None

    for order, seasonal_base in itertools.product(
        orders, seasonal_orders
    ):

        seasonal_order = (
            *seasonal_base,
            seasonal_period
        )

        try:

            model = SARIMAX(
                fitting_data,
                order=order,
                seasonal_order=seasonal_order,
                enforce_stationarity=False,
                enforce_invertibility=False
            )

            fitted_model = model.fit(
                disp=False,
                maxiter=100
            )

            predictions = fitted_model.forecast(
                steps=len(validation_data)
            )

            score = calculate_metrics(
                validation_data,
                predictions
            )["RMSE"]

            if np.isfinite(score) and score < best_score:

                best_score = score
                best_order = order
                best_seasonal_order = seasonal_order

        except Exception:
            continue

    if best_order is None:
        raise RuntimeError("SARIMAX tuning failed.")

    return best_order, best_seasonal_order, best_score


# 5. Complete forecasting pipeline

def run_forecasting(
    data,
    date_col="date",
    demand_col="demand",
    seasonal_period=7,
    test_size=0.2,
    output_dir="outputs"
):

    daily_data = prepare_daily_data(
        data,
        date_col,
        demand_col
    )

    # Chronological train-test split

    split_index = int(len(daily_data) * (1 - test_size))

    train_data = daily_data.iloc[:split_index]
    test_data = daily_data.iloc[split_index:]

    print("Training observations:", len(train_data))
    print("Testing observations:", len(test_data))

    # Naive baseline

    baseline_predictions = naive_forecast(
        train_data,
        len(test_data)
    )

    # Parameter tuning

    best_order, best_seasonal_order, validation_rmse = (
        tune_sarimax(train_data, seasonal_period)
    )

    print("Best order:", best_order)
    print("Best seasonal order:", best_seasonal_order)
    print("Validation RMSE:", validation_rmse)

    # Fit final model using training data

    model = SARIMAX(
        train_data,
        order=best_order,
        seasonal_order=best_seasonal_order,
        enforce_stationarity=False,
        enforce_invertibility=False
    )

    fitted_model = model.fit(
        disp=False,
        maxiter=200
    )

    # Forecast

    forecast_result = fitted_model.get_forecast(
        steps=len(test_data)
    )

    forecast_values = forecast_result.predicted_mean

    intervals = forecast_result.conf_int(alpha=0.05)

    # Prediction output

    predictions_df = pd.DataFrame({

        "date": test_data.index,

        "actual": test_data.values,

        "naive_forecast": baseline_predictions,

        "sarimax_forecast": forecast_values.values,

        "lower_95": intervals.iloc[:, 0].values,

        "upper_95": intervals.iloc[:, 1].values

    })

    # Evaluation

    metrics = {

        "Naive": calculate_metrics(
            test_data,
            baseline_predictions
        ),

        "SARIMAX": calculate_metrics(
            test_data,
            forecast_values
        )

    }

    metrics_df = pd.DataFrame(metrics).T

    # Export

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    predictions_df.to_csv(
        output_path / "sarimax_forecasts.csv",
        index=False
    )

    metrics_df.to_csv(
        output_path / "evaluation_metrics.csv"
    )

    print("\nEvaluation metrics:")
    print(metrics_df)

    print("\nForecast files exported successfully!")

    return predictions_df, metrics_df, fitted_model


# 6. Test using dummy daily demand data
if __name__ == "__main__":
    np.random.seed(42)
    dates = pd.date_range(
        start="2025-01-01",
        periods=365,
        freq="D"
    )
    trend = np.linspace(100, 150, 365)
    weekly_pattern = 15 * np.sin(
        2 * np.pi * np.arange(365) / 7
    )
    noise = np.random.normal(0, 5, 365)
    demand = trend + weekly_pattern + noise
    dummy_df = pd.DataFrame({
        "date": dates,
        "demand": demand
    })
    predictions, metrics, model = run_forecasting(
        dummy_df,
        date_col="date",
        demand_col="demand",
        seasonal_period=7,
        output_dir="outputs"
    )
    print("\nDummy data forecasting completed!")
    print(predictions.head())
    print(metrics)
