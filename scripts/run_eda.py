from pathlib import Path
import sys

# Make the project root available for imports.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.data.data_loader import load_dataset, inspect_dataset
from src.data.preprocessing import prepare_dataset

PROCESSED_PATH = ROOT / "data" / "processed" / "cleaned_inventory.csv"
REPORT_PATH = ROOT / "reports" / "EDA_Report.md"
FIGURE_DIR = ROOT / "reports" / "figures"


def create_visualizations(df):
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Daily demand trend
    daily = df.groupby("date")["target_demand"].sum().sort_index()

    plt.figure(figsize=(12, 5))
    plt.plot(daily.index, daily.values)
    plt.title("Daily Retail Demand")
    plt.xlabel("Date")
    plt.ylabel("Demand")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(FIGURE_DIR / "demand_over_time.png")
    plt.close()

    # 2. Demand distribution
    plt.figure(figsize=(10, 5))
    plt.hist(df["target_demand"], bins=40, edgecolor="black")
    plt.title("Demand Distribution")
    plt.xlabel("Demand")
    plt.ylabel("Frequency")
    plt.tight_layout()
    plt.savefig(FIGURE_DIR / "demand_distribution.png")
    plt.close()

    # 3. Category demand
    if "category" in df.columns:
        category = df.groupby("category")["target_demand"].sum()
        category = category.sort_values(ascending=False)

        plt.figure(figsize=(10, 5))
        category.plot(kind="bar")
        plt.title("Demand by Product Category")
        plt.xlabel("Category")
        plt.ylabel("Demand")
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        plt.savefig(FIGURE_DIR / "demand_by_category.png")
        plt.close()

    # 4. Regional demand
    if "region" in df.columns:
        region = df.groupby("region")["target_demand"].sum()
        region = region.sort_values(ascending=False)

        plt.figure(figsize=(9, 5))
        region.plot(kind="bar")
        plt.title("Demand by Region")
        plt.xlabel("Region")
        plt.ylabel("Demand")
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        plt.savefig(FIGURE_DIR / "demand_by_region.png")
        plt.close()


def create_report(raw_df, clean_df):
    report = [
        "# Retail Inventory Dataset - EDA Report",
        "",
        "## Dataset Overview",
        f"- Original rows: {len(raw_df):,}",
        f"- Cleaned rows: {len(clean_df):,}",
        f"- Original columns: {len(raw_df.columns)}",
        f"- Date range: {clean_df['date'].min().date()} to {clean_df['date'].max().date()}",
        f"- Unique stores: {clean_df['store_id'].nunique()}",
        f"- Unique products: {clean_df['product_id'].nunique()}",
        "",
        "## Data Quality",
        f"- Original duplicate rows: {raw_df.duplicated().sum():,}",
        f"- Rows removed: {len(raw_df) - len(clean_df):,}",
        "",
        "## Demand Analysis",
        "- Forecasting target: Demand",
        f"- Total demand: {clean_df['target_demand'].sum():,.2f}",
        f"- Average demand: {clean_df['target_demand'].mean():,.2f}",
        f"- Minimum demand: {clean_df['target_demand'].min():,.2f}",
        f"- Maximum demand: {clean_df['target_demand'].max():,.2f}",
        "",
        "## Generated Charts",
        "- figures/demand_over_time.png",
        "- figures/demand_distribution.png",
        "- figures/demand_by_category.png",
        "- figures/demand_by_region.png",
        "",
        "## Modeling Notes",
        "- Demand is used as the forecasting target.",
        "- Units Sold is retained for comparison.",
        "- Lag features use previous observations only.",
        "- Forecasting should use chronological train/test splits.",
        "- Low sales may reflect stockouts rather than low demand.",
        "",
        "## Processed Dataset Columns",
    ]

    report.extend(f"- {col}" for col in clean_df.columns)

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(report), encoding="utf-8")


def main():
    print("\n========== FATIMA DATA PIPELINE ==========", flush=True)

    raw_df = load_dataset()

    print("\nInspecting original dataset...", flush=True)
    inspect_dataset(raw_df)

    print("\nCleaning and preprocessing...", flush=True)
    clean_df = prepare_dataset(raw_df)

    PROCESSED_PATH.parent.mkdir(parents=True, exist_ok=True)
    clean_df.to_csv(PROCESSED_PATH, index=False)

    print(f"\nCleaned dataset saved: {PROCESSED_PATH}", flush=True)

    print("\nGenerating visualizations...", flush=True)
    create_visualizations(clean_df)

    print("\nGenerating EDA report...", flush=True)
    create_report(raw_df, clean_df)

    print("\n========== PIPELINE COMPLETED ==========")
    print(f"Processed dataset: {PROCESSED_PATH}")
    print(f"EDA report: {REPORT_PATH}")
    print(f"Charts: {FIGURE_DIR}")


if __name__ == "__main__":
    main()
