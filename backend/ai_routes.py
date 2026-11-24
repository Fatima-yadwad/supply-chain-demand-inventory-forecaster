
from collections import OrderedDict
from copy import deepcopy
from threading import Lock

import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from src.ai.forecasting_service import forecast_demand
from src.ai.inventory_service import calculate_inventory_risk
from src.ai.insights_service import (
    detect_anomalies,
    generate_insights,
)


def create_ai_router(get_filtered_data):
    router = APIRouter(prefix="/api/ai", tags=["AI Intelligence"])
    forecast_cache = OrderedDict()
    forecast_cache_locks = {}
    cache_lock = Lock()
    cache_limit = 64

    def load_selected_data(
        product,
        category,
        store,
        region,
        dataset_id=None,
        selected_product="All",
        selected_store="All",
    ):
        df = get_filtered_data(
            product=product,
            category=category,
            store=store,
            region=region,
            dataset_id=dataset_id,
        )

        if selected_product != "All":
            df = df[
                df["product_id"].astype(str) == selected_product
            ]

        if selected_store != "All":
            df = df[
                df["store_id"].astype(str) == selected_store
            ]

        return df

    def run_forecast(data, dataset_id, filters, horizon):
        source_version = data.attrs.get(
            "dataset_version", dataset_id or "historical"
        )
        cache_filters = tuple(sorted(
            (key, value)
            for key, value in filters.items()
            if value != "All"
        ))
        key = (
            source_version,
            cache_filters,
        )

        def result_for_horizon(result):
            formatted = deepcopy(result)
            predictions = formatted["forecast"][:horizon]
            formatted["forecast"] = predictions
            formatted["forecast_horizon"] = horizon
            formatted["total_predicted_demand"] = round(
                sum(item["predicted_demand"] for item in predictions), 2
            )
            formatted["average_daily_forecast"] = round(
                formatted["total_predicted_demand"] / horizon, 2
            )
            return formatted

        with cache_lock:
            cached = forecast_cache.get(key)
            if cached is not None:
                forecast_cache.move_to_end(key)
                return result_for_horizon(cached)
            forecast_lock = forecast_cache_locks.setdefault(key, Lock())

        with forecast_lock:
            try:
                with cache_lock:
                    cached = forecast_cache.get(key)
                    if cached is not None:
                        forecast_cache.move_to_end(key)
                        return result_for_horizon(cached)

                result = forecast_demand(data, 30)
                with cache_lock:
                    forecast_cache[key] = result
                    forecast_cache.move_to_end(key)
                    while len(forecast_cache) > cache_limit:
                        forecast_cache.popitem(last=False)
                return result_for_horizon(result)
            finally:
                with cache_lock:
                    forecast_cache_locks.pop(key, None)

    def require_inventory_data(data):
        required = ["date", "store_id", "product_id", "demand", "inventory_level"]
        missing = [column for column in required if column not in data]
        if missing:
            column_labels = {
                "date": "Date",
                "store_id": "Store ID",
                "product_id": "Product ID",
                "inventory_level": "Inventory Level",
                "demand": "Demand",
            }
            raise HTTPException(
                status_code=422,
                detail=(
                    "Inventory risk and replenishment are unavailable; "
                    "the selected dataset is missing: "
                    + ", ".join(
                        column_labels.get(column, column)
                        for column in missing
                    )
                    + "."
                ),
            )

        stock = pd.to_numeric(data["inventory_level"], errors="coerce")
        missing_stock = int(stock.isna().sum())
        if missing_stock:
            raise HTTPException(
                status_code=422,
                detail=(
                    "Inventory risk and replenishment are unavailable; "
                    f"Inventory Level is missing or invalid in {missing_stock} row(s)."
                ),
            )
        if (stock < 0).any():
            raise HTTPException(
                status_code=422,
                detail="Inventory risk and replenishment are unavailable; Inventory Level contains negative values.",
            )

    def inventory_summary(data):
        try:
            require_inventory_data(data)
            risks = calculate_inventory_risk(data)
        except HTTPException as error:
            return {
                "available": False,
                "reason": error.detail,
                "risk_counts": {},
                "stockout_warnings": [],
                "results": [],
            }
        except ValueError as error:
            return {
                "available": False,
                "reason": str(error),
                "risk_counts": {},
                "stockout_warnings": [],
                "results": [],
            }

        risk_levels = ["Critical", "High", "Medium", "Low", "Overstock"]
        risk_counts = {
            level: sum(item["risk_level"] == level for item in risks)
            for level in risk_levels
        }
        warnings = [
            item for item in risks
            if item["risk_level"] in {"Critical", "High"}
        ]
        return {
            "available": True,
            "reason": None,
            "risk_counts": risk_counts,
            "stockout_warnings": warnings,
            "results": risks,
        }

    def replenishment_results(data, dataset_id, filters):
        require_inventory_data(data)
        risks = calculate_inventory_risk(data)
        forecast = run_forecast(data, dataset_id, filters, 15)

        latest_date = pd.to_datetime(data["date"]).max().normalize()
        recent_dates = pd.date_range(
            end=latest_date, periods=28, freq="D"
        )
        recent_data = data.copy()
        recent_data["date"] = pd.to_datetime(
            recent_data["date"]
        ).dt.normalize()
        recent_daily = (
            recent_data.groupby("date")["demand"]
            .sum()
            .reindex(recent_dates, fill_value=0)
        )
        recent_average = float(recent_daily.mean())
        projected_average = float(
            sum(row["predicted_demand"] for row in forecast["forecast"][:14])
            / 14
        )
        demand_scale = (
            projected_average / recent_average
            if recent_average > 0 else 0
        )

        recommendations = []
        for item in risks:
            future_daily_demand = (
                item["average_daily_demand"] * demand_scale
            )
            projected_demand = future_daily_demand * 14
            reorder_quantity = max(
                0,
                round(projected_demand - item["current_stock_estimate"]),
            )
            if reorder_quantity:
                recommendations.append({
                    **item,
                    "historical_reorder_quantity":
                        item["recommended_reorder_quantity"],
                    "forecast_average_daily_demand": round(
                        future_daily_demand, 2
                    ),
                    "projected_demand_14_days": round(
                        projected_demand, 2
                    ),
                    "recommended_reorder_quantity": int(reorder_quantity),
                    "replenishment_basis": (
                        "14-day forecast from the selected model, allocated "
                        "by each store-product's recent demand share"
                    ),
                })

        return recommendations, forecast

    def group_demand(data, dimension):
        if dimension not in data or data.empty:
            return []
        grouped = (
            data.groupby(dimension)["demand"]
            .sum()
            .sort_values(ascending=False)
        )
        return [
            {"name": str(name), "demand": round(float(value), 2)}
            for name, value in grouped.items()
        ]

    def period_complete(data, start, end):
        observed = set(pd.to_datetime(data["date"]).dt.normalize())
        expected = pd.date_range(start=start, end=end, freq="D")
        return all(date in observed for date in expected)

    def report_inventory_and_replenishment(data, dataset_id, filters):
        inventory = inventory_summary(data)
        try:
            recommendations, forecast = replenishment_results(
                data, dataset_id, filters
            )
            replenishment = {
                "available": True,
                "reason": None,
                "recommendations": recommendations,
                "forecast_model": forecast["selected_model"],
            }
        except (HTTPException, ValueError) as error:
            replenishment = {
                "available": False,
                "reason": (
                    error.detail
                    if isinstance(error, HTTPException)
                    else str(error)
                ),
                "recommendations": [],
                "forecast_model": None,
            }
        return inventory, replenishment
    @router.get("/forecast")
    def ai_forecast(
        horizon: int = Query(7, ge=7, le=30),
        product: str = Query("All"),
        category: str = Query("All"),
        store: str = Query("All"),
        region: str = Query("All"),
        dataset_id: str | None = Query(None),
        selected_product: str = Query("All"),
        selected_store: str = Query("All"),
    ):
        if horizon not in [7, 15, 30]:
            raise HTTPException(
                status_code=400,
                detail="Horizon must be 7, 15 or 30 days.",
            )

        df = load_selected_data(
            product=product,
            category=category,
            store=store,
            region=region,
            dataset_id=dataset_id,
            selected_product=selected_product,
            selected_store=selected_store,
        )

        if df.empty:
            raise HTTPException(
                status_code=404,
                detail="No historical data found for these selections.",
            )

        try:
            result = run_forecast(
                df,
                dataset_id,
                {
                    "product": product,
                    "category": category,
                    "store": store,
                    "region": region,
                    "selected_product": selected_product,
                    "selected_store": selected_store,
                },
                horizon,
            )
            result["dataset_id"] = dataset_id
            result["data_source"] = (
                "Uploaded dataset" if dataset_id else "Historical dataset"
            )
            return result
        except ValueError as error:
            raise HTTPException(400, str(error))
        except Exception as error:
            raise HTTPException(
                500,
                f"Forecast generation failed: {str(error)}",
            )

    @router.get("/model-performance")
    def model_performance(
        product: str = Query("All"),
        category: str = Query("All"),
        store: str = Query("All"),
        region: str = Query("All"),
        dataset_id: str | None = Query(None),
        selected_product: str = Query("All"),
        selected_store: str = Query("All"),
    ):
        df = load_selected_data(
            product=product,
            category=category,
            store=store,
            region=region,
            dataset_id=dataset_id,
            selected_product=selected_product,
            selected_store=selected_store,
        )

        if df.empty:
            raise HTTPException(404, "No historical data found.")

        try:
            result = run_forecast(
                df,
                dataset_id,
                {
                    "product": product,
                    "category": category,
                    "store": store,
                    "region": region,
                    "selected_product": selected_product,
                    "selected_store": selected_store,
                },
                7,
            )

            return {
                "dataset_id": dataset_id,
                "selected_model": result["selected_model"],
                "validation_metrics": result["validation_metrics"],
                "selected_metrics": result["validation_metrics"][
                    result["selected_model"]
                ],
                "model_errors": result.get("model_errors", {}),
                "historical_days": result["historical_days"],
                "evaluation_method": (
                    "Chronological holdout validation"
                ),
            }
        except ValueError as error:
            raise HTTPException(400, str(error))
        except Exception as error:
            raise HTTPException(
                500,
                f"Model performance evaluation failed: {str(error)}",
            )

    @router.get("/inventory-risk")
    def ai_inventory_risk(
        product: str = Query("All"),
        category: str = Query("All"),
        store: str = Query("All"),
        region: str = Query("All"),
        dataset_id: str | None = Query(None),
    ):
        df = get_filtered_data(
            product, category, store, region, dataset_id
        )

        if df.empty:
            return {"count": 0, "results": []}

        try:
            require_inventory_data(df)
            results = calculate_inventory_risk(df)
            return {
                "count": len(results),
                "results": results,
                "method": "Historical stock coverage rules",
            }
        except ValueError as error:
            raise HTTPException(400, str(error))

    @router.get("/replenishment")
    def ai_replenishment(
        product: str = Query("All"),
        category: str = Query("All"),
        store: str = Query("All"),
        region: str = Query("All"),
        dataset_id: str | None = Query(None),
    ):
        filters = {
            "product": product,
            "category": category,
            "store": store,
            "region": region,
        }
        df = get_filtered_data(
            product, category, store, region, dataset_id
        )

        if df.empty:
            return {"count": 0, "recommendations": []}

        try:
            recommendations, forecast = replenishment_results(
                df, dataset_id, filters
            )

            return {
                "dataset_id": dataset_id,
                "count": len(recommendations),
                "recommendations": recommendations,
                "forecast_model": forecast["selected_model"],
                "method": (
                    "14-day forecast from the selected model, allocated "
                    "by each store-product's recent demand share"
                ),
            }
        except ValueError as error:
            raise HTTPException(400, str(error))

    @router.get("/anomalies")
    def ai_anomalies(
        product: str = Query("All"),
        category: str = Query("All"),
        store: str = Query("All"),
        region: str = Query("All"),
        dataset_id: str | None = Query(None),
    ):
        df = get_filtered_data(
            product, category, store, region, dataset_id
        )

        if df.empty:
            return {"count": 0, "anomalies": []}

        try:
            results = detect_anomalies(df)
            return {
                "count": len(results),
                "anomalies": results,
            }
        except ValueError as error:
            raise HTTPException(400, str(error))

    @router.get("/insights")
    def ai_insights(
        product: str = Query("All"),
        category: str = Query("All"),
        store: str = Query("All"),
        region: str = Query("All"),
        dataset_id: str | None = Query(None),
    ):
        df = get_filtered_data(
            product, category, store, region, dataset_id
        )

        try:
            return generate_insights(df)
        except ValueError as error:
            raise HTTPException(400, str(error))

    @router.get("/reports/weekly")
    def weekly_report(
        product: str = Query("All"),
        category: str = Query("All"),
        store: str = Query("All"),
        region: str = Query("All"),
        dataset_id: str | None = Query(None),
    ):
        data = get_filtered_data(
            product, category, store, region, dataset_id
        )
        if data.empty:
            raise HTTPException(
                status_code=404,
                detail="No historical data found for these selections.",
            )

        data = data.copy()
        data["date"] = pd.to_datetime(data["date"]).dt.normalize()
        last_date = data["date"].max()
        start_date = last_date - pd.Timedelta(days=6)
        actual_dates = pd.date_range(
            start=start_date, end=last_date, freq="D"
        )
        daily = (
            data.groupby("date")["demand"]
            .sum()
            .sort_index()
        )
        actual_week = daily.reindex(actual_dates, fill_value=0)
        previous_dates = pd.date_range(
            start=start_date - pd.Timedelta(days=7),
            end=start_date - pd.Timedelta(days=1),
            freq="D",
        )
        previous_week = daily.reindex(previous_dates, fill_value=0)
        previous_total = float(previous_week.sum())
        actual_total = float(actual_week.sum())
        trend_change = (
            round((actual_total - previous_total) / previous_total * 100, 2)
            if previous_total > 0 else None
        )
        week_data = data[
            data["date"].between(start_date, last_date)
        ]
        filters = {
            "product": product,
            "category": category,
            "store": store,
            "region": region,
        }

        try:
            forecast = run_forecast(data, dataset_id, filters, 7)
            forecast_result = {
                "available": True,
                "reason": None,
                "selected_model": forecast["selected_model"],
                "validation_metrics": forecast["validation_metrics"],
                "predictions": forecast["forecast"],
            }
        except ValueError as error:
            forecast_result = {
                "available": False,
                "reason": str(error),
                "selected_model": None,
                "validation_metrics": {},
                "predictions": [],
            }

        inventory, replenishment = report_inventory_and_replenishment(
            data, dataset_id, filters
        )
        product_demand = group_demand(week_data, "product_id")
        insights = generate_insights(data)

        return {
            "dataset_id": dataset_id,
            "period": {
                "start": start_date.strftime("%Y-%m-%d"),
                "end": last_date.strftime("%Y-%m-%d"),
                "complete": period_complete(
                    data, start_date, last_date
                ),
                "actual_demand_total": round(actual_total, 2),
                "actual_demand_daily": [
                    {
                        "date": date.strftime("%Y-%m-%d"),
                        "demand": round(float(value), 2),
                    }
                    for date, value in actual_week.items()
                ],
            },
            "trend": {
                "previous_period_demand": round(previous_total, 2),
                "change_percent": trend_change,
                "comparison_available": bool(previous_total > 0),
            },
            "forecast": forecast_result,
            "highest_demand_products": product_demand[:5],
            "lowest_demand_products": list(reversed(product_demand[-5:])),
            "store_performance": group_demand(week_data, "store_id"),
            "regional_performance": group_demand(week_data, "region"),
            "inventory_risk": {
                "available": inventory["available"],
                "reason": inventory["reason"],
                "risk_counts": inventory["risk_counts"],
                "stockout_warnings": inventory["stockout_warnings"],
            },
            "replenishment": replenishment,
            "insights": insights["insights"],
        }

    @router.get("/reports/monthly")
    def monthly_report(
        product: str = Query("All"),
        category: str = Query("All"),
        store: str = Query("All"),
        region: str = Query("All"),
        dataset_id: str | None = Query(None),
    ):
        data = get_filtered_data(
            product, category, store, region, dataset_id
        )
        if data.empty:
            raise HTTPException(
                status_code=404,
                detail="No historical data found for these selections.",
            )

        data = data.copy()
        data["date"] = pd.to_datetime(data["date"]).dt.normalize()
        data["month"] = data["date"].dt.to_period("M")
        monthly = (
            data.groupby("month")["demand"]
            .sum()
            .sort_index()
        )
        month_summaries = []
        complete_by_month = {}
        for month, total in monthly.items():
            start_date = month.start_time.normalize()
            end_date = month.end_time.normalize()
            complete = period_complete(data, start_date, end_date)
            complete_by_month[month] = complete
            observed_days = int(
                data.loc[data["month"] == month, "date"].nunique()
            )
            month_summaries.append({
                "month": str(month),
                "actual_demand": round(float(total), 2),
                "days_observed": observed_days,
                "days_in_month": int(end_date.day),
                "complete": complete,
            })

        comparisons = []
        months = list(monthly.index)
        for index in range(1, len(months)):
            previous_month = months[index - 1]
            current_month = months[index]
            previous_total = float(monthly.loc[previous_month])
            if (
                previous_month + 1 == current_month
                and complete_by_month[previous_month]
                and complete_by_month[current_month]
                and previous_total > 0
            ):
                current_total = float(monthly.loc[current_month])
                comparisons.append({
                    "month": str(current_month),
                    "previous_month": str(previous_month),
                    "change_percent": round(
                        (current_total - previous_total)
                        / previous_total * 100,
                        2,
                    ),
                })

        latest_month = months[-1]
        latest_month_data = data[data["month"] == latest_month]
        filters = {
            "product": product,
            "category": category,
            "store": store,
            "region": region,
        }
        try:
            forecast = run_forecast(data, dataset_id, filters, 30)
            forecast_result = {
                "available": True,
                "reason": None,
                "selected_model": forecast["selected_model"],
                "validation_metrics": forecast["validation_metrics"],
                "predictions": forecast["forecast"],
            }
        except ValueError as error:
            forecast_result = {
                "available": False,
                "reason": str(error),
                "selected_model": None,
                "validation_metrics": {},
                "predictions": [],
            }

        inventory, replenishment = report_inventory_and_replenishment(
            data, dataset_id, filters
        )
        insights = generate_insights(data)

        return {
            "dataset_id": dataset_id,
            "monthly_summary": month_summaries,
            "month_over_month_comparison": comparisons,
            "latest_actual_month": {
                "month": str(latest_month),
                "complete": complete_by_month[latest_month],
                "actual_demand": round(
                    float(monthly.loc[latest_month]), 2
                ),
            },
            "product_performance": group_demand(
                latest_month_data, "product_id"
            ),
            "category_performance": group_demand(
                latest_month_data, "category"
            ),
            "store_performance": group_demand(
                latest_month_data, "store_id"
            ),
            "regional_performance": group_demand(
                latest_month_data, "region"
            ),
            "inventory_risk": {
                "available": inventory["available"],
                "reason": inventory["reason"],
                "risk_counts": inventory["risk_counts"],
                "stockout_warnings": inventory["stockout_warnings"],
            },
            "replenishment": replenishment,
            "forecast_30_days": forecast_result,
            "insights": insights["insights"],
        }

    return router
