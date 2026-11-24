
from __future__ import annotations

import numpy as np
import pandas as pd
from statsmodels.tsa.statespace.sarimax import SARIMAX


def _metrics(actual, predicted):
    actual = np.asarray(actual, dtype=float)
    predicted = np.asarray(predicted, dtype=float)

    errors = predicted - actual
    total = np.abs(actual).sum()

    return {
        "mae": round(float(np.mean(np.abs(errors))), 2),
        "rmse": round(float(np.sqrt(np.mean(errors ** 2))), 2),
        "wape": round(
            float(np.abs(errors).sum() / total * 100), 2
        ) if total else None,
    }


def _prepare_series(data):
    required = {"date", "demand"}

    if not required.issubset(data.columns):
        raise ValueError("Dataset must contain date and demand columns.")

    df = data[["date", "demand"]].copy()
    df["date"] = pd.to_datetime(
        df["date"], errors="coerce"
    ).dt.normalize()
    df["demand"] = pd.to_numeric(df["demand"], errors="coerce")
    df = df.dropna()

    if (df["demand"] < 0).any():
        raise ValueError("Demand cannot contain negative values.")

    observed_daily = (
        df.groupby("date")["demand"]
        .sum()
        .sort_index()
    )

    if len(observed_daily) < 14:
        raise ValueError(
            "At least 14 distinct historical dates are required."
        )

    return observed_daily.asfreq("D", fill_value=0)


def forecast_demand(data, horizon=7):
    """
    Compare a seven-day seasonal-naive baseline with SARIMAX.
    Select the model with the lower validation WAPE and forecast
    the requested number of future days.
    """

    if horizon not in [7, 15, 30]:
        raise ValueError("Forecast horizon must be 7, 15 or 30 days.")

    series = _prepare_series(data)

    validation_size = min(
        max(7, int(len(series) * 0.2)),
        len(series) // 3,
    )

    train = series.iloc[:-validation_size]
    actual = series.iloc[-validation_size:]

    # Seven-day seasonal-naive baseline.
    baseline = np.resize(
        train.iloc[-min(7, len(train)):].to_numpy(),
        validation_size,
    )

    model_scores = {
        "Naive": _metrics(actual, baseline)
    }

    sarimax_available = False
    model_errors = {}

    # Try SARIMAX only when enough history is available.
    if len(train) >= 60:
        try:
            model = SARIMAX(
                train,
                order=(1, 1, 1),
                seasonal_order=(1, 1, 1, 7),
                enforce_stationarity=False,
                enforce_invertibility=False,
            )

            fitted = model.fit(disp=False, maxiter=100)
            predicted = fitted.get_forecast(
                steps=validation_size
            ).predicted_mean

            model_scores["SARIMAX"] = _metrics(
                actual,
                np.maximum(predicted.to_numpy(), 0),
            )

            sarimax_available = True

        except Exception as error:
            sarimax_available = False
            model_errors["SARIMAX"] = (
                f"{type(error).__name__}: {error}"
            )

    # Prefer the lowest WAPE; use RMSE and MAE when WAPE is undefined.
    best_model = min(
        model_scores,
        key=lambda name: (
            model_scores[name]["wape"]
            if model_scores[name]["wape"] is not None
            else float("inf"),
            model_scores[name]["rmse"],
            model_scores[name]["mae"],
        ),
    )

    if best_model == "SARIMAX" and sarimax_available:
        final_model = SARIMAX(
            series,
            order=(1, 1, 1),
            seasonal_order=(1, 1, 1, 7),
            enforce_stationarity=False,
            enforce_invertibility=False,
        ).fit(disp=False, maxiter=100)

        future = final_model.get_forecast(steps=horizon)
        forecast_values = np.maximum(
            future.predicted_mean.to_numpy(), 0
        )

        confidence = future.conf_int()
        lower = np.maximum(confidence.iloc[:, 0].to_numpy(), 0)
        upper = np.maximum(confidence.iloc[:, 1].to_numpy(), 0)

    else:
        last_values = series.iloc[-min(7, len(series)):].to_numpy()
        forecast_values = np.maximum(
            np.resize(last_values, horizon), 0
        )

        # Naive baseline has no statistical confidence interval.
        lower = None
        upper = None

    future_dates = pd.date_range(
        start=series.index.max() + pd.Timedelta(days=1),
        periods=horizon,
        freq="D",
    )

    predictions = []

    for index, date in enumerate(future_dates):
        item = {
            "date": date.strftime("%Y-%m-%d"),
            "predicted_demand": round(float(forecast_values[index]), 2),
        }

        if lower is not None:
            item["lower_bound"] = round(float(lower[index]), 2)
            item["upper_bound"] = round(float(upper[index]), 2)

        predictions.append(item)

    historical = [
        {
            "date": date.strftime("%Y-%m-%d"),
            "actual_demand": round(float(value), 2),
        }
        for date, value in series.tail(30).items()
    ]

    return {
        "selected_model": best_model,
        "forecast_horizon": horizon,
        "historical_days": int(len(series)),
        "validation_metrics": model_scores,
        "model_errors": model_errors,
        "historical": historical,
        "forecast": predictions,
        "total_predicted_demand": round(
            float(forecast_values.sum()), 2
        ),
        "average_daily_forecast": round(
            float(forecast_values.mean()), 2
        ),
        "historical_average_daily_demand": round(
            float(series.mean()), 2
        ),
        "last_historical_date": series.index.max().strftime("%Y-%m-%d"),
        "data_source": "Historical dataset",
    }
