import numpy as np
import pandas as pd
from pathlib import Path

np.random.seed(42)

dates = pd.date_range(
    start="2023-01-01",
    periods=730,
    freq="D"
)

trend = np.linspace(100, 160, 730)

weekly_seasonality = 20 * np.sin(
    2 * np.pi * np.arange(730) / 7
)

yearly_seasonality = 12 * np.sin(
    2 * np.pi * np.arange(730) / 365
)

random_noise = np.random.normal(0, 8, 730)

demand = (
    trend
    + weekly_seasonality
    + yearly_seasonality
    + random_noise
)

demand = np.maximum(demand, 0).round().astype(int)

df = pd.DataFrame({
    "date": dates,
    "demand": demand
})

output_path = Path(__file__).parent / "dummy_daily_demand_chandana.csv"

df.to_csv(output_path, index=False)

print("Dummy dataset created successfully!")
print(df.head(10))
print("Dataset shape:", df.shape)