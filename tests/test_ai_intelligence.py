import hashlib
import io

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from src.ai.forecasting_service import forecast_demand
from backend.main import DATA_FILE, app


@pytest.mark.parametrize("horizon", [7, 15, 30])
def test_forecast_separates_historical_actuals_from_predictions(horizon):
    dates = pd.date_range("2024-01-01", periods=28, freq="D")
    data = pd.DataFrame({
        "date": dates,
        "demand": [10 + (index % 7) for index in range(len(dates))],
    })

    result = forecast_demand(data, horizon)

    assert len(result["historical"]) == 28
    assert len(result["forecast"]) == horizon
    assert result["historical"][-1]["date"] == "2024-01-28"
    assert result["forecast"][0]["date"] == "2024-01-29"
    assert "actual_demand" in result["historical"][0]
    assert "predicted_demand" in result["forecast"][0]
    assert result["selected_model"] in result["validation_metrics"]


def test_forecast_rejects_unsupported_horizon():
    data = pd.DataFrame({
        "date": pd.date_range("2024-01-01", periods=14, freq="D"),
        "demand": [10] * 14,
    })

    with pytest.raises(ValueError, match="horizon must be 7, 15 or 30"):
        forecast_demand(data, 10)


def _csv_content(days=35, include_inventory=True):
    rows = []
    for date in pd.date_range("2024-01-01", periods=days, freq="D"):
        row = {
            "Date": date.strftime("%Y-%m-%d"),
            "Store ID": "Store-1",
            "Product ID": "Product-1",
            "Category": "Food",
            "Region": "North",
            "Units Sold": 10 + date.day % 5,
        }
        if include_inventory:
            row["Inventory Level"] = 100
        rows.append(row)
    return pd.DataFrame(rows).to_csv(index=False).encode("utf-8")


def _upload(client, content, filename="session-data.csv"):
    return client.post(
        "/api/datasets/upload",
        files={"file": (filename, content, "text/csv")},
    )


def test_uploaded_dataset_drives_filtered_forecasts_inventory_and_reports():
    client = TestClient(app)
    original_hash = hashlib.sha256(DATA_FILE.read_bytes()).hexdigest()

    upload = _upload(client, _csv_content())
    assert upload.status_code == 201
    metadata = upload.json()
    dataset_id = metadata["dataset_id"]
    assert metadata["forecast_ready"] is True
    assert metadata["inventory_available"] is True

    filters = client.get(
        "/api/filters", params={"dataset_id": dataset_id}
    )
    assert filters.status_code == 200
    assert filters.json()["products"] == ["Product-1"]

    for horizon in [7, 15, 30]:
        response = client.get(
            "/api/ai/forecast",
            params={"dataset_id": dataset_id, "horizon": horizon},
        )
        assert response.status_code == 200
        result = response.json()
        assert len(result["forecast"]) == horizon
        assert result["data_source"] == "Uploaded dataset"
        assert result["selected_model"] in result["validation_metrics"]

    weekly = client.get(
        "/api/ai/reports/weekly",
        params={"dataset_id": dataset_id, "region": "North"},
    )
    assert weekly.status_code == 200
    assert weekly.json()["period"]["complete"] is True
    assert len(weekly.json()["forecast"]["predictions"]) == 7
    assert weekly.json()["inventory_risk"]["available"] is True

    monthly = client.get(
        "/api/ai/reports/monthly",
        params={"dataset_id": dataset_id, "store": "Store-1"},
    )
    assert monthly.status_code == 200
    assert monthly.json()["latest_actual_month"]["complete"] is False
    assert len(monthly.json()["forecast_30_days"]["predictions"]) == 30

    replenishment = client.get(
        "/api/ai/replenishment",
        params={"dataset_id": dataset_id, "product": "Product-1"},
    )
    assert replenishment.status_code == 200
    assert replenishment.json()["forecast_model"]
    assert hashlib.sha256(DATA_FILE.read_bytes()).hexdigest() == original_hash


def test_upload_rejects_invalid_data_and_marks_short_history():
    client = TestClient(app)

    missing_columns = _upload(
        client,
        b"Date,Store ID,Product ID\n2024-01-01,S1,P1\n",
    )
    assert missing_columns.status_code == 422
    assert "Demand (or Units Sold)" in missing_columns.json()["detail"]

    invalid_dates = _upload(
        client,
        b"Date,Store ID,Product ID,Demand\nnot-a-date,S1,P1,5\n",
    )
    assert invalid_dates.status_code == 422
    assert "invalid date" in invalid_dates.json()["detail"]

    negative_demand = _upload(
        client,
        b"Date,Store ID,Product ID,Demand\n2024-01-01,S1,P1,-1\n",
    )
    assert negative_demand.status_code == 422
    assert "negative demand" in negative_demand.json()["detail"]

    short_upload = _upload(client, _csv_content(days=7))
    assert short_upload.status_code == 201
    metadata = short_upload.json()
    assert metadata["forecast_ready"] is False
    forecast = client.get(
        "/api/ai/forecast",
        params={"dataset_id": metadata["dataset_id"], "horizon": 7},
    )
    assert forecast.status_code == 400
    assert "14 distinct historical dates" in forecast.json()["detail"]

    invalid_numeric = _upload(
        client,
        b"Date,Store ID,Product ID,Demand\n2024-01-01,S1,P1,not-a-number\n",
    )
    assert invalid_numeric.status_code == 422
    assert "invalid numeric" in invalid_numeric.json()["detail"]


def test_upload_removes_exact_duplicates_and_applies_all_filter_dimensions():
    client = TestClient(app)
    rows = []
    for date in pd.date_range("2024-01-01", periods=21, freq="D"):
        rows.extend([
            {
                "Date": date.strftime("%Y-%m-%d"),
                "Store ID": "Store-1",
                "Product ID": "Product-1",
                "Category": "Food",
                "Region": "North",
                "Demand": 5,
            },
            {
                "Date": date.strftime("%Y-%m-%d"),
                "Store ID": "Store-2",
                "Product ID": "Product-2",
                "Category": "Home",
                "Region": "South",
                "Demand": 20,
            },
        ])
    data = pd.DataFrame(rows)
    data = pd.concat([data, data.iloc[[0]]], ignore_index=True)
    content = data.to_csv(index=False).encode("utf-8")

    upload = _upload(client, content)
    assert upload.status_code == 201
    metadata = upload.json()
    assert metadata["duplicate_rows_removed"] == 1
    assert metadata["records"] == 42

    response = client.get(
        "/api/demand",
        params={
            "dataset_id": metadata["dataset_id"],
            "product": "Product-1",
            "category": "Food",
            "store": "Store-1",
            "region": "North",
        },
    )
    assert response.status_code == 200
    assert len(response.json()) == 21
    assert all(item["demand"] == 5 for item in response.json())

    no_match = client.get(
        "/api/overview",
        params={
            "dataset_id": metadata["dataset_id"],
            "product": "Product-1",
            "category": "Home",
            "store": "Store-1",
            "region": "North",
        },
    )
    assert no_match.status_code == 200
    assert no_match.json()["total_records"] == 0


def test_inventory_absence_is_reported_without_blocking_demand_insights():
    client = TestClient(app)
    upload = _upload(
        client, _csv_content(days=21, include_inventory=False)
    )
    assert upload.status_code == 201
    dataset_id = upload.json()["dataset_id"]

    overview = client.get(
        "/api/overview", params={"dataset_id": dataset_id}
    )
    assert overview.status_code == 200
    assert overview.json()["average_inventory"] is None
    assert overview.json()["inventory_available"] is False

    insights = client.get(
        "/api/ai/insights", params={"dataset_id": dataset_id}
    )
    assert insights.status_code == 200
    assert insights.json()["inventory_available"] is False
    assert any(
        item["type"] == "Inventory analysis unavailable"
        for item in insights.json()["insights"]
    )

    risk = client.get(
        "/api/ai/inventory-risk", params={"dataset_id": dataset_id}
    )
    assert risk.status_code == 422
    assert "Inventory Level" in risk.json()["detail"]


def test_missing_inventory_values_disable_inventory_recommendations():
    client = TestClient(app)
    data = pd.read_csv(io.BytesIO(_csv_content(days=21)))
    data.loc[0, "Inventory Level"] = None
    upload = _upload(
        client, data.to_csv(index=False).encode("utf-8")
    )
    assert upload.status_code == 201
    metadata = upload.json()
    assert metadata["inventory_available"] is False
    assert "missing in 1 row" in metadata["inventory_issue"]

    replenishment = client.get(
        "/api/ai/replenishment",
        params={"dataset_id": metadata["dataset_id"]},
    )
    assert replenishment.status_code == 422
    assert "missing or invalid" in replenishment.json()["detail"]
