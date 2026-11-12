# Retail Inventory Dataset - EDA Report

## Dataset Overview
- Original rows: 76,000
- Cleaned rows: 76,000
- Original columns: 16
- Date range: 2022-01-01 to 2024-01-30
- Unique stores: 5
- Unique products: 20

## Data Quality
- Original duplicate rows: 0
- Rows removed: 0

## Demand Analysis
- Forecasting target: Demand
- Total demand: 7,928,104.00
- Average demand: 104.32
- Minimum demand: 4.00
- Maximum demand: 430.00

## Generated Charts
- figures/demand_over_time.png
- figures/demand_distribution.png
- figures/demand_by_category.png
- figures/demand_by_region.png

## Modeling Notes
- Demand is used as the forecasting target.
- Units Sold is retained for comparison.
- Lag features use previous observations only.
- Forecasting should use chronological train/test splits.
- Low sales may reflect stockouts rather than low demand.

## Processed Dataset Columns
- date
- store_id
- product_id
- category
- region
- inventory_level
- units_sold
- units_ordered
- price
- discount
- weather_condition
- promotion
- competitor_pricing
- seasonality
- epidemic
- demand
- target_demand
- year
- month
- day
- day_of_week
- week_of_year
- is_weekend
- demand_lag_1
- demand_lag_7
- demand_rolling_mean_7