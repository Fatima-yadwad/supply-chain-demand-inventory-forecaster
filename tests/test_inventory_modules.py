import math
import pandas as pd
import pytest

from src.inventory.safety_stock import calculate_safety_stock
from src.inventory.reorder_point import calculate_reorder_point, replenishment_recommendation
from src.inventory.inventory_simulation import simulate_inventory
from src.inventory.allocation import allocate_inventory
from src.analytics.spike_detection import detect_demand_spikes
from src.analytics.bullwhip import calculate_bullwhip_ratio


def test_safety_stock_positive_and_rounds_up():
    assert calculate_safety_stock(100, 20, 5, 0.95) == 74


def test_reorder_point():
    assert calculate_reorder_point(100, 5, 74) == 574


def test_replenishment_recommendation():
    result = replenishment_recommendation(300, 350, 500, on_order=0)
    assert result["reorder_required"] is True
    assert result["recommended_order_quantity"] == 500


def test_simulation_records_stockout_and_fill_rate():
    daily, summary = simulate_inventory([10, 20, 30], 25, 5, 20, 2)
    assert len(daily) == 3
    assert summary["total_lost_sales"] > 0
    assert 0 <= summary["fill_rate"] <= 1


def test_allocation_respects_stock_and_demand():
    result = allocate_inventory({"A": 10, "B": 20}, 15)
    assert sum(result.values()) == 15
    assert result["A"] <= 10 and result["B"] <= 20


def test_spike_detection_uses_prior_window():
    df = pd.DataFrame({"date": pd.date_range("2026-01-01", periods=8), "sku": "P1", "actual_demand": [10, 11, 9, 10, 10, 11, 10, 40]})
    result = detect_demand_spikes(df, window=5, threshold=2)
    assert bool(result.iloc[-1]["is_spike"]) is True


def test_bullwhip_ratio():
    ratio = calculate_bullwhip_ratio([10, 12, 9, 11], [10, 16, 6, 14])
    assert ratio > 1


def test_invalid_service_level_raises():
    with pytest.raises(ValueError):
        calculate_safety_stock(100, 20, 5, 1.0)
