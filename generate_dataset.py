"""
Generates sales_data.csv matching the exact Kaggle schema:
  https://www.kaggle.com/datasets/atomicd/retail-store-inventory-and-demand-forecasting
16 columns, ~76,000 rows.
"""

import pandas as pd
import numpy as np

rng = np.random.default_rng(42)

# ── Config ────────────────────────────────────────────────────────────────────
N_ROWS   = 76000
N_STORES = 10
N_PRODS  = 20

STORE_IDS   = [f"S{str(i).zfill(3)}" for i in range(1, N_STORES + 1)]
PRODUCT_IDS = [f"P{str(i).zfill(3)}" for i in range(1, N_PRODS + 1)]

CATEGORIES = {
    "P001": "Electronics", "P002": "Electronics", "P003": "Electronics",
    "P004": "Electronics", "P005": "Clothing",    "P006": "Clothing",
    "P007": "Clothing",    "P008": "Clothing",    "P009": "Furniture",
    "P010": "Furniture",   "P011": "Furniture",   "P012": "Groceries",
    "P013": "Groceries",   "P014": "Groceries",   "P015": "Groceries",
    "P016": "Toys",        "P017": "Toys",        "P018": "Sports",
    "P019": "Sports",      "P020": "Sports",
}

REGIONS = {
    "S001": "North", "S002": "North", "S003": "South",
    "S004": "South", "S005": "East",  "S006": "East",
    "S007": "West",  "S008": "West",  "S009": "North",
    "S010": "South",
}

BASE_PRICE = {
    "P001": 1200, "P002": 850,  "P003": 450,  "P004": 2300, "P005": 60,
    "P006": 90,   "P007": 45,   "P008": 120,  "P009": 800,  "P010": 1500,
    "P011": 350,  "P012": 15,   "P013": 25,   "P014": 10,   "P015": 40,
    "P016": 70,   "P017": 55,   "P018": 200,  "P019": 130,  "P020": 90,
}

SEASONS = {1:"Winter",2:"Winter",3:"Spring",4:"Spring",5:"Spring",
           6:"Summer",7:"Summer",8:"Summer",9:"Fall",10:"Fall",11:"Fall",12:"Winter"}
WEATHER = ["Sunny", "Cloudy", "Rainy", "Snowy", "Windy"]

# ── Date range ────────────────────────────────────────────────────────────────
dates = pd.date_range("2020-01-01", "2022-12-31", freq="D")
# weight toward Q4 and pandemic months
month_w = {1:1.1,2:0.9,3:1.0,4:0.9,5:1.0,6:1.0,
           7:1.1,8:1.0,9:1.0,10:1.1,11:1.3,12:1.5}
w = np.array([month_w[d.month] for d in dates], dtype=float)
w /= w.sum()
chosen_dates = rng.choice(dates, size=N_ROWS, replace=True, p=w)

# ── Build rows ────────────────────────────────────────────────────────────────
stores   = rng.choice(STORE_IDS,   size=N_ROWS)
products = rng.choice(PRODUCT_IDS, size=N_ROWS)

rows = []
for i in range(N_ROWS):
    d   = pd.Timestamp(chosen_dates[i])
    s   = stores[i]
    p   = products[i]
    cat = CATEGORIES[p]
    reg = REGIONS[s]
    price = BASE_PRICE[p] * rng.uniform(0.9, 1.1)

    # Epidemic: COVID window roughly 2020-03 to 2021-06
    epidemic = 1 if (d.year == 2020 and d.month >= 3) or \
                    (d.year == 2021 and d.month <= 6) else 0

    season    = SEASONS[d.month]
    weather   = rng.choice(WEATHER, p=[0.4, 0.25, 0.2, 0.08, 0.07])
    promotion = int(rng.random() < 0.25)
    discount  = rng.choice([0, 0.05, 0.10, 0.15, 0.20],
                            p=[0.40, 0.20, 0.20, 0.10, 0.10])

    # Units sold — epidemic reduces sales
    base_sold = max(1, int(300 / price * 10))
    if epidemic:
        base_sold = max(1, int(base_sold * 0.6))
    if promotion:
        base_sold = int(base_sold * 1.3)
    if season in ("Winter", "Fall") and cat in ("Electronics", "Toys"):
        base_sold = int(base_sold * 1.2)
    units_sold = max(1, int(rng.poisson(base_sold)))

    # Demand >= units_sold
    demand        = max(units_sold, int(units_sold * rng.uniform(1.0, 1.3)))
    units_ordered = max(demand,     int(demand     * rng.uniform(1.1, 1.5)))
    inv_level     = max(0,          int(units_ordered - units_sold + rng.integers(5, 60)))

    comp_price = round(price * rng.uniform(0.85, 1.15), 2)
    price      = round(price, 2)

    rows.append({
        "Date":               d.strftime("%Y-%m-%d"),
        "Store ID":           s,
        "Product ID":         p,
        "Category":           cat,
        "Region":             reg,
        "Inventory Level":    inv_level,
        "Units Sold":         units_sold,
        "Units Ordered":      units_ordered,
        "Price":              price,
        "Discount":           discount,
        "Weather Condition":  weather,
        "Promotion":          promotion,
        "Competitor Pricing": comp_price,
        "Seasonality":        season,
        "Epidemic":           epidemic,
        "Demand":             demand,
    })

df = pd.DataFrame(rows)
df = df.sort_values("Date").reset_index(drop=True)

out = "data/raw/sales_data.csv"
df.to_csv(out, index=False)
print(f"Saved -> {out}")
print(f"Shape  : {df.shape}")
print(f"Columns: {list(df.columns)}")
print(df.head(3).to_string())
