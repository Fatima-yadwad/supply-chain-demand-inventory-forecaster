
import pandas as pd


def calculate_inventory_risk(data):
    """
    Estimate inventory risk using the latest historical stock
    and recent average daily demand.

    These are rule-based operational estimates, not a trained
    stockout-classification model.
    """

    required = {
        "date",
        "store_id",
        "product_id",
        "inventory_level",
        "demand",
    }

    missing = required - set(data.columns)

    if missing:
        raise ValueError(
            f"Missing inventory columns: {sorted(missing)}"
        )

    df = data.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    for column in ["inventory_level", "demand"]:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df = df.dropna(
        subset=["date", "inventory_level", "demand"]
    )

    results = []

    for (store, product), group in df.groupby(
        ["store_id", "product_id"]
    ):
        group = group.sort_values("date")

        latest_date = group["date"].max()
        latest_rows = group[group["date"] == latest_date]

        current_stock = float(
            latest_rows["inventory_level"].mean()
        )

        recent = group[
            group["date"] > latest_date - pd.Timedelta(days=28)
        ]

        daily_demand = (
            recent.groupby("date")["demand"].sum()
        )

        average_daily_demand = (
            float(daily_demand.mean())
            if not daily_demand.empty else 0
        )

        if average_daily_demand <= 0:
            coverage_days = None
            risk = "Insufficient demand data"
            reorder_quantity = 0
        else:
            coverage_days = current_stock / average_daily_demand

            if coverage_days < 7:
                risk = "Critical"
            elif coverage_days < 14:
                risk = "High"
            elif coverage_days < 30:
                risk = "Medium"
            elif coverage_days > 60:
                risk = "Overstock"
            else:
                risk = "Low"

            # Illustrative 14-day stock target.
            target_stock = average_daily_demand * 14

            reorder_quantity = max(
                0,
                round(target_stock - current_stock),
            )

        results.append({
            "store_id": str(store),
            "product_id": str(product),
            "latest_inventory_date": latest_date.strftime("%Y-%m-%d"),
            "current_stock_estimate": round(current_stock, 2),
            "average_daily_demand": round(
                average_daily_demand, 2
            ),
            "stock_coverage_days": round(
                coverage_days, 2
            ) if coverage_days is not None else None,
            "risk_level": risk,
            "recommended_reorder_quantity": int(
                reorder_quantity
            ),
        })

    return sorted(
        results,
        key=lambda item: (
            item["stock_coverage_days"]
            if item["stock_coverage_days"] is not None
            else float("inf")
        ),
    )
