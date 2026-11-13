
import pandas as pd
import streamlit as st
from pathlib import Path

DATA_PATH = (
    Path(__file__).resolve().parent.parent
    / "data" / "raw" / "sales_data.csv"
)


@st.cache_data(show_spinner="Loading dataset...")
def load_data():

    if not DATA_PATH.exists():
        st.error(f"Dataset not found: {DATA_PATH}")
        st.stop()

    df = pd.read_csv(DATA_PATH)

    # Standardize column names
    column_mapping = {
        "Store ID": "Store",
        "Product ID": "Product",
        "Units Sold": "Units_Sold",
        "Units Ordered": "Units_Ordered",
        "Inventory Level": "Inventory_Level",
        "Weather Condition": "Weather_Condition",
        "Competitor Pricing": "Competitor_Pricing",
        "Discount": "Discount_Pct",
    }

    df = df.rename(columns=column_mapping)

    # Check required columns
    required_columns = [
        "Date", "Store", "Product", "Category",
        "Region", "Units_Sold", "Units_Ordered",
        "Inventory_Level", "Price", "Demand"
    ]

    missing = [col for col in required_columns if col not in df.columns]

    if missing:
        st.error(f"Missing required columns: {missing}")
        st.stop()

    # Convert date
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"])

    # Convert numeric columns
    numeric_columns = [
        "Units_Sold",
        "Units_Ordered",
        "Inventory_Level",
        "Price",
        "Discount_Pct",
        "Competitor_Pricing",
        "Demand",
        "Promotion",
        "Epidemic"
    ]

    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Remove duplicate records
    df = df.drop_duplicates()

    # Remove rows with missing essential values
    df = df.dropna(
        subset=[
            "Units_Sold",
            "Units_Ordered",
            "Inventory_Level",
            "Price",
            "Demand"
        ]
    )

    # Calculate estimated gross revenue before discounts
    df["Revenue"] = df["Units_Sold"] * df["Price"]

    # Clean text columns
    text_columns = ["Store", "Product", "Category", "Region"]

    for col in text_columns:
        df[col] = df[col].astype("string").str.strip()

    # Date helper columns
    df["Year"] = df["Date"].dt.year
    df["Month"] = df["Date"].dt.month
    df["Month_Name"] = df["Date"].dt.strftime("%b %Y")
    df["Week"] = df["Date"].dt.to_period("W").apply(
        lambda period: period.start_time
    )
    df["Day_Name"] = df["Date"].dt.day_name()

    df = df.sort_values("Date").reset_index(drop=True)

    return df


def apply_filters(df, filters):

    start, end = filters.get(
        "date_range",
        (df["Date"].min().date(), df["Date"].max().date())
    )

    mask = (
        (df["Date"] >= pd.Timestamp(start))
        & (df["Date"] < pd.Timestamp(end) + pd.Timedelta(days=1))
    )

    df = df.loc[mask]

    filter_columns = {
        "stores": "Store",
        "regions": "Region",
        "categories": "Category",
        "products": "Product",
    }

    for filter_key, column in filter_columns.items():
        selected = filters.get(filter_key, [])

        if selected:
            df = df[df[column].isin(selected)]

    return df.reset_index(drop=True)
