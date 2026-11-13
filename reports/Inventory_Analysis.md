# Inventory Optimization and Analytics – Initial Analysis

**Owner:** Bhumika KN (Member 4)  
**Branch:** `bhumikakn`  
**Status:** Initial implementation using illustrative dummy data

> **Important:** The data in this report is synthetic and is used only to demonstrate the modules. Replace it with the team's approved dataset and actual forecasts before presenting project findings. Do not describe these sample results as real business results.

## 1. Objective

The inventory module converts demand information and forecasts into operational recommendations. It calculates safety stock and reorder points, simulates replenishment, estimates stockout and service metrics, detects unusual demand and measures demand-variance amplification across supply-chain stages.

## 2. Module structure

- `src/inventory/safety_stock.py`: safety stock based on demand and optional lead-time variability.
- `src/inventory/reorder_point.py`: reorder point and replenishment recommendations.
- `src/inventory/inventory_simulation.py`: day-by-day stock, receipts, lost sales, order placement and scenario comparison.
- `src/inventory/allocation.py`: optional weighted allocation of constrained stock.
- `src/analytics/spike_detection.py`: prior-window rolling z-score or robust MAD spike detection.
- `src/analytics/bullwhip.py`: variance ratio and stage-wise bullwhip analysis.

## 3. Methods

### Safety stock

For demand variability and fixed lead time:

`Safety Stock = Z × daily-demand standard deviation × sqrt(lead time)`

When lead time also varies, the implementation uses:

`Z × sqrt(L × sigma_demand² + mean_daily_demand² × sigma_lead_time²)`

The service-level Z value is obtained from the standard normal distribution. The normality and independence assumptions should be checked against the project data.

### Reorder point

`Reorder Point = average daily demand × lead time + safety stock`

### Inventory simulation

The simulation receives orders after the specified lead time. It uses a lost-sales assumption: demand that cannot be fulfilled from available stock is recorded as lost sales and is not carried forward as backorders. This assumption must be changed if the project dataset/business scenario requires backorders.

### Service metrics

- Fill rate = fulfilled demand / total demand.
- Stockout-day risk = days with any lost sales / simulated days.
- Cycle service level (estimated) = 1 − stockout-day risk.

These are different service measures; they should not be treated as interchangeable.

### Demand spikes

The detector compares current demand with a rolling baseline computed only from previous observations. It supports z-score and modified z-score (MAD) methods. The first `window` observations are not flagged because there is insufficient history.

### Bullwhip effect

`Bullwhip ratio = variance(upstream orders) / variance(customer demand)`

A ratio above 1 indicates that order variance is greater than customer-demand variance. Valid analysis requires aligned observations from customer demand and one or more upstream order stages. If the denominator variance is zero, the ratio is undefined.

## 4. Input/output contract

The forecast team should provide at minimum:

- `date`: forecast period/date
- `sku`: product identifier
- `forecast_demand`: predicted demand quantity
- optional `lower_bound`, `upper_bound`, `model`

The inventory functions accept demand sequences and numeric inventory parameters. A small adapter should group the forecast DataFrame by SKU and pass each SKU's forecast-demand series into the simulation. Actual historical demand should be used to estimate demand variability when available; forecast values alone should not silently be treated as historical observations.

Bullwhip analysis additionally requires a table containing `period`, `stage`, and `quantity`, with a `customer_demand` stage and upstream order stages.

## 5. Limitations and next steps

1. Dummy data is not a validated business dataset.
2. The simulation currently uses fixed order quantity and lost sales.
3. Supplier capacity, minimum order quantities, order costs, holding costs and multiple suppliers are not yet modeled.
4. Forecast uncertainty intervals are not yet directly converted into a probabilistic stockout model.
5. Bullwhip findings depend on availability and alignment of multi-stage order data.
6. Validate parameter units, missing dates, seasonality, outliers and product-level lead times before final evaluation.

## 6. Validation plan

Run `python -m pytest tests/` from the repository root. Also verify edge cases: zero demand, zero lead time, no stockout, stockout, delayed receipt, constant demand, missing stage data and a zero-variance bullwhip denominator.
