
import React, { useEffect, useMemo, useState } from "react";
import {
  ResponsiveContainer,
  LineChart,
  BarChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";

import api, {
  filterParams,
  getAIReport,
  uploadDataset,
} from "../services/api";

const COLORS = {
  navy: "#172B3A",
  copper: "#C47D48",
  blue: "#6D8799",
  green: "#668A70",
  red: "#B85C50",
  amber: "#C18B38",
  muted: "#78838A",
  border: "#E8E2D9",
  background: "#FFFFFF",
  text: "#263746",
};

const number = (value) => {
  if (value === undefined || value === null || !Number.isFinite(Number(value))) {
    return "—";
  }

  return Number(value).toLocaleString("en-IN", {
    maximumFractionDigits: 2,
  });
};

const titleCase = (value) =>
  String(value || "Unknown")
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());

const getRows = (data, keys) => {
  for (const key of keys) {
    if (Array.isArray(data?.[key])) return data[key];
  }
  return [];
};

const getValue = (item, keys, fallback = 0) => {
  for (const key of keys) {
    if (item?.[key] !== undefined && item?.[key] !== null) {
      return item[key];
    }
  }
  return fallback;
};

const requestError = (reason) => {
  const detail = reason?.response?.data?.detail;
  if (typeof detail === "string" && detail.trim()) return detail;
  return reason?.message || "The service could not return data.";
};

function MetricCard({ label, value, subtitle, accent }) {
  return (
    <div style={styles.metricCard}>
      <div style={{ ...styles.metricAccent, background: accent }} />
      <div style={styles.metricLabel}>{label}</div>
      <div style={styles.metricValue}>{value}</div>
      {subtitle && <div style={styles.metricSubtitle}>{subtitle}</div>}
    </div>
  );
}

function Section({ title, subtitle, children, action }) {
  return (
    <section style={styles.section}>
      <div style={styles.sectionHeader}>
        <div>
          <h3 style={styles.sectionTitle}>{title}</h3>
          {subtitle && <p style={styles.sectionSubtitle}>{subtitle}</p>}
        </div>
        {action}
      </div>
      {children}
    </section>
  );
}

function EmptyState({ children }) {
  return <div style={styles.empty}>{children}</div>;
}

function ReportTable({ rows, label, valueLabel = "Demand" }) {
  if (!rows?.length) {
    return <EmptyState>No report rows are available for this period.</EmptyState>;
  }

  return (
    <div style={styles.tableWrap}>
      <table style={styles.table}>
        <thead>
          <tr>
            <th>{label}</th>
            <th>{valueLabel}</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.name}>
              <td>{row.name}</td>
              <td>{number(row.demand)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function AIIntelligence({
  filters = {},
  datasetId = null,
  datasetMeta = null,
  onDatasetChange = () => {},
  onDatasetUploaded = () => {},
}) {
  const [horizon, setHorizon] = useState(7);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [serviceErrors, setServiceErrors] = useState({});
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState("");
  const [uploadNotice, setUploadNotice] = useState("");
  const [forecast, setForecast] = useState(null);
  const [performance, setPerformance] = useState(null);
  const [inventory, setInventory] = useState([]);
  const [replenishment, setReplenishment] = useState([]);
  const [anomalies, setAnomalies] = useState([]);
  const [insights, setInsights] = useState(null);
  const [weeklyReport, setWeeklyReport] = useState(null);
  const [monthlyReport, setMonthlyReport] = useState(null);

  const params = useMemo(
    () => filterParams(filters, datasetId),
    [filters, datasetId]
  );

  const handleUpload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setUploadError("");
    setUploadNotice("");
    if (!file.name.toLowerCase().endsWith(".csv")) {
      setUploadError("Select a CSV file.");
      event.target.value = "";
      return;
    }
    if (file.size > 20 * 1024 * 1024) {
      setUploadError("The CSV exceeds the 20 MB upload limit.");
      event.target.value = "";
      return;
    }

    setUploading(true);
    try {
      const { data } = await uploadDataset(file);
      onDatasetUploaded(data.dataset_id, data);
      setUploadNotice(
        `${data.name} validated and loaded. ${
          data.forecast_ready
            ? "Forecasting is available."
            : data.forecast_issue
        }`
      );
    } catch (reason) {
      setUploadError(requestError(reason));
    } finally {
      setUploading(false);
      event.target.value = "";
    }
  };

  useEffect(() => {
    let cancelled = false;

    async function loadAIData() {
      setLoading(true);
      setError("");
      setServiceErrors({});

      const requests = await Promise.allSettled([
        api.get("/api/ai/forecast", {
          params: { ...params, horizon },
        }),
        api.get("/api/ai/model-performance", { params }),
        api.get("/api/ai/inventory-risk", { params }),
        api.get("/api/ai/replenishment", { params }),
        api.get("/api/ai/anomalies", { params }),
        api.get("/api/ai/insights", { params }),
      ]);

      if (cancelled) return;

      const [
        forecastResult,
        performanceResult,
        inventoryResult,
        replenishmentResult,
        anomalyResult,
        insightsResult,
      ] = requests;
      const serviceKeys = [
        "forecast",
        "performance",
        "inventory",
        "replenishment",
        "anomalies",
        "insights",
      ];
      const failures = requests.reduce((result, request, index) => {
        if (request.status === "rejected") {
          result[serviceKeys[index]] = requestError(request.reason);
        }
        return result;
      }, {});
      setServiceErrors(failures);

      if (forecastResult.status === "fulfilled") {
        setForecast(forecastResult.value.data);
      } else {
        setForecast(null);
      }

      if (performanceResult.status === "fulfilled") {
        setPerformance(performanceResult.value.data);
      } else {
        setPerformance(null);
      }

      if (inventoryResult.status === "fulfilled") {
        setInventory(
          getRows(inventoryResult.value.data, ["results"])
        );
      } else {
        setInventory([]);
      }

      if (replenishmentResult.status === "fulfilled") {
        setReplenishment(
          getRows(replenishmentResult.value.data, [
            "recommendations",
          ])
        );
      } else {
        setReplenishment([]);
      }

      if (anomalyResult.status === "fulfilled") {
        setAnomalies(
          getRows(anomalyResult.value.data, ["anomalies"])
        );
      } else {
        setAnomalies([]);
      }

      if (insightsResult.status === "fulfilled") {
        setInsights(insightsResult.value.data);
      } else {
        setInsights(null);
      }

      const reportRequests = await Promise.allSettled([
        getAIReport("weekly", filters, datasetId),
        getAIReport("monthly", filters, datasetId),
      ]);
      if (cancelled) return;

      const [weeklyReportResult, monthlyReportResult] = reportRequests;
      if (weeklyReportResult.status === "fulfilled") {
        setWeeklyReport(weeklyReportResult.value.data);
      } else {
        setWeeklyReport(null);
      }
      if (monthlyReportResult.status === "fulfilled") {
        setMonthlyReport(monthlyReportResult.value.data);
      } else {
        setMonthlyReport(null);
      }
      reportRequests.forEach((request, index) => {
        if (request.status === "rejected") {
          failures[index === 0 ? "weekly report" : "monthly report"] =
            requestError(request.reason);
        }
      });
      setServiceErrors(failures);

      const failedCount =
        requests.filter((result) => result.status === "rejected").length +
        reportRequests.filter((result) => result.status === "rejected").length;

      setError(
        failedCount === requests.length + reportRequests.length
          ? `Unable to load AI services: ${Object.entries(failures)
              .map(([key, message]) => `${key}: ${message}`)
              .join(" ")}`
          : failedCount > 0
            ? `${failedCount} AI service(s) failed: ${Object.entries(failures)
                .map(([key, message]) => `${key}: ${message}`)
                .join(" ")}`
            : ""
      );

      setLoading(false);
    }

    loadAIData();

    return () => {
      cancelled = true;
    };
  }, [params, horizon, filters, datasetId]);

  const forecastRows = useMemo(() => {
    const rows = getRows(forecast, ["forecast", "forecasts", "predictions"]);

    return rows.map((item, index) => ({
      date: String(
        getValue(item, ["date", "ds", "forecast_date"], `Day ${index + 1}`)
      ).slice(0, 10),
      predicted: Number(
        getValue(item, [
          "predicted_demand",
          "prediction",
          "forecast",
          "yhat",
          "demand",
        ])
      ),
      lower: Number(
        getValue(item, ["lower_bound", "lower", "yhat_lower"], 0)
      ),
      upper: Number(
        getValue(item, ["upper_bound", "upper", "yhat_upper"], 0)
      ),
    }));
  }, [forecast]);

  const selectedModel =
    performance?.selected_model ||
    forecast?.selected_model ||
    "Not available";

  const metrics =
    performance?.selected_metrics ||
    performance?.validation_metrics?.[selectedModel] ||
    forecast?.validation_metrics?.[selectedModel] ||
    {};

  const chartRows = useMemo(() => {
    const historical = getRows(forecast, ["historical"]).map((item) => ({
      date: String(item.date).slice(0, 10),
      actual: Number(item.actual_demand),
      predicted: null,
    }));

    return [
      ...historical,
      ...forecastRows.map((item) => ({
        date: item.date,
        actual: null,
        predicted: item.predicted,
      })),
    ];
  }, [forecast, forecastRows]);

  const weeklyChartRows = useMemo(() => {
    const actualRows = weeklyReport?.period?.actual_demand_daily || [];
    const predictedRows = weeklyReport?.forecast?.predictions || [];
    return [
      ...actualRows.map((item) => ({
        date: item.date,
        actual: Number(item.demand),
        predicted: null,
      })),
      ...predictedRows.map((item) => ({
        date: item.date,
        actual: null,
        predicted: Number(item.predicted_demand),
      })),
    ];
  }, [weeklyReport]);

  const monthlyChartRows = useMemo(
    () => (monthlyReport?.monthly_summary || []).map((item) => ({
      month: item.month,
      demand: Number(item.actual_demand),
      complete: item.complete,
    })),
    [monthlyReport]
  );

  const monthlyForecastRows =
    monthlyReport?.forecast_30_days?.predictions || [];

  const criticalCount = inventory.filter((item) =>
    String(getValue(item, ["risk", "risk_level", "status"], ""))
      .toLowerCase()
      .includes("critical")
  ).length;

  const highCount = inventory.filter((item) =>
    String(getValue(item, ["risk", "risk_level", "status"], ""))
      .toLowerCase()
      .includes("high")
  ).length;

  const totalReorder = replenishment.reduce(
    (sum, item) =>
      sum +
      Number(
        getValue(item, [
          "recommended_reorder_quantity",
          "reorder_quantity",
        ])
      ),
    0
  );

  const summary =
    typeof insights?.summary === "string"
      ? insights.summary
      : "";

  const insightItems = getRows(insights, ["insights"]);

  return (
    <div style={styles.page}>
      <div style={styles.heading}>
        <div>
          <div style={styles.eyebrow}>SUPPLY CHAIN INTELLIGENCE</div>
          <h1 style={styles.pageTitle}>AI Intelligence</h1>
          <p style={styles.description}>
            Demand prediction, inventory risk analysis and
            intelligent replenishment recommendations.
          </p>
          <div style={styles.datasetTag}>
            {datasetMeta
              ? `${datasetMeta.name} · ${number(datasetMeta.records)} records · ${datasetMeta.date_start} to ${datasetMeta.date_end}`
              : "Historical Dataset · 2022–2024"}
          </div>
        </div>

        <div style={styles.horizonBox}>
          <label style={styles.horizonLabel}>
            Forecast Horizon
          </label>
          <select
            value={horizon}
            onChange={(event) =>
              setHorizon(Number(event.target.value))
            }
            style={styles.select}
          >
            <option value={7}>Next 7 Days</option>
            <option value={15}>Next 15 Days</option>
            <option value={30}>Next 30 Days</option>
          </select>
        </div>
      </div>

      <Section
        title="Dataset"
        subtitle="Upload a validated CSV for this browser session or switch back to the original historical data."
      >
        <div style={styles.datasetControls}>
          <label style={styles.controlField}>
            <span style={styles.smallLabel}>Active dataset</span>
            <select
              value={datasetId || ""}
              onChange={(event) =>
                onDatasetChange(
                  event.target.value || null,
                  event.target.value ? datasetMeta : null
                )
              }
              style={styles.select}
            >
              <option value="">Original historical dataset</option>
              {datasetId && (
                <option value={datasetId}>
                  {datasetMeta?.name || "Uploaded dataset"}
                </option>
              )}
            </select>
          </label>
          <label style={styles.controlField}>
            <span style={styles.smallLabel}>Upload new CSV (max 20 MB)</span>
            <input
              type="file"
              accept=".csv,text/csv"
              onChange={handleUpload}
              disabled={uploading}
              style={styles.fileInput}
            />
          </label>
        </div>
        <p style={styles.note}>
          Required: Date, Store ID, Product ID, and Demand (or Units Sold).
          Inventory Level is optional; without complete inventory values,
          stock risk and replenishment are unavailable. Uploads stay in
          backend memory for this session and expire after inactivity.
        </p>
        {uploading && (
          <div style={styles.loading}>Validating and preprocessing CSV...</div>
        )}
        {uploadError && <div style={styles.warning}>{uploadError}</div>}
        {uploadNotice && <div style={styles.success}>{uploadNotice}</div>}
        {datasetMeta?.forecast_issue && (
          <div style={styles.warning}>{datasetMeta.forecast_issue}</div>
        )}
        {datasetMeta?.inventory_issue && (
          <div style={styles.warning}>{datasetMeta.inventory_issue}</div>
        )}
        {datasetMeta?.duplicate_rows_removed > 0 && (
          <div style={styles.note}>
            {datasetMeta.duplicate_rows_removed} exact duplicate row(s) were
            removed during preprocessing.
          </div>
        )}
      </Section>

      {error && (
        <div style={styles.warning}>
          {error}
        </div>
      )}

      {loading && (
        <div style={styles.loading}>
          Loading AI analysis from your backend...
        </div>
      )}

      <div style={styles.metricGrid}>
        <MetricCard
          label="Selected Forecast Model"
          value={titleCase(selectedModel)}
          subtitle="Based on validation"
          accent={COLORS.copper}
        />
        <MetricCard
          label="Critical Inventory"
          value={serviceErrors.inventory ? "—" : number(criticalCount)}
          subtitle="Critical-risk combinations"
          accent={COLORS.red}
        />
        <MetricCard
          label="High Inventory Risk"
          value={serviceErrors.inventory ? "—" : number(highCount)}
          subtitle="High-risk combinations"
          accent={COLORS.amber}
        />
        <MetricCard
          label="Suggested Reorder"
          value={serviceErrors.replenishment ? "—" : number(totalReorder)}
          subtitle="Units across recommendations"
          accent={COLORS.green}
        />
      </div>

      <Section
        title="AI Demand Prediction"
        subtitle={`Last 30 days of historical actual demand and the next ${horizon} days of predicted demand`}
      >
        {serviceErrors.forecast ? (
          <EmptyState>{serviceErrors.forecast}</EmptyState>
        ) : forecastRows.length > 0 ? (
          <>
            <div style={styles.chart}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartRows}>
                  <CartesianGrid
                    strokeDasharray="3 3"
                    stroke="#EAE6E0"
                  />
                  <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="actual"
                    name="Historical Actual Demand"
                    stroke={COLORS.blue}
                    strokeWidth={2}
                    dot={false}
                    connectNulls={false}
                  />
                  <Line
                    type="monotone"
                    dataKey="predicted"
                    name="Predicted Demand"
                    stroke={COLORS.copper}
                    strokeWidth={3}
                    dot={{ r: 3 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>

            <div style={styles.forecastSummary}>
              <div>
                <span style={styles.smallLabel}>
                  Total predicted demand
                </span>
                <strong>
                  {number(
                    getValue(
                      forecast,
                      ["total_predicted_demand"],
                      forecastRows.reduce(
                        (sum, item) => sum + item.predicted,
                        0
                      )
                    )
                  )}
                </strong>
              </div>
              <div>
                <span style={styles.smallLabel}>
                  Average daily prediction
                </span>
                <strong>
                  {number(
                    getValue(
                      forecast,
                      ["average_daily_forecast"],
                      forecastRows.reduce(
                        (sum, item) => sum + item.predicted,
                        0
                      ) / forecastRows.length
                    )
                  )}
                </strong>
              </div>
              <div>
                <span style={styles.smallLabel}>Model used</span>
                <strong>{titleCase(selectedModel)}</strong>
              </div>
            </div>
          </>
        ) : (
          <EmptyState>
            {forecast
              ? "No forecast rows were returned for these selections."
              : "Forecast data is not available. Check the backend response."}
          </EmptyState>
        )}
      </Section>

      <Section
        title="Model Performance"
        subtitle="Chronological holdout validation on the selected historical data"
      >
        {serviceErrors.performance ? (
          <EmptyState>{serviceErrors.performance}</EmptyState>
        ) : (
          <>
            <div style={styles.metricGrid}>
              <MetricCard
                label="MAE"
                value={number(metrics.mae)}
                subtitle="Mean Absolute Error"
                accent={COLORS.blue}
              />
              <MetricCard
                label="RMSE"
                value={number(metrics.rmse)}
                subtitle="Root Mean Squared Error"
                accent={COLORS.copper}
              />
              <MetricCard
                label="WAPE"
                value={
                  metrics.wape === undefined || metrics.wape === null
                    ? "—"
                    : `${number(metrics.wape)}%`
                }
                subtitle="Weighted Absolute Percentage Error"
                accent={COLORS.green}
              />
              <MetricCard
                label="Historical Days"
                value={number(performance?.historical_days)}
                subtitle="Days used for evaluation"
                accent={COLORS.amber}
              />
            </div>
            <p style={styles.note}>
              Lower error values indicate better validation accuracy.
              These metrics are calculated for the currently selected
              data, not copied from the previous Model Insights page.
            </p>
            <div style={styles.tableWrap}>
              <table style={styles.table}>
                <thead>
                  <tr>
                    <th>Model</th>
                    <th>MAE</th>
                    <th>RMSE</th>
                    <th>WAPE</th>
                    <th>Selection</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(performance?.validation_metrics || {}).map(
                    ([model, scores]) => (
                      <tr key={model}>
                        <td>{titleCase(model)}</td>
                        <td>{number(scores.mae)}</td>
                        <td>{number(scores.rmse)}</td>
                        <td>
                          {scores.wape === null || scores.wape === undefined
                            ? "—"
                            : `${number(scores.wape)}%`}
                        </td>
                        <td>
                          {model === selectedModel
                            ? "Selected"
                            : "Compared"}
                        </td>
                      </tr>
                    )
                  )}
                  {Object.entries(performance?.model_errors || {}).map(
                    ([model, message]) => (
                      <tr key={`${model}-error`}>
                        <td>{titleCase(model)}</td>
                        <td colSpan={4}>
                          Validation unavailable: {message}
                        </td>
                      </tr>
                    )
                  )}
                </tbody>
              </table>
            </div>
          </>
        )}
      </Section>

      <Section
        title="Inventory Risk Detection"
        subtitle="Historical stock coverage analysis by product and store"
      >
        {serviceErrors.inventory ? (
          <EmptyState>{serviceErrors.inventory}</EmptyState>
        ) : inventory.length > 0 ? (
          <div style={styles.tableWrap}>
            <table style={styles.table}>
              <thead>
                <tr>
                  <th>Product</th>
                  <th>Store</th>
                  <th>Estimated Current Stock</th>
                  <th>Average Daily Demand</th>
                  <th>Coverage Days</th>
                  <th>Risk</th>
                </tr>
              </thead>
              <tbody>
                {inventory.slice(0, 20).map((item, index) => {
                  const risk = getValue(
                    item,
                    ["risk", "risk_level", "status"],
                    "Unknown"
                  );

                  return (
                    <tr key={`${item.product_id}-${item.store_id}-${index}`}>
                      <td>{item.product_id || "—"}</td>
                      <td>{item.store_id || "—"}</td>
                      <td>
                        {number(
                          getValue(item, [
                            "current_stock_estimate",
                            "current_stock",
                            "latest_stock",
                            "inventory_level",
                          ])
                        )}
                      </td>
                      <td>{number(item.average_daily_demand)}</td>
                      <td>
                        {number(item.stock_coverage_days)}
                      </td>
                      <td>
                        <span
                          style={{
                            ...styles.riskBadge,
                            background:
                              String(risk).toLowerCase() === "critical"
                                ? "#FCE8E5"
                                : String(risk).toLowerCase() === "high"
                                  ? "#FFF0D9"
                                  : "#E8F0EA",
                            color:
                              String(risk).toLowerCase() === "critical"
                                ? COLORS.red
                                : String(risk).toLowerCase() === "high"
                                  ? "#A36A1E"
                                  : COLORS.green,
                          }}
                        >
                          {titleCase(risk)}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState>No inventory risk results available.</EmptyState>
        )}
      </Section>

      <Section
        title="Smart Replenishment"
        subtitle="Suggested reorder quantities based on a 14-day target stock level"
      >
        {serviceErrors.replenishment ? (
          <EmptyState>{serviceErrors.replenishment}</EmptyState>
        ) : replenishment.length > 0 ? (
          <div style={styles.tableWrap}>
            <table style={styles.table}>
              <thead>
                <tr>
                  <th>Product</th>
                  <th>Store</th>
                  <th>Estimated Current Stock</th>
                  <th>Average Daily Demand</th>
                  <th>Recommended Reorder</th>
                </tr>
              </thead>
              <tbody>
                {replenishment.slice(0, 20).map((item, index) => (
                  <tr key={`${item.product_id}-${item.store_id}-${index}`}>
                    <td>{item.product_id || "—"}</td>
                    <td>{item.store_id || "—"}</td>
                    <td>
                      {number(
                        getValue(item, [
                          "current_stock_estimate",
                          "current_stock",
                          "latest_stock",
                        ])
                      )}
                    </td>
                    <td>
                      {number(
                        getValue(item, [
                          "average_daily_demand",
                          "avg_daily_demand",
                        ])
                      )}
                    </td>
                    <td style={{ fontWeight: 700, color: COLORS.green }}>
                      {number(
                        getValue(item, [
                          "recommended_reorder_quantity",
                          "reorder_quantity",
                        ])
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState>
            No reorder recommendations are currently available.
          </EmptyState>
        )}
      </Section>

      <Section
        title="Demand Anomaly Detection"
        subtitle="Unusual historical demand patterns identified by the analytics service"
      >
        {serviceErrors.anomalies ? (
          <EmptyState>{serviceErrors.anomalies}</EmptyState>
        ) : anomalies.length > 0 ? (
          <div style={styles.tableWrap}>
            <table style={styles.table}>
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Product</th>
                  <th>Store</th>
                  <th>Demand</th>
                  <th>Severity</th>
                </tr>
              </thead>
              <tbody>
                {anomalies.slice(0, 20).map((item, index) => (
                  <tr key={index}>
                    <td>
                      {String(
                        getValue(item, ["date", "Date"], "—")
                      ).slice(0, 10)}
                    </td>
                    <td>{item.product_id || "—"}</td>
                    <td>{item.store_id || "—"}</td>
                    <td>
                      {number(
                        getValue(item, [
                          "actual_demand",
                          "demand",
                          "target_demand",
                          "units_sold",
                        ])
                      )}
                    </td>
                    <td>
                      {titleCase(
                        getValue(
                          item,
                          ["severity", "risk", "status"],
                          "Anomaly"
                        )
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState>No demand anomalies were returned.</EmptyState>
        )}
      </Section>

      <Section
        title="AI Business Insights"
        subtitle="Summary and actionable observations from the selected data"
      >
        {serviceErrors.insights ? (
          <EmptyState>{serviceErrors.insights}</EmptyState>
        ) : (
          <>
        {summary && <p style={styles.insightSummary}>{summary}</p>}

        {insightItems.length > 0 ? (
          <div style={styles.insightList}>
            {insightItems.map((item, index) => (
              <div style={styles.insightItem} key={index}>
                <div style={styles.insightNumber}>
                  {index + 1}
                </div>
                <div>
                  <strong>
                    {typeof item === "string"
                      ? item
                      : item.title || item.type || "Supply Chain Insight"}
                  </strong>
                  {typeof item === "object" && (
                    <p style={styles.insightText}>
                      {item.description ||
                        item.message ||
                        item.recommendation ||
                        ""}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : !summary ? (
          <EmptyState>No business insights are available.</EmptyState>
        ) : null}
          </>
        )}
      </Section>

      <Section
        title="Weekly Report"
        subtitle="Trailing seven-day actual demand and the following seven-day forecast, using the active dataset and filters."
      >
        {serviceErrors["weekly report"] ? (
          <EmptyState>{serviceErrors["weekly report"]}</EmptyState>
        ) : weeklyReport ? (
          <>
            <p style={styles.note}>
              Actual period: {weeklyReport.period.start} to{" "}
              {weeklyReport.period.end} (
              {weeklyReport.period.complete ? "complete" : "incomplete"}).
              Predicted values are for future dates and are not actual sales.
              {weeklyReport.trend.comparison_available
                ? ` Demand changed ${number(weeklyReport.trend.change_percent)}% versus the prior seven days.`
                : " Prior-period comparison is unavailable."}
            </p>
            <div style={styles.forecastSummary}>
              <div>
                <span style={styles.smallLabel}>Weekly actual demand</span>
                <strong>
                  {number(weeklyReport.period.actual_demand_total)}
                </strong>
              </div>
              <div>
                <span style={styles.smallLabel}>Next 7 predicted demand</span>
                <strong>
                  {weeklyReport.forecast.available
                    ? number(
                        weeklyReport.forecast.predictions.reduce(
                          (sum, item) =>
                            sum + Number(item.predicted_demand || 0),
                          0
                        )
                      )
                    : "—"}
                </strong>
              </div>
            </div>
            <div style={styles.chart}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={weeklyChartRows}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#EAE6E0" />
                  <XAxis dataKey="date" tick={{ fontSize: 10 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="actual"
                    name="Historical Actual Demand"
                    stroke={COLORS.blue}
                    strokeWidth={2}
                    dot={false}
                  />
                  <Line
                    type="monotone"
                    dataKey="predicted"
                    name="Predicted Demand"
                    stroke={COLORS.copper}
                    strokeWidth={3}
                    dot={{ r: 3 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
            {!weeklyReport.forecast.available && (
              <div style={styles.warning}>
                Forecast unavailable: {weeklyReport.forecast.reason}
              </div>
            )}
            <div style={styles.reportGrid}>
              <div>
                <h4 style={styles.reportTitle}>Highest-demand products</h4>
                <ReportTable
                  rows={weeklyReport.highest_demand_products}
                  label="Product"
                />
              </div>
              <div>
                <h4 style={styles.reportTitle}>Lowest-demand products</h4>
                <ReportTable
                  rows={weeklyReport.lowest_demand_products}
                  label="Product"
                />
              </div>
              <div>
                <h4 style={styles.reportTitle}>Store performance</h4>
                <ReportTable
                  rows={weeklyReport.store_performance}
                  label="Store"
                />
              </div>
              <div>
                <h4 style={styles.reportTitle}>Regional performance</h4>
                <ReportTable
                  rows={weeklyReport.regional_performance}
                  label="Region"
                />
              </div>
            </div>
            {!weeklyReport.inventory_risk.available && (
              <div style={styles.warning}>
                Inventory report unavailable:{" "}
                {weeklyReport.inventory_risk.reason}
              </div>
            )}
            {weeklyReport.inventory_risk.available && (
              <ReportTable
                rows={weeklyReport.inventory_risk.stockout_warnings.map((item) => ({
                  name: `${item.product_id} · ${item.store_id}`,
                  demand: item.stock_coverage_days,
                }))}
                label="High-risk product · store"
                valueLabel="Coverage days"
              />
            )}
            {!weeklyReport.replenishment.available && (
              <div style={styles.warning}>
                Replenishment unavailable: {weeklyReport.replenishment.reason}
              </div>
            )}
            {weeklyReport.replenishment.available && (
              <ReportTable
                rows={weeklyReport.replenishment.recommendations.map((item) => ({
                  name: `${item.product_id} · ${item.store_id}`,
                  demand: item.recommended_reorder_quantity,
                }))}
                label="Product · Store"
                valueLabel="Recommended reorder quantity"
              />
            )}
          </>
        ) : (
          <EmptyState>Weekly report is not available.</EmptyState>
        )}
      </Section>

      <Section
        title="Monthly Report"
        subtitle="Historical monthly demand, completeness status, month-over-month comparison, and the next 30 forecast days."
      >
        {serviceErrors["monthly report"] ? (
          <EmptyState>{serviceErrors["monthly report"]}</EmptyState>
        ) : monthlyReport ? (
          <>
            <p style={styles.note}>
              Latest actual month: {monthlyReport.latest_actual_month.month} (
              {monthlyReport.latest_actual_month.complete
                ? "complete"
                : "incomplete"}).
              {monthlyReport.forecast_30_days.available
                ? ` Next-30-day forecast uses ${titleCase(monthlyReport.forecast_30_days.selected_model)}.`
                : ` Next-30-day forecast unavailable: ${monthlyReport.forecast_30_days.reason}`}
            </p>
            <div style={styles.forecastSummary}>
              <div>
                <span style={styles.smallLabel}>Latest month actual demand</span>
                <strong>
                  {number(monthlyReport.latest_actual_month.actual_demand)}
                </strong>
              </div>
              <div>
                <span style={styles.smallLabel}>Next 30 predicted demand</span>
                <strong>
                  {monthlyReport.forecast_30_days.available
                    ? number(
                        monthlyForecastRows.reduce(
                          (sum, item) =>
                            sum + Number(item.predicted_demand || 0),
                          0
                        )
                      )
                    : "—"}
                </strong>
              </div>
            </div>
            <div style={styles.chart}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={monthlyChartRows}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#EAE6E0" />
                  <XAxis dataKey="month" tick={{ fontSize: 10 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Legend />
                  <Bar
                    dataKey="demand"
                    name="Historical Actual Demand (partial months flagged below)"
                    fill={COLORS.blue}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <ReportTable
              rows={monthlyReport.monthly_summary.map((item) => ({
                name: `${item.month} · ${item.complete ? "Complete" : "Incomplete"} (${item.days_observed}/${item.days_in_month} days)`,
                demand: item.actual_demand,
              }))}
              label="Historical actual period"
            />
            <div style={styles.reportGrid}>
              <div>
                <h4 style={styles.reportTitle}>Product performance</h4>
                <ReportTable
                  rows={monthlyReport.product_performance}
                  label="Product"
                />
              </div>
              <div>
                <h4 style={styles.reportTitle}>Category performance</h4>
                <ReportTable
                  rows={monthlyReport.category_performance}
                  label="Category"
                />
              </div>
              <div>
                <h4 style={styles.reportTitle}>Store performance</h4>
                <ReportTable
                  rows={monthlyReport.store_performance}
                  label="Store"
                />
              </div>
              <div>
                <h4 style={styles.reportTitle}>Regional performance</h4>
                <ReportTable
                  rows={monthlyReport.regional_performance}
                  label="Region"
                />
              </div>
            </div>
            <h4 style={styles.reportTitle}>Month-over-month changes</h4>
            <ReportTable
              rows={monthlyReport.month_over_month_comparison.map((item) => ({
                name: `${item.previous_month} to ${item.month}`,
                demand: item.change_percent,
              }))}
              label="Complete month comparison"
              valueLabel="Demand change (%)"
            />
            {monthlyReport.forecast_30_days.available && (
              <>
                <h4 style={styles.reportTitle}>Next 30 predicted days</h4>
                <ReportTable
                  rows={monthlyForecastRows.map((item) => ({
                    name: item.date,
                    demand: item.predicted_demand,
                  }))}
                  label="Future date"
                  valueLabel="Predicted demand"
                />
              </>
            )}
            {!monthlyReport.inventory_risk.available && (
              <div style={styles.warning}>
                Inventory report unavailable:{" "}
                {monthlyReport.inventory_risk.reason}
              </div>
            )}
            {monthlyReport.inventory_risk.available && (
              <ReportTable
                rows={monthlyReport.inventory_risk.stockout_warnings.map((item) => ({
                  name: `${item.product_id} · ${item.store_id}`,
                  demand: item.stock_coverage_days,
                }))}
                label="High-risk product · store"
                valueLabel="Coverage days"
              />
            )}
            {!monthlyReport.replenishment.available && (
              <div style={styles.warning}>
                Replenishment unavailable: {monthlyReport.replenishment.reason}
              </div>
            )}
            {monthlyReport.replenishment.available && (
              <ReportTable
                rows={monthlyReport.replenishment.recommendations.map((item) => ({
                  name: `${item.product_id} · ${item.store_id}`,
                  demand: item.recommended_reorder_quantity,
                }))}
                label="Product · Store"
                valueLabel="Recommended reorder quantity"
              />
            )}
            <div style={styles.insightList}>
              {monthlyReport.insights.map((item, index) => (
                <div style={styles.insightItem} key={`${item.type}-${index}`}>
                  <strong>{item.type}</strong>
                  <span style={styles.insightText}>{item.message}</span>
                </div>
              ))}
            </div>
          </>
        ) : (
          <EmptyState>Monthly report is not available.</EmptyState>
        )}
      </Section>

      <div style={styles.disclaimer}>
        <strong>Methodology note:</strong> Demand forecasts use
        statistical forecasting. Inventory risk and replenishment
        use historical stock-coverage rules. Anomaly detection and
        business insights use analytical rules. These results are
        based on historical dataset records and are not live stock
        or real-time demand measurements.
      </div>
    </div>
  );
}

const styles = {
  page: {
    display: "flex",
    flexDirection: "column",
    gap: 22,
    color: COLORS.text,
    width: "100%",
  },
  heading: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "flex-end",
    flexWrap: "wrap",
    gap: 18,
  },
  eyebrow: {
    fontSize: 10,
    letterSpacing: 2,
    fontWeight: 800,
    color: COLORS.copper,
    marginBottom: 8,
  },
  pageTitle: {
    fontSize: 29,
    fontWeight: 800,
    color: COLORS.navy,
    margin: 0,
  },
  description: {
    color: COLORS.muted,
    fontSize: 13,
    margin: "8px 0",
  },
  datasetTag: {
    fontSize: 11,
    color: COLORS.muted,
    marginTop: 8,
  },
  datasetControls: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(230px, 1fr))",
    gap: 16,
  },
  controlField: {
    display: "flex",
    flexDirection: "column",
    gap: 7,
    minWidth: 0,
  },
  fileInput: {
    width: "100%",
    boxSizing: "border-box",
    border: `1px solid ${COLORS.border}`,
    borderRadius: 8,
    padding: 8,
    background: "#fff",
    color: COLORS.text,
  },
  success: {
    padding: 13,
    borderRadius: 9,
    background: "#E8F0EA",
    color: COLORS.green,
    fontSize: 12,
    marginTop: 10,
  },
  horizonBox: {
    display: "flex",
    flexDirection: "column",
    gap: 7,
    minWidth: 155,
  },
  horizonLabel: {
    fontSize: 11,
    fontWeight: 700,
    color: COLORS.muted,
  },
  select: {
    border: `1px solid ${COLORS.border}`,
    borderRadius: 8,
    padding: "10px 12px",
    background: "#fff",
    color: COLORS.navy,
    fontWeight: 600,
  },
  warning: {
    padding: 13,
    borderRadius: 9,
    background: "#FFF2E5",
    color: "#89551E",
    fontSize: 12,
  },
  loading: {
    padding: 12,
    color: COLORS.muted,
    fontSize: 12,
  },
  metricGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))",
    gap: 13,
  },
  metricCard: {
    background: COLORS.background,
    border: `1px solid ${COLORS.border}`,
    borderRadius: 11,
    padding: 17,
    minWidth: 0,
    position: "relative",
    overflow: "hidden",
  },
  metricAccent: {
    position: "absolute",
    left: 0,
    top: 0,
    bottom: 0,
    width: 4,
  },
  metricLabel: {
    fontSize: 11,
    color: COLORS.muted,
    fontWeight: 700,
    marginBottom: 11,
  },
  metricValue: {
    fontSize: 23,
    fontWeight: 800,
    color: COLORS.navy,
    overflowWrap: "anywhere",
  },
  metricSubtitle: {
    fontSize: 10,
    color: COLORS.muted,
    marginTop: 7,
  },
  section: {
    background: COLORS.background,
    border: `1px solid ${COLORS.border}`,
    borderRadius: 12,
    padding: 19,
    minWidth: 0,
  },
  sectionHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    gap: 12,
    marginBottom: 17,
  },
  sectionTitle: {
    fontSize: 16,
    color: COLORS.navy,
    fontWeight: 800,
    margin: 0,
  },
  sectionSubtitle: {
    fontSize: 11,
    color: COLORS.muted,
    margin: "5px 0 0",
  },
  chart: {
    width: "100%",
    height: 290,
  },
  forecastSummary: {
    display: "flex",
    flexWrap: "wrap",
    gap: 30,
    borderTop: `1px solid ${COLORS.border}`,
    paddingTop: 15,
    marginTop: 12,
  },
  smallLabel: {
    display: "block",
    fontSize: 10,
    color: COLORS.muted,
    marginBottom: 6,
  },
  forecastSummaryStrong: {
    fontSize: 15,
  },
  reportGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(230px, 1fr))",
    gap: 16,
    marginTop: 18,
  },
  reportTitle: {
    color: COLORS.navy,
    fontSize: 12,
    margin: "16px 0 8px",
  },
  note: {
    color: COLORS.muted,
    fontSize: 11,
    marginBottom: 0,
  },
  tableWrap: {
    overflowX: "auto",
    width: "100%",
  },
  table: {
    borderCollapse: "collapse",
    width: "100%",
    minWidth: 570,
    fontSize: 11,
    textAlign: "left",
  },
  riskBadge: {
    display: "inline-block",
    padding: "5px 9px",
    borderRadius: 20,
    fontSize: 10,
    fontWeight: 800,
  },
  empty: {
    background: "#F8F7F4",
    borderRadius: 8,
    padding: 22,
    textAlign: "center",
    color: COLORS.muted,
    fontSize: 12,
  },
  insightSummary: {
    fontSize: 13,
    lineHeight: 1.7,
    color: COLORS.text,
  },
  insightList: {
    display: "flex",
    flexDirection: "column",
    gap: 13,
  },
  insightItem: {
    display: "flex",
    alignItems: "flex-start",
    gap: 12,
    padding: 12,
    borderRadius: 8,
    background: "#F8F7F4",
    fontSize: 12,
  },
  insightNumber: {
    background: "#EFE3D8",
    color: COLORS.copper,
    width: 25,
    height: 25,
    borderRadius: "50%",
    display: "grid",
    placeItems: "center",
    fontWeight: 800,
    flexShrink: 0,
  },
  insightText: {
    color: COLORS.muted,
    lineHeight: 1.6,
    margin: "5px 0 0",
  },
  disclaimer: {
    padding: 14,
    background: "#F5F2ED",
    borderRadius: 9,
    color: COLORS.muted,
    fontSize: 11,
    lineHeight: 1.7,
  },
};
