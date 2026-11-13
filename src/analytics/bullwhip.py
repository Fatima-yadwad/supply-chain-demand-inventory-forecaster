"""Bullwhip-effect metrics for demand and upstream order series."""
from __future__ import annotations

import pandas as pd


def calculate_bullwhip_ratio(customer_demand, upstream_orders, ddof: int = 1) -> float:
    """Return variance(upstream orders) / variance(customer demand).

    A NaN result is returned when customer-demand variance is zero/undefined;
    the ratio cannot be interpreted in that case.
    """
    demand = pd.Series(customer_demand, dtype="float64").dropna()
    orders = pd.Series(upstream_orders, dtype="float64").dropna()
    if len(demand) != len(orders):
        raise ValueError("Demand and order series must have the same number of non-null values")
    if len(demand) <= ddof:
        raise ValueError("Not enough observations to calculate variance")
    if (demand < 0).any() or (orders < 0).any():
        raise ValueError("Demand and orders cannot be negative")
    demand_var = demand.var(ddof=ddof)
    order_var = orders.var(ddof=ddof)
    if demand_var == 0:
        return float("nan")
    return float(order_var / demand_var)


def bullwhip_by_stage(
    data: pd.DataFrame,
    *,
    stage_col: str = "stage",
    period_col: str = "period",
    quantity_col: str = "quantity",
    customer_stage: str = "customer_demand",
) -> pd.DataFrame:
    """Compare variance at each stage with customer-demand variance.

    Input should have one quantity per stage and period. Example stages might
    be customer_demand, retailer_orders, wholesaler_orders, manufacturer_orders.
    """
    required = {stage_col, period_col, quantity_col}
    missing = required - set(data.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    pivot = data.pivot_table(index=period_col, columns=stage_col, values=quantity_col, aggfunc="mean").sort_index()
    if customer_stage not in pivot.columns:
        raise ValueError(f"customer_stage '{customer_stage}' not found in {stage_col}")
    baseline = pivot[customer_stage].var(ddof=1)
    rows = []
    for stage in pivot.columns:
        series = pivot[stage].dropna()
        variance = series.var(ddof=1)
        ratio = float(variance / baseline) if pd.notna(baseline) and baseline > 0 else float("nan")
        rows.append({"stage": stage, "observations": len(series), "variance": variance, "bullwhip_ratio": ratio})
    return pd.DataFrame(rows).sort_values("stage").reset_index(drop=True)
