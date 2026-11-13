
from pathlib import Path
import numpy as np
import pandas as pd

from src.forecasting.prophet_model import (
    prepare_prophet_data,
    fit_prophet,
    make_forecast
)
from src.forecasting.evaluation import evaluate_model

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data" / "processed" / "cleaned_inventory.csv"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "prophet_actual"


def main():
    print("Loading actual dataset...")

    df = pd.read_csv(DATA_PATH)

    # Aggregate demand by date, same as SARIMAX
    daily = (
        df.groupby("date", as_index=False)["demand"]
        .sum()
    )

    daily["date"] = pd.to_datetime(daily["date"])
    daily = daily.sort_values("date")

    daily = daily.set_index("date").asfreq("D")
    daily["demand"] = daily["demand"].fillna(0)
    daily = daily.reset_index()

    # Prepare Prophet data
    prophet_data = prepare_prophet_data(
        daily,
        date_col="date",
        target_col="demand"
    )

    # Same chronological 80/20 split as SARIMAX
    split_index = int(len(prophet_data) * 0.8)

    train_data = prophet_data.iloc[:split_index].copy()
    test_data = prophet_data.iloc[split_index:].copy()

    print("Training observations:", len(train_data))
    print("Testing observations:", len(test_data))

    print("\nTraining Prophet on actual demand...")

    model = fit_prophet(
        train_data,
       yearly_seasonality=False,
       weekly_seasonality=True,
       daily_seasonality=False
    )

    # Forecast the test dates
    forecast = make_forecast(
        model,
        test_data["ds"]
    )

    actual = test_data["y"].to_numpy()
    predicted = forecast["yhat"].to_numpy()

    # Naive baseline for fair comparison
    naive = np.repeat(
        train_data["y"].iloc[-1],
        len(test_data)
    )

    metrics = pd.DataFrame({
        "Naive": evaluate_model(actual, naive),
        "Prophet": evaluate_model(actual, predicted)
    }).T

    predictions = pd.DataFrame({
        "date": test_data["ds"].values,
        "actual": actual,
        "naive_forecast": naive,
        "prophet_forecast": predicted,
        "lower_95": forecast["yhat_lower"].values,
        "upper_95": forecast["yhat_upper"].values
    })

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    predictions.to_csv(
        OUTPUT_DIR / "prophet_forecasts.csv",
        index=False
    )

    metrics.to_csv(
        OUTPUT_DIR / "prophet_metrics.csv"
    )

    print("\nProphet evaluation metrics:")
    print(metrics)

    print("\nForecast preview:")
    print(predictions.head())

    print("\nProphet actual-data training completed!")


if __name__ == "__main__":
    main()
