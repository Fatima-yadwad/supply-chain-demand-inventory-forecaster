# Supply Chain Demand & Inventory Forecaster

## 1. Project Overview

The **Supply Chain Demand & Inventory Forecaster** is a data-driven project designed to analyse historical retail demand, forecast future product demand, and support better inventory management decisions.

The project aims to help businesses reduce stockouts and overstocking by combining demand forecasting with inventory analytics.

## 2. Project Objectives

- Analyse historical sales, demand, and inventory data.
- Identify demand patterns, trends, and seasonality.
- Forecast future product demand using time-series forecasting models.
- Calculate inventory metrics such as safety stock and reorder points.
- Detect unusual demand spikes and fluctuations.
- Present insights through an interactive dashboard.

## 3. Dataset

The project uses the **Retail Store Inventory and Demand Forecasting** dataset from Kaggle.

Dataset: https://www.kaggle.com/datasets/atomicd/retail-store-inventory-and-demand-forecasting

The dataset contains 76,000 records and 16 columns, including:

- Date
- Store ID and Product ID
- Category and Region
- Inventory Level
- Units Sold and Units Ordered
- Price and Discount
- Weather Condition and Promotion
- Competitor Pricing
- Seasonality and Epidemic
- Demand

**Target variable:** `Demand`

The original dataset is stored locally in `data/raw/` and is not included in Git commits.

## 4. Project Modules

1. **Data Loading and Preprocessing:** Load, inspect, clean, and transform the dataset.
2. **Exploratory Data Analysis:** Understand demand distributions, trends, and patterns.
3. **Demand Forecasting:** Develop and evaluate SARIMAX and Prophet forecasting models.
4. **Inventory Analytics:** Calculate safety stock, reorder points, and identify demand spikes.
5. **Dashboard and Integration:** Combine project outputs into an interactive Streamlit application.

## 5. Technology Stack

- Python
- Pandas and NumPy
- Matplotlib
- SARIMAX
- Prophet
- Scikit-learn
- Streamlit
- Git and GitHub

## 6. Repository Structure

```text
supply-chain-demand-inventory-forecaster/
│
├── data/
│   ├── raw/
│   └── processed/
│
├── notebooks/
├── reports/
│   └── figures/
│
├── scripts/
│   └── run_eda.py
│
├── src/
│   └── data/
│       ├── data_loader.py
│       └── preprocessing.py
│
├── tests/
│   └── test_preprocessing.py
│
├── README.md
└── .gitignore
```

## 7. Setup and Execution

### Clone the repository

```bash
git clone https://github.com/Fatima-yadwad/supply-chain-demand-inventory-forecaster.git
cd supply-chain-demand-inventory-forecaster
```

### Create and activate a virtual environment

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### Install dependencies

```bash
pip install pandas numpy matplotlib pytest
```

### Add the dataset

Download the Kaggle dataset and place `sales_data.csv` inside:

```text
data/raw/
```

### Run exploratory data analysis

```bash
python -u scripts/run_eda.py
```

### Run preprocessing tests

```bash
python -m pytest tests/test_preprocessing.py -v
```

## 8. Current Development Status

- [x] Dataset loading and inspection
- [x] Data cleaning and preprocessing
- [x] Date and demand lag feature generation
- [x] Exploratory data analysis
- [x] Preprocessing unit tests
- [ ] SARIMAX forecasting
- [ ] Prophet forecasting and model comparison
- [ ] Inventory analytics
- [ ] Streamlit dashboard
- [ ] Final integration and deployment

## 9. Team Contributions

The project is being developed collaboratively, with responsibilities divided across data engineering, forecasting, inventory analytics, and application development.

## 10. Expected Outcome

The final system aims to provide demand forecasts and inventory insights that can support informed replenishment decisions, improve inventory planning, and reduce supply chain inefficiencies.
