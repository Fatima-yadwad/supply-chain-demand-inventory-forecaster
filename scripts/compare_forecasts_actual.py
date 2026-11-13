
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs"

sarimax = pd.read_csv(
    OUTPUT / "evaluation_metrics.csv", index_col=0
)
prophet = pd.read_csv(
    OUTPUT / "prophet_actual" / "prophet_metrics.csv",
    index_col=0
)

metrics = ["MAE", "RMSE", "WAPE"]

comparison = pd.concat([
    sarimax.loc[["Naive"], metrics],
    sarimax.loc[["SARIMAX"], metrics],
    prophet.loc[["Prophet"], metrics]
])

comparison = comparison.sort_values("WAPE")
print("\nFINAL ACTUAL-DATA MODEL COMPARISON")
print(comparison.round(2))

comparison.to_csv(OUTPUT / "model_comparison_actual.csv")
print("\nSaved model_comparison_actual.csv")
