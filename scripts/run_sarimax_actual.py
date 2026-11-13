
from pathlib import Path
import pandas as pd

from src.forecasting.sarimax_model import run_forecasting

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data" / "processed" / "cleaned_inventory.csv"
OUTPUT_DIR = PROJECT_ROOT / "outputs"

def main():
    print("Loading actual inventory dataset...")

    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)

    print("Dataset shape:", df.shape)
    print("Available columns:", df.columns.tolist())

    # Confirm required columns
    required = {"date", "demand"}
    if not required.issubset(df.columns):
        raise ValueError(f"Missing columns: {required - set(df.columns)}")

    print("\nDate range:")
    print(df["date"].min(), "to", df["date"].max())

    print("\nTraining SARIMAX on actual demand data...")

    predictions, metrics, model = run_forecasting(
        data=df,
        date_col="date",
        demand_col="demand",
        seasonal_period=7,
        test_size=0.2,
        output_dir=str(OUTPUT_DIR)
    )

    print("\nActual-data forecasting completed!")
    print("\nEvaluation metrics:")
    print(metrics)

    print("\nForecast preview:")
    print(predictions.head())

    print("\nSaved files:")
    print(OUTPUT_DIR / "sarimax_forecasts.csv")
    print(OUTPUT_DIR / "evaluation_metrics.csv")

if __name__ == "__main__":
    main()
