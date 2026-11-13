# Model Comparison Report
## Supply Chain Demand and Inventory Forecasting

### 1. Introduction

This project focuses on forecasting product demand using time-series forecasting techniques. The objective is to predict future demand and support better inventory planning and management.

The Prophet model is being developed as part of the forecasting module. Its performance will later be compared with other models developed by the team, including SARIMAX.

### 2. Prophet Model

Prophet is a time-series forecasting model developed by Meta. It is designed to identify patterns in time-series data, including:

- Trend: Long-term increase or decrease in demand.
- Seasonality: Repeated patterns over time.
- Holidays and special events: Changes caused by specific dates or events.

For this project, Prophet was trained using historical demand data.

### 3. Dataset Used for Initial Testing

Synthetic daily demand data was generated to test the Prophet implementation before integrating the actual project dataset.

| Description | Value |
|---|---:|
| Total records | 365 |
| Training records | 292 |
| Testing records | 73 |
| Training percentage | 80% |
| Testing percentage | 20% |
| Data frequency | Daily |

**Note:** These are preliminary results using synthetic data, not the actual Kaggle dataset.

### 4. Implementation Steps

1. Generated daily demand data.
2. Converted the date and demand columns into Prophet format (`ds` and `y`).
3. Divided the data chronologically into training and testing sets.
4. Trained the Prophet forecasting model.
5. Generated predictions for the testing dates.
6. Compared actual demand with predicted demand.
7. Calculated evaluation metrics.
8. Plotted actual and predicted demand for visualization.

### 5. Prophet Evaluation Results

The following metrics were obtained using the synthetic test dataset.

| Evaluation Metric | Result |
|---|---:|
| MAE | 6.93 |
| RMSE | 8.00 |
| MAPE | 4.73% |
| WAPE | 4.77% |
| Forecast Bias | -6.81 |

### 6. Interpretation of Results

- **MAE:** The average absolute prediction error is approximately 6.93 demand units.
- **RMSE:** The root mean squared error is 8.00, giving more weight to larger prediction errors.
- **MAPE:** The average absolute percentage error is approximately 4.73%.
- **WAPE:** The weighted absolute percentage error is approximately 4.77%.
- **Forecast Bias:** The negative value (-6.81) indicates that the model tends to underestimate demand.

### 7. Model Comparison

The Prophet model will be compared with the SARIMAX model after the team integrates the actual dataset and completes both implementations.

| Evaluation Metric | Prophet | SARIMAX |
|---|---:|---:|
| MAE | 6.93* | Pending |
| RMSE | 8.00* | Pending |
| MAPE | 4.73%* | Pending |
| WAPE | 4.77%* | Pending |
| Forecast Bias | -6.81* | Pending |

*Prophet values are from preliminary synthetic-data testing. They must not be directly compared with SARIMAX results until both models use the same dataset, target series, training/testing dates, and evaluation procedure.*

### 8. Conclusion

The Prophet model was successfully implemented and tested using synthetic daily demand data. The implementation includes data preparation, model training, forecasting, evaluation, and visualization.

The next stage is to integrate the actual project dataset, retrain the model, and compare its performance with SARIMAX using the same testing period and evaluation metrics.

This comparison will help identify the more suitable forecasting approach for the final supply chain demand and inventory forecasting system.

---

**Report Status:** Preliminary implementation completed. Actual dataset integration and final model comparison are pending.