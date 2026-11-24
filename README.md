# SupplyIQ – Supply Chain Demand & Inventory Forecaster

## Project Overview

SupplyIQ is an AI-powered supply chain analytics and inventory forecasting platform designed to analyze historical demand, predict future demand, identify inventory risks, and generate replenishment recommendations.

The platform supports historical dataset analysis and uploaded CSV datasets.

## Key Features

### 1. Supply Chain Dashboard

- Overall supply chain performance.
- Product, category, store, and regional analysis.
- Interactive dashboard filters.
- Historical sales and demand visualization.

### 2. AI Demand Forecasting

- 7-day, 15-day, and 30-day demand forecasting.
- SARIMAX and seasonal naive forecasting approaches.
- Chronological model validation.
- Model comparison using MAE, RMSE, and WAPE.
- Automatic selection of the best-performing forecasting approach.

### AI, Machine Learning & Supply Chain Optimization

**Time-Series Forecasting Models**

- **SARIMAX:** Seasonal time-series forecasting to capture demand trends and seasonality.
- **Prophet:** Forecasting model designed to capture trends, seasonality, and changing patterns.
- **Seasonal Naive:** Baseline forecasting model using historical seasonal demand patterns.
- **Model Evaluation:** Chronological validation and model comparison.

**Inventory Optimization**

- Safety Stock Calculation
- Reorder Point Calculation
- Inventory Coverage Analysis
- Replenishment Quantity Recommendations
- Stockout Risk Identification

**Supply Chain Analytics**

- **Bullwhip Effect Analysis:** Evaluates demand variability and amplification across the supply chain.
- Demand Variability Analysis
- Demand Anomaly Detection
- Demand Spike Identification

**Model Performance Metrics**

- MAE – Mean Absolute Error
- RMSE – Root Mean Squared Error
- WAPE – Weighted Absolute Percentage Error

The project includes dedicated Python modules and Jupyter notebooks for forecasting experiments, inventory optimization, and supply chain analytics.

### 3. Inventory Risk Detection

- Estimated inventory levels.
- Average daily demand.
- Stock coverage calculation.
- Critical, High, Medium, Low, and Overstock classifications.
- Stockout risk identification.

### 4. AI Replenishment Recommendations

- Recommended reorder quantities.
- Demand-based replenishment planning.
- Product and store-level recommendations.

### 5. Anomaly Detection and AI Insights

- Unusual demand spike detection.
- Demand trend analysis.
- Inventory warnings.
- Actionable supply chain insights.

### 6. CSV Dataset Upload

- Upload and validate new CSV datasets.
- Data preprocessing and schema validation.
- Analysis using uploaded datasets.
- Dataset switching between original and uploaded data.
- Forecast generation using suitable uploaded historical data.

### 7. Weekly and Monthly Reports

- Historical demand summaries.
- Forecast summaries.
- Product and category performance.
- Regional and store-level comparisons.
- Inventory risk and replenishment summaries.

## Technology Stack

### Frontend

- React
- Vite
- JavaScript
- Recharts
- CSS

### Backend

- Python
- FastAPI
- Pandas

### Machine Learning and Analytics

- SARIMAX
- Seasonal Naive Forecasting
- Statistical Model Evaluation
- Anomaly Detection

## Dataset

The original historical dataset contains approximately 76,000 records covering January 2022 to January 2024.

It includes information about:

- Products
- Stores
- Categories
- Regions
- Dates
- Demand
- Inventory

## Forecasting Workflow

1. Load the selected dataset.
2. Validate and preprocess the data.
3. Apply the selected product, category, store, and region filters.
4. Prepare historical demand time series.
5. Train and evaluate available forecasting approaches.
6. Select the best-performing model.
7. Generate future demand predictions.
8. Calculate inventory risks and replenishment recommendations.
9. Visualize results through interactive charts and reports.

## Running the Project

### Backend

```powershell
.venv\Scripts\activate
uvicorn backend.main:app --reload
```

Backend URL: http://localhost:8000

API documentation: http://localhost:8000/docs

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Frontend URL: http://localhost:5173

## Important Notes

- Forecasts are estimates based on historical data.
- Inventory calculations based on historical records are estimates, not live warehouse stock.
- Forecast accuracy depends on the quality and amount of uploaded historical data.
- Uploaded datasets must satisfy the application's validation requirements.
