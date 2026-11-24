
import pandas as pd

from src.analytics.spike_detection import detect_spikes_by_product
from src.ai.inventory_service import calculate_inventory_risk


def detect_anomalies(data):
    """Reuse the existing store/product demand spike detector."""

    required = {"date", "store_id", "product_id", "demand"}
    missing = required - set(data.columns)

    if missing:
        raise ValueError(
            f"Missing anomaly detection columns: {sorted(missing)}"
        )

    daily = (
        data.groupby(
            ["date", "store_id", "product_id"],
            as_index=False,
        )["demand"]
        .sum()
        .rename(columns={"demand": "target_demand"})
    )

    detected = detect_spikes_by_product(daily)

    if detected.empty:
        return []

    anomalies = detected[detected["is_spike"]].copy()
    anomalies = anomalies.sort_values(
        "spike_score", ascending=False
    )

    results = []

    for _, row in anomalies.head(100).iterrows():
        results.append({
            "date": pd.Timestamp(row["date"]).strftime("%Y-%m-%d"),
            "store_id": str(row["store_id"]),
            "product_id": str(row["product_id"]),
            "actual_demand": round(
                float(row["target_demand"]), 2
            ),
            "rolling_average": round(
                float(row["rolling_mean"]), 2
            ),
            "spike_score": round(
                float(row["spike_score"]), 2
            ),
            "severity": (
                "High" if row["spike_score"] >= 4
                else "Moderate"
            ),
        })

    return results


def generate_insights(data):
    """Generate operational insights from historical data."""

    if data.empty:
        return {
            "summary": "No data available for the selected filters.",
            "insights": [],
        }

    insights = []

    # Demand trend: compare the latest 28 days with the
    # preceding 28 days available in the historical dataset.
    daily = (
        data.groupby("date")["demand"]
        .sum()
        .sort_index()
    )

    if len(daily) >= 2:
        latest = daily.tail(28)
        previous = daily.iloc[:-len(latest)].tail(28)

        if not previous.empty:
            current_avg = float(latest.mean())
            previous_avg = float(previous.mean())

            if previous_avg > 0:
                change = (
                    (current_avg - previous_avg)
                    / previous_avg
                ) * 100

                if change > 5:
                    insights.append({
                        "type": "Demand trend",
                        "severity": "Positive",
                        "message": (
                            f"Average daily demand increased "
                            f"by {change:.1f}% compared with "
                            "the preceding period."
                        ),
                    })
                elif change < -5:
                    insights.append({
                        "type": "Demand trend",
                        "severity": "Warning",
                        "message": (
                            f"Average daily demand decreased "
                            f"by {abs(change):.1f}% compared "
                            "with the preceding period."
                        ),
                    })
                else:
                    insights.append({
                        "type": "Demand trend",
                        "severity": "Neutral",
                        "message": (
                            "Average daily demand has remained "
                            "relatively stable."
                        ),
                    })

    # Inventory risk insights are only valid when historical stock is present
    # and complete; demand insights can still be generated without stock data.
    inventory_available = "inventory_level" in data.columns
    inventory_reason = None

    if inventory_available:
        missing_stock = int(data["inventory_level"].isna().sum())
        if missing_stock:
            inventory_available = False
            inventory_reason = (
                f"Inventory Level is missing in {missing_stock} row(s)."
            )
    else:
        inventory_reason = "Inventory Level is not present in the selected dataset."

    if inventory_available:
        try:
            inventory = calculate_inventory_risk(data)
        except ValueError as error:
            inventory = []
            inventory_available = False
            inventory_reason = str(error)
    else:
        inventory = []

    critical = [
        item for item in inventory
        if item["risk_level"] == "Critical"
    ]

    high = [
        item for item in inventory
        if item["risk_level"] == "High"
    ]

    overstock = [
        item for item in inventory
        if item["risk_level"] == "Overstock"
    ]

    if critical:
        insights.append({
            "type": "Stockout warning",
            "severity": "Critical",
            "message": (
                f"{len(critical)} product-store combinations "
                "have less than 7 days of estimated stock coverage."
            ),
        })

    if high:
        insights.append({
            "type": "Inventory warning",
            "severity": "Warning",
            "message": (
                f"{len(high)} product-store combinations "
                "have less than 14 days of estimated stock coverage."
            ),
        })

    if overstock:
        insights.append({
            "type": "Overstock",
            "severity": "Warning",
            "message": (
                f"{len(overstock)} product-store combinations "
                "have more than 60 days of estimated stock coverage."
            ),
        })

    if not inventory_available:
        insights.append({
            "type": "Inventory analysis unavailable",
            "severity": "Information",
            "message": inventory_reason,
        })

    # Demand anomalies.
    anomalies = detect_anomalies(data)

    if anomalies:
        insights.append({
            "type": "Demand anomalies",
            "severity": "Warning",
            "message": (
                f"{len(anomalies)} unusual historical demand "
                "spikes were detected."
            ),
        })

    if not insights:
        insights.append({
            "type": "General",
            "severity": "Neutral",
            "message": (
                "No significant demand or inventory warnings "
                "were identified in the selected historical data."
            ),
        })

    return {
        "summary": (
            f"Analysis completed using {len(data)} historical records."
        ),
        "insights": insights,
        "inventory_available": inventory_available,
        "inventory_unavailable_reason": inventory_reason,
        "inventory_risk_count": len(inventory),
        "anomaly_count": len(anomalies),
    }
