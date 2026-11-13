import pandas as pd

COLUMN_ALIASES = {
    "date": "date",
    "store id": "store_id",
    "product id": "product_id",
    "category": "category",
    "region": "region",
    "inventory level": "inventory_level",
    "units sold": "units_sold",
    "units ordered": "units_ordered",
    "price": "price",
    "discount": "discount",
    "weather condition": "weather_condition",
    "promotion": "promotion",
    "competitor pricing": "competitor_pricing",
    "seasonality": "seasonality",
    "epidemic": "epidemic",
    "demand": "demand",
}

NUMERIC_COLUMNS = [
    "inventory_level",
    "units_sold",
    "units_ordered",
    "price",
    "discount",
    "promotion",
    "competitor_pricing",
    "epidemic",
    "demand",
]


def standardize_columns(df):
    """Standardize the original Kaggle dataset column names."""
    df = df.copy()

    renamed = {}
    for col in df.columns:
        key = str(col).strip().lower()
        renamed[col] = COLUMN_ALIASES.get(
            key, key.replace(" ", "_").replace("/", "_")
        )

    df = df.rename(columns=renamed)

    if df.columns.duplicated().any():
        raise ValueError("Duplicate columns found after standardization.")

    return df


def clean_dataset(df):
    """Clean the Kaggle retail inventory dataset."""
    df = standardize_columns(df)

    required = ["date", "store_id", "product_id"]

    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    if "demand" in df.columns:
        df["target_demand"] = pd.to_numeric(
            df["demand"], errors="coerce"
        )
        print("Forecast target selected: Demand")
    elif "units_sold" in df.columns:
        df["target_demand"] = pd.to_numeric(
            df["units_sold"], errors="coerce"
        )
        print("Forecast target selected: Units Sold")
    else:
        raise ValueError("Neither Demand nor Units Sold is available.")

    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["date", "target_demand"])
    df = df[df["target_demand"] >= 0]
    df = df.drop_duplicates()

    df = df.sort_values(
        ["store_id", "product_id", "date"]
    ).reset_index(drop=True)

    return df


def add_date_features(df):
    """Extract calendar features."""
    df = df.copy()

    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["day"] = df["date"].dt.day
    df["day_of_week"] = df["date"].dt.day_of_week
    df["week_of_year"] = df["date"].dt.isocalendar().week.astype(int)
    df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)

    return df


def add_demand_lags(df):
    """Create historical demand features without future leakage."""
    df = df.copy()
    keys = ["store_id", "product_id"]

    df = df.sort_values(keys + ["date"]).copy()

    grouped = df.groupby(keys)["target_demand"]

    df["demand_lag_1"] = grouped.shift(1)
    df["demand_lag_7"] = grouped.shift(7)

    df["demand_rolling_mean_7"] = (
        df.groupby(keys)["target_demand"]
        .transform(
            lambda s: s.shift(1).rolling(7, min_periods=1).mean()
        )
    )

    return df.reset_index(drop=True)


def prepare_dataset(df):
    """Run the complete preprocessing pipeline."""
    df = clean_dataset(df)
    df = add_date_features(df)
    df = add_demand_lags(df)

    return df

