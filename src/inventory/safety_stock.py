"""Safety-stock calculations.

All demand values must use the same time unit (for example, units/day), and
lead time must use the matching unit (days). The normal-demand assumption is
an approximation; document it when presenting results.
"""
from __future__ import annotations

import math
from statistics import NormalDist


def z_score_for_service_level(service_level: float) -> float:
    """Return the standard-normal z value for a cycle service level (0, 1)."""
    if not 0 < service_level < 1:
        raise ValueError("service_level must be strictly between 0 and 1")
    return NormalDist().inv_cdf(service_level)


def calculate_safety_stock(
    average_daily_demand: float,
    demand_std: float,
    lead_time_days: float,
    service_level: float = 0.95,
    lead_time_std: float = 0.0,
) -> int:
    """Calculate safety stock using demand and optional lead-time variability.

    With fixed lead time: Z * sigma_demand * sqrt(lead_time).
    With variable lead time (independent demand and lead time):
    Z * sqrt(L * sigma_demand**2 + mean_demand**2 * sigma_lead_time**2).

    The returned stock is rounded up to a whole unit.
    """
    values = (average_daily_demand, demand_std, lead_time_days, lead_time_std)
    if any(not math.isfinite(float(v)) for v in values):
        raise ValueError("Inputs must be finite numbers")
    if average_daily_demand < 0 or demand_std < 0 or lead_time_days < 0 or lead_time_std < 0:
        raise ValueError("Demand, standard deviations and lead time cannot be negative")
    z = z_score_for_service_level(service_level)
    variance_during_lead_time = (
        lead_time_days * demand_std**2
        + average_daily_demand**2 * lead_time_std**2
    )
    return int(math.ceil(z * math.sqrt(variance_during_lead_time)))


def safety_stock_from_history(
    daily_demand,
    lead_time_days: float,
    service_level: float = 0.95,
    lead_time_std: float = 0.0,
) -> int:
    """Estimate safety stock from a sequence/Series of historical daily demand."""
    values = [float(x) for x in daily_demand]
    if len(values) < 2:
        raise ValueError("At least two daily demand observations are required")
    if any(not math.isfinite(x) or x < 0 for x in values):
        raise ValueError("Historical demand must contain finite, non-negative values")
    mean_demand = sum(values) / len(values)
    variance = sum((x - mean_demand) ** 2 for x in values) / (len(values) - 1)
    return calculate_safety_stock(
        mean_demand, math.sqrt(variance), lead_time_days,
        service_level=service_level, lead_time_std=lead_time_std,
    )
