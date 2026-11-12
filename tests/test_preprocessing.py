import pandas as pd

from src.data.preprocessing import prepare_dataset


def sample_data():
    return pd.DataFrame({
        "Date": [
            "2024-01-01",
            "2024-01-02",
            "2024-01-03",
        ],
        "Store ID": ["S001", "S001", "S001"],
        "Product ID": ["P0001", "P0001", "P0001"],
        "Units Sold": [10, 12, 15],
        "Demand": [15, 18, 20],
        "Inventory Level": [100, 90, 80],
    })


def test_demand_is_selected_as_target():
    result = prepare_dataset(sample_data())

    assert result["target_demand"].tolist() == [15, 18, 20]


def test_date_features_are_created():
    result = prepare_dataset(sample_data())

    assert "year" in result.columns
    assert "month" in result.columns
    assert "day_of_week" in result.columns


def test_lag_features_use_previous_values():
    result = prepare_dataset(sample_data())

    assert pd.isna(result.loc[0, "demand_lag_1"])
    assert result.loc[1, "demand_lag_1"] == 15
    assert result.loc[2, "demand_lag_1"] == 18


def test_negative_demand_is_removed():
    df = sample_data()
    df.loc[1, "Demand"] = -5

    result = prepare_dataset(df)

    assert (result["target_demand"] >= 0).all()
    assert len(result) == 2


def test_duplicate_rows_are_removed():
    df = sample_data()
    df = pd.concat([df, df.iloc[[0]]], ignore_index=True)

    result = prepare_dataset(df)

    assert len(result) == 3
