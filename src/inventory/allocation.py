"""Optional weighted allocation of limited stock across locations."""
from __future__ import annotations

import math


def allocate_inventory(
    demand_by_location: dict[str, float],
    available_units: int,
    priority_weights: dict[str, float] | None = None,
) -> dict[str, int]:
    """Allocate available units proportionally to weighted unmet demand.

    Allocation never exceeds a location's demand and never exceeds total stock.
    Largest-remainder rounding ensures integer allocations use stock fairly.
    """
    if available_units < 0 or int(available_units) != available_units:
        raise ValueError("available_units must be a non-negative integer")
    if not demand_by_location:
        return {}
    for loc, qty in demand_by_location.items():
        if not math.isfinite(float(qty)) or qty < 0:
            raise ValueError(f"Demand for {loc} must be finite and non-negative")
    weights = priority_weights or {}
    for loc, weight in weights.items():
        if not math.isfinite(float(weight)) or weight < 0:
            raise ValueError(f"Priority weight for {loc} must be finite and non-negative")

    allocation = {loc: 0 for loc in demand_by_location}
    remaining = min(int(available_units), int(sum(demand_by_location.values())))
    while remaining > 0:
        eligible = [loc for loc, qty in demand_by_location.items() if allocation[loc] < qty]
        if not eligible:
            break
        scores = {loc: (demand_by_location[loc] - allocation[loc]) * float(weights.get(loc, 1.0)) for loc in eligible}
        total_score = sum(scores.values())
        if total_score <= 0:
            scores = {loc: demand_by_location[loc] - allocation[loc] for loc in eligible}
            total_score = sum(scores.values())
        quotas = {loc: remaining * scores[loc] / total_score for loc in eligible}
        base = {loc: min(int(demand_by_location[loc] - allocation[loc]), math.floor(quotas[loc])) for loc in eligible}
        used = sum(base.values())
        for loc, qty in base.items():
            allocation[loc] += qty
        remaining -= used
        if remaining == 0:
            break
        ranked = sorted(eligible, key=lambda loc: (quotas[loc] - math.floor(quotas[loc]), scores[loc]), reverse=True)
        progressed = False
        for loc in ranked:
            if remaining == 0:
                break
            if allocation[loc] < demand_by_location[loc]:
                allocation[loc] += 1
                remaining -= 1
                progressed = True
        if not progressed:
            break
    return allocation
def allocate_stock_by_product(
    prepared_df,
    available_stock_by_product,
    priority_weights=None,
):
    """Allocate available stock across stores for each product."""

    required = {"store_id", "product_id", "target_demand"}

    missing = required - set(prepared_df.columns)

    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    results = []

    for product, group in prepared_df.groupby("product_id"):

        demand_by_store = (
            group.groupby("store_id")["target_demand"]
            .sum()
            .to_dict()
        )

        available_units = available_stock_by_product.get(product, 0)

        weights = priority_weights or {}

        allocation = allocate_inventory(
            demand_by_location=demand_by_store,
            available_units=available_units,
            priority_weights=weights,
        )

        for store, allocated_units in allocation.items():
            results.append({
                "product_id": product,
                "store_id": store,
                "demand": demand_by_store[store],
                "allocated_stock": allocated_units,
            })

    return results