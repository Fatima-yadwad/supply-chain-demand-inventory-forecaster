
"""
Evaluation metrics for demand forecasting models.
"""

import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error


def evaluate_model(actual, predicted):
    """
    Calculate evaluation metrics by comparing actual
    demand with predicted demand.
    """

    actual = np.asarray(actual, dtype=float)
    predicted = np.asarray(predicted, dtype=float)

    if len(actual) != len(predicted):
        raise ValueError(
            "Actual and predicted values must have the same length."
        )

    if len(actual) == 0:
        raise ValueError("Evaluation data cannot be empty.")

    if not np.all(np.isfinite(actual)) or not np.all(np.isfinite(predicted)):
        raise ValueError("Values must not contain NaN or infinity.")

    errors = predicted - actual

    # Mean Absolute Error
    mae = mean_absolute_error(actual, predicted)

    # Root Mean Squared Error
    rmse = np.sqrt(mean_squared_error(actual, predicted))

    # Mean Absolute Percentage Error
    # Ignore zero actual values to avoid division by zero.
    non_zero_mask = actual != 0

    if np.any(non_zero_mask):
        mape = np.mean(
            np.abs(errors[non_zero_mask] / actual[non_zero_mask])
        ) * 100
    else:
        mape = np.nan

    # Weighted Absolute Percentage Error
    total_actual = np.sum(np.abs(actual))

    if total_actual != 0:
        wape = (np.sum(np.abs(errors)) / total_actual) * 100
    else:
        wape = np.nan

    # Forecast Bias
    # Positive bias means over-forecasting.
    bias = np.mean(errors)

    return {
        "MAE": mae,
        "RMSE": rmse,
        "MAPE": mape,
        "WAPE": wape,
        "Forecast Bias": bias
    }
