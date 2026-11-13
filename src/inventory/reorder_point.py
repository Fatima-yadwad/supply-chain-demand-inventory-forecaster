"""Reorder-point and replenishment recommendation functions."""
from __future__ import annotations

import math


def calculate_reorder_point(
    average_daily_demand: float,
    lead_time_days: float,
    safety_stock: float,
) -> int:
    """ROP = expected demand during lead time + safety stock."""
    vals = (average_daily_demand, lead_time_days, safety_stock)
    if any(not math.isfinite(float(v)) for v in vals):
        raise ValueError("Inputs must be finite numbers")
    if any(v < 0 for v in vals):
        raise ValueError("Demand, lead time and safety stock cannot be negative")
    return int(math.ceil(average_daily_demand * lead_time_days + safety_stock))


def replenishment_recommendation(
    inventory_on_hand: float,
    reorder_point: float,
    order_quantity: float,
    on_order: float = 0.0,
    backorders: float = 0.0,
) -> dict:
    """Return a simple order recommendation using inventory position.

    Inventory position = on-hand + on-order - backorders. If it is at or below
    the reorder point, recommend the supplied fixed order quantity.
    """
    vals = (inventory_on_hand, reorder_point, order_quantity, on_order, backorders)
    if any(not math.isfinite(float(v)) for v in vals):
        raise ValueError("Inputs must be finite numbers")
    if any(v < 0 for v in vals):
        raise ValueError("Inventory values and quantities cannot be negative")
    position = inventory_on_hand + on_order - backorders
    should_reorder = position <= reorder_point
    return {
        "inventory_position": position,
        "reorder_point": reorder_point,
        "reorder_required": should_reorder,
        "recommended_order_quantity": float(order_quantity) if should_reorder else 0.0,
        "status": "REORDER" if should_reorder else "SUFFICIENT_STOCK",
    }


def order_up_to_quantity(
    target_stock_level: float,
    inventory_on_hand: float,
    on_order: float = 0.0,
    backorders: float = 0.0,
) -> int:
    """Calculate order-up-to quantity, never returning a negative order."""
    vals = (target_stock_level, inventory_on_hand, on_order, backorders)
    if any(not math.isfinite(float(v)) for v in vals):
        raise ValueError("Inputs must be finite numbers")
    if any(v < 0 for v in vals):
        raise ValueError("Inventory values cannot be negative")
    position = inventory_on_hand + on_order - backorders
    return int(math.ceil(max(0.0, target_stock_level - position)))
