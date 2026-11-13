
import numpy as np
import pandas as pd
from pathlib import Path


def calculate_safety_stock(forecast_errors, lead_time, z_score=1.65):
    """Calculate safety stock using historical forecast errors."""

    error_std = np.std(forecast_errors, ddof=1)

    return z_score * error_std * np.sqrt(lead_time)


def calculate_reorder_point(lead_time_demand, safety_stock):
    """Calculate reorder point."""

    return lead_time_demand + safety_stock


def calculate_eoq(annual_demand, ordering_cost, holding_cost):
    """Calculate Economic Order Quantity."""

    if annual_demand < 0 or ordering_cost < 0 or holding_cost <= 0:
        raise ValueError("Invalid demand or cost values.")

    return np.sqrt(
        (2 * annual_demand * ordering_cost) / holding_cost
    )


def optimize_inventory(
    forecast_file,
    lead_time=7,
    ordering_cost=100,
    holding_cost=10,
    current_stock=1000
):

    df = pd.read_csv(forecast_file)

    required_columns = [
        "date", "actual", "sarimax_forecast"
    ]

    for column in required_columns:
        if column not in df.columns:
            raise ValueError(f"Missing column: {column}")

    df["date"] = pd.to_datetime(df["date"])

    df = df.sort_values("date").reset_index(drop=True)

    df = df.dropna(
        subset=["actual", "sarimax_forecast"]
    )

    if len(df) <= lead_time:
        raise ValueError(
            "Not enough observations for the selected lead time."
        )

    if (df[["actual", "sarimax_forecast"]] < 0).any().any():
        raise ValueError("Demand values cannot be negative.")

    # Estimate forecasting errors
    forecast_errors = (
        df["actual"] - df["sarimax_forecast"]
    ).values

    # Use the next lead-time forecast observations
    lead_time_forecasts = (
        df["sarimax_forecast"].iloc[:lead_time].values
    )

    lead_time_demand = np.sum(lead_time_forecasts)

    avg_daily_demand = df["sarimax_forecast"].mean()

    # Safety stock
    safety_stock = calculate_safety_stock(
        forecast_errors,
        lead_time
    )

    # Reorder point
    reorder_point = calculate_reorder_point(
        lead_time_demand,
        safety_stock
    )

    # Annual demand
    annual_demand = avg_daily_demand * 365

    # EOQ
    eoq = calculate_eoq(
        annual_demand,
        ordering_cost,
        holding_cost
    )

    # Inventory status
    reorder_status = (
        "REORDER REQUIRED"
        if current_stock <= reorder_point
        else "STOCK SUFFICIENT"
    )

    recommended_order = (
        max(0, eoq)
        if reorder_status == "REORDER REQUIRED"
        else 0
    )

    return {
        "Average Daily Demand": round(avg_daily_demand, 2),
        "Lead Time Demand": round(lead_time_demand, 2),
        "Safety Stock": round(safety_stock, 2),
        "Reorder Point": round(reorder_point, 2),
        "Economic Order Quantity": round(eoq, 2),
        "Current Stock": current_stock,
        "Reorder Status": reorder_status,
        "Recommended Order Quantity": round(recommended_order, 2)
    }


if __name__ == "__main__":

    # Locate project directory
    project_root = Path(__file__).resolve().parents[2]

    forecast_file = (
        project_root / "outputs" / "sarimax_forecasts.csv"
    )

    results = optimize_inventory(
        forecast_file=forecast_file,
        lead_time=7,
        ordering_cost=100,
        holding_cost=10,
        current_stock=1000
    )

    print("\n===== INVENTORY OPTIMIZATION RESULTS =====")

    for key, value in results.items():
        print(f"{key}: {value}")

    # Export inventory recommendations
    output_folder = project_root / "outputs"
    output_folder.mkdir(exist_ok=True)

    result_df = pd.DataFrame([results])

    result_df.to_csv(
        output_folder / "inventory_recommendations.csv",
        index=False
    )

    print("\nInventory recommendations exported successfully!")
