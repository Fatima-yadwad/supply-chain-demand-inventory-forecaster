"""Day-by-day inventory simulation and scenario comparison."""
from __future__ import annotations

import math
from collections import defaultdict
from typing import Iterable

import pandas as pd


def simulate_inventory(
    demand: Iterable[float],
    initial_inventory: float,
    reorder_point: float,
    order_quantity: float,
    lead_time_days: int,
    *,
    safety_stock: float = 0.0,
    dates: Iterable | None = None,
) -> tuple[pd.DataFrame, dict]:
    """Simulate a continuous-review, fixed-order-quantity inventory policy.

    Receipts arrive at the start of the day `lead_time_days` after order
    placement. Demand is served from available stock; unmet demand is recorded
    as lost sales (not carried as backorders). Orders are triggered using
    inventory position = on-hand + on-order. One order can be placed whenever
    the position is at/below the ROP.
    """
    demand_values = [float(x) for x in demand]
    if not demand_values:
        raise ValueError("demand must contain at least one observation")
    if any(not math.isfinite(x) or x < 0 for x in demand_values):
        raise ValueError("Demand must contain finite, non-negative values")
    if lead_time_days < 0 or int(lead_time_days) != lead_time_days:
        raise ValueError("lead_time_days must be a non-negative integer")
    params = (initial_inventory, reorder_point, order_quantity, safety_stock)
    if any(not math.isfinite(float(x)) or x < 0 for x in params):
        raise ValueError("Inventory parameters must be finite and non-negative")
    if order_quantity <= 0:
        raise ValueError("order_quantity must be greater than zero")
    date_values = list(dates) if dates is not None else list(range(1, len(demand_values) + 1))
    if len(date_values) != len(demand_values):
        raise ValueError("dates and demand must have the same length")

    on_hand = float(initial_inventory)
    arrivals = defaultdict(float)
    pending_orders = 0.0
    rows = []
    total_demand = total_fulfilled = total_lost = 0.0
    stockout_days = orders_placed = 0

    for idx, daily_demand in enumerate(demand_values):
        opening = on_hand
        received = arrivals[idx]
        on_hand += received
        pending_orders -= received
        pending_orders = max(0.0, pending_orders)

        fulfilled = min(on_hand, daily_demand)
        lost = daily_demand - fulfilled
        on_hand -= fulfilled
        inventory_position = on_hand + pending_orders
        order_placed = 0.0
        arrival_day = None

        if inventory_position <= reorder_point:
            order_placed = float(order_quantity)
            arrival_idx = idx + int(lead_time_days)
            # A zero-day lead-time order is received immediately after today's demand.
            if int(lead_time_days) == 0:
                on_hand += order_placed
            else:
                arrivals[arrival_idx] += order_placed
                pending_orders += order_placed
                arrival_day = date_values[arrival_idx] if arrival_idx < len(date_values) else f"after_simulation_day_{arrival_idx + 1}"
            orders_placed += 1

        total_demand += daily_demand
        total_fulfilled += fulfilled
        total_lost += lost
        if lost > 0:
            stockout_days += 1

        rows.append({
            "date": date_values[idx],
            "opening_inventory": opening,
            "receipts": received,
            "demand": daily_demand,
            "fulfilled_demand": fulfilled,
            "lost_sales": lost,
            "closing_inventory": on_hand,
            "on_order": pending_orders,
            "inventory_position": on_hand + pending_orders,
            "order_placed": order_placed,
            "expected_arrival": arrival_day,
            "stockout": lost > 0,
        })

    result = pd.DataFrame(rows)
    summary = {
        "total_demand": total_demand,
        "total_fulfilled_demand": total_fulfilled,
        "total_lost_sales": total_lost,
        "fill_rate": total_fulfilled / total_demand if total_demand else 1.0,
        "stockout_day_risk": stockout_days / len(demand_values),
        "stockout_days": stockout_days,
        "cycle_service_level": 1 - stockout_days / len(demand_values),
        "orders_placed": orders_placed,
        "average_closing_inventory": float(result["closing_inventory"].mean()),
        "ending_inventory": float(on_hand),
        "ending_on_order": float(pending_orders),
    }
    return result, summary


def compare_inventory_scenarios(
    demand: Iterable[float],
    scenarios: dict[str, dict],
    *,
    dates: Iterable | None = None,
) -> pd.DataFrame:
    """Run named parameter scenarios and return one summary row per scenario.

    Each scenario dictionary accepts initial_inventory, reorder_point,
    order_quantity, lead_time_days and optional safety_stock.
    """
    rows = []
    for name, params in scenarios.items():
        _, summary = simulate_inventory(demand, dates=dates, **params)
        rows.append({"scenario": name, **summary})
    return pd.DataFrame(rows)

def simulate_inventory_by_product(
    prepared_df,
    reorder_results,
    lead_time_days: int = 7,
):
    """Simulate inventory separately for every store-product combination."""
    required = {
        "date", "store_id", "product_id",
        "target_demand", "inventory_level"
    }
    missing = required - set(prepared_df.columns)

    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    reorder_lookup = {
        (item["store_id"], item["product_id"]): item
        for item in reorder_results
    }

    simulations = {}

    for (store, product), group in prepared_df.groupby(
        ["store_id", "product_id"]
    ):
        group = group.sort_values("date")

        daily = (
            group.groupby("date")
            .agg(
                demand=("target_demand", "sum"),
                inventory=("inventory_level", "first"),
            )
            .sort_index()
        )

        policy = reorder_lookup.get((store, product))

        if policy is None or daily.empty:
            continue

        average_demand = float(daily["demand"].mean())

        # Assumption: one average lead-time demand per replenishment order.
        order_quantity = max(
            1,
            math.ceil(average_demand * lead_time_days)
        )

        simulation, summary = simulate_inventory(
            demand=daily["demand"].tolist(),
            dates=daily.index.tolist(),
            initial_inventory=float(daily["inventory"].iloc[0]),
            reorder_point=policy["reorder_point"],
            order_quantity=order_quantity,
            lead_time_days=lead_time_days,
            safety_stock=policy["safety_stock"],
        )

        simulations[(store, product)] = {
            "daily_results": simulation,
            "summary": summary,
        }

    return simulations
