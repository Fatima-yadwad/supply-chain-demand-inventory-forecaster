import heroImage from "./assets/hero.png";
import { useEffect, useState } from "react";
import {
  ResponsiveContainer,
  AreaChart, Area,
  LineChart, Line,
  BarChart, Bar,
  PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid,
  Tooltip, Legend,
} from "recharts";
import AIIntelligence from "./pages/AIIntelligence";
import {
  getOverview,
  getDemand,
  getSales,
  getInventory,
  getAnalytics,
  getFilters,
  getDataset,
} from "./services/api";

import "./index.css";

const ALL = ["All"];

const INITIAL_FILTERS = {
  product: ALL,
  category: ALL,
  store: ALL,
  region: ALL,
};

const COLORS = [
  "#C47D48",
  "#6D8799",
  "#17283F",
  "#D5B58B",
  "#8C9D86",
];

const NAV_ITEMS = [
  ["control", "Control Tower"],
  ["inventory", "Inventory"],
  ["demand", "Demand Forecast"],
  ["sales", "Sales Analytics"],
  ["replenishment", "Replenishment Lab"],
  ["models", "Model Insights"],
  ["ai", "AI Intelligence"],
];
const FILTER_FIELDS = [
  { key: "product", label: "Product", all: "All Products" },
  { key: "category", label: "Category", all: "All Categories" },
  { key: "store", label: "Store", all: "All Stores" },
  { key: "region", label: "Region", all: "All Regions" },
];

const fmt = (value) => {
  const numeric = Number(value);
  if (value === null || value === undefined || !Number.isFinite(numeric)) {
    return "—";
  }

  return numeric.toLocaleString("en-IN", {
    maximumFractionDigits: 2,
  });
};

function FilterDropdown({
  field,
  options,
  value,
  onChange,
  open,
  setOpen,
}) {
  const isAll = value.includes("All");

  const toggleAll = () => {
    onChange(isAll ? [] : ALL);
  };

  const toggleOption = (option) => {
    const item = String(option);
    let next;

    if (isAll) {
      next = options.map(String).filter((v) => v !== item);
    } else if (value.includes(item)) {
      next = value.filter((v) => v !== item);
    } else {
      next = [...value, item];
    }

    if (options.length && options.every((v) => next.includes(String(v)))) {
      next = ALL;
    }

    onChange(next);
  };

  const label = isAll
    ? field.all
    : value.length === 0
      ? "None selected"
      : value.length === 1
        ? value[0]
        : `${value.length} selected`;

  return (
    <div className="siq-filter">
      <label className="siq-filter-label">{field.label}</label>

      <button
        type="button"
        className={`siq-dropdown-button ${open ? "is-open" : ""}`}
        onClick={() => setOpen(open ? null : field.key)}
      >
        <span>{label}</span>
        <span className="siq-chevron">⌄</span>
      </button>

      {open === field.key && (
        <div className="siq-dropdown-menu">
          <div className="siq-dropdown-top">
            <strong>{field.label}</strong>
            <span>
              {isAll ? options.length : value.length} / {options.length}
            </span>
          </div>

          <label className="siq-check-option siq-select-all">
            <input
              type="checkbox"
              checked={isAll}
              onChange={toggleAll}
            />
            <span>Select all</span>
          </label>

          <div className="siq-option-list">
            {options.map((option) => (
              <label className="siq-check-option" key={option}>
                <input
                  type="checkbox"
                  checked={isAll || value.includes(String(option))}
                  onChange={() => toggleOption(option)}
                />
                <span>{option}</span>
              </label>
            ))}
          </div>

          <div className="siq-dropdown-footer">
            <button type="button" onClick={() => onChange(ALL)}>
              Select all
            </button>
            <button type="button" onClick={() => onChange([])}>
              Clear
            </button>
            <button type="button" onClick={() => setOpen(null)}>
              Done
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function FiltersPanel({ draft, setDraft, options, onApply, onReset, loading }) {
  const [open, setOpen] = useState(null);

  return (
    <section className="siq-filter-panel">
      <div className="siq-panel-heading">
        <div>
          <h2>Dashboard Filters</h2>
          <p>Choose parameters to analyse your supply chain data.</p>
        </div>
        <span className="siq-filter-hint">Multiple selection available</span>
      </div>

      <div className="siq-filter-grid">
        {FILTER_FIELDS.map((field) => (
          <FilterDropdown
            key={field.key}
            field={field}
            options={options[field.key] || []}
            value={draft[field.key] || ALL}
            onChange={(values) =>
              setDraft((current) => ({
                ...current,
                [field.key]: values,
              }))
            }
            open={open}
            setOpen={setOpen}
          />
        ))}
      </div>

      <div className="siq-filter-actions">
        <button
          className="siq-apply-button"
          disabled={loading}
          onClick={() => {
            setOpen(null);
            onApply();
          }}
        >
          {loading ? "Applying..." : "Apply Filters"}
        </button>

        <button
          className="siq-reset-button"
          onClick={() => {
            setOpen(null);
            onReset();
          }}
        >
          Reset Filters
        </button>
      </div>
    </section>
  );
}

function MetricCard({ label, value, note }) {
  return (
    <div className="siq-metric-card">
      <span className="siq-metric-label">{label}</span>
      <strong>{fmt(value)}</strong>
      <small>{note}</small>
    </div>
  );
}

function Panel({ title, subtitle, children }) {
  return (
    <section className="siq-panel">
      <div className="siq-panel-heading">
        <div>
          <h2>{title}</h2>
          {subtitle && <p>{subtitle}</p>}
        </div>
      </div>
      {children}
    </section>
  );
}

function EmptyChart() {
  return (
    <div className="siq-empty">
      No data available for the selected filters.
    </div>
  );
}

function ChartTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;

  return (
    <div className="siq-tooltip">
      <strong>{label}</strong>
      {payload.map((item) => (
        <div key={item.dataKey}>
          {item.name || item.dataKey}: {fmt(item.value)}
        </div>
      ))}
    </div>
  );
}

function DataTable({ columns, rows }) {
  if (!rows?.length) return <EmptyChart />;

  return (
    <div className="siq-table-wrap">
      <table className="siq-table">
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column.key}>{column.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={index}>
              {columns.map((column) => (
                <td key={column.key}>
                  {column.render
                    ? column.render(row[column.key], row)
                    : row[column.key] ?? "—"}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function SalesDemandChart({ demand, sales }) {
  const salesMap = new Map(sales.map((row) => [row.date, row.units_sold]));

  const combined = demand.map((row) => ({
    date: row.date,
    demand: row.demand,
    units_sold: salesMap.get(row.date) || 0,
  }));

  return (
    <Panel
      title="Demand vs Sales"
      subtitle="Daily demand compared with units sold"
    >
      {combined.length ? (
        <ResponsiveContainer width="100%" height={310}>
          <LineChart data={combined}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e7e1d8" />
            <XAxis dataKey="date" tick={{ fontSize: 10 }} />
            <YAxis />
            <Tooltip content={<ChartTooltip />} />
            <Legend />
            <Line
              type="monotone"
              dataKey="demand"
              name="Demand"
              stroke="#C47D48"
              strokeWidth={2}
              dot={false}
            />
            <Line
              type="monotone"
              dataKey="units_sold"
              name="Units Sold"
              stroke="#6D8799"
              strokeWidth={2}
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      ) : <EmptyChart />}
    </Panel>
  );
}

function RegionPie({ data }) {
  return (
    <Panel
      title="Region-wise Demand Distribution"
      subtitle="Share of total demand across regions"
    >
      {data.length ? (
        <ResponsiveContainer width="100%" height={310}>
          <PieChart>
            <Pie
              data={data}
              dataKey="demand"
              nameKey="name"
              cx="50%"
              cy="48%"
              innerRadius={65}
              outerRadius={105}
              paddingAngle={3}
              label={({ name, percent }) =>
                `${name} ${(percent * 100).toFixed(1)}%`
              }
            >
              {data.map((entry, index) => (
                <Cell
                  key={entry.name}
                  fill={COLORS[index % COLORS.length]}
                />
              ))}
            </Pie>
            <Tooltip formatter={(value) => fmt(value)} />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      ) : <EmptyChart />}
    </Panel>
  );
}

function BarVisual({ title, subtitle, data, dataKey, label }) {
  return (
    <Panel title={title} subtitle={subtitle}>
      {data.length ? (
        <ResponsiveContainer width="100%" height={310}>
          <BarChart data={data} margin={{ bottom: 12 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e7e1d8" />
            <XAxis
              dataKey="name"
              tick={{ fontSize: 10 }}
              interval={0}
              angle={-15}
              textAnchor="end"
              height={65}
            />
            <YAxis />
            <Tooltip content={<ChartTooltip />} />
            <Bar
              dataKey={dataKey}
              name={label}
              fill="#C47D48"
              radius={[5, 5, 0, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      ) : <EmptyChart />}
    </Panel>
  );
}

function MonthlyChart({ data }) {
  return (
    <Panel
      title="Monthly Sales & Demand"
      subtitle="Monthly trends across the selected period"
    >
      {data.length ? (
        <ResponsiveContainer width="100%" height={310}>
          <AreaChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e7e1d8" />
            <XAxis dataKey="month" tick={{ fontSize: 10 }} />
            <YAxis />
            <Tooltip content={<ChartTooltip />} />
            <Legend />
            <Area
              type="monotone"
              dataKey="demand"
              name="Demand"
              stroke="#C47D48"
              fill="#C47D48"
              fillOpacity={0.15}
            />
            <Area
              type="monotone"
              dataKey="units_sold"
              name="Units Sold"
              stroke="#6D8799"
              fill="#6D8799"
              fillOpacity={0.12}
            />
          </AreaChart>
        </ResponsiveContainer>
      ) : <EmptyChart />}
    </Panel>
  );
}

function InventoryChart({ inventory }) {
  const data = inventory.map((row) => ({
    name: row.product_id,
    average_inventory: row.average_inventory,
  }));

  return (
    <BarVisual
      title="Inventory by Product"
      subtitle="Average inventory level for each product"
      data={data}
      dataKey="average_inventory"
      label="Average Inventory"
    />
  );
}

function ControlTower({ overview, demand, sales, inventory, analytics }) {
  return (
    <>
      <div className="siq-metrics">
        <MetricCard
          label="Total Demand"
          value={overview.total_demand}
          note="Total demand units"
        />
        <MetricCard
          label="Units Sold"
          value={overview.total_units_sold}
          note="Total units sold"
        />
        <MetricCard
          label="Average Inventory"
          value={overview.average_inventory}
          note="Average stock level"
        />
        <MetricCard
          label="Total Records"
          value={overview.total_records}
          note="Filtered dataset records"
        />
      </div>

      <div className="siq-chart-grid">
        <RegionPie data={analytics.region_demand || []} />

        <SalesDemandChart
          demand={demand}
          sales={sales}
        />

        <BarVisual
          title="Product-wise Demand"
          subtitle="Demand comparison across products"
          data={analytics.product_demand || []}
          dataKey="demand"
          label="Demand"
        />

        <BarVisual
          title="Category-wise Sales"
          subtitle="Sales contribution by category"
          data={analytics.category_sales || []}
          dataKey="units_sold"
          label="Units Sold"
        />

        <BarVisual
          title="Store-wise Sales"
          subtitle="Sales comparison across stores"
          data={analytics.store_sales || []}
          dataKey="units_sold"
          label="Units Sold"
        />

        <InventoryChart inventory={inventory} />

        <MonthlyChart data={analytics.monthly_trend || []} />

        <BarVisual
          title="Region-wise Sales"
          subtitle="Sales comparison across regions"
          data={analytics.region_sales || []}
          dataKey="units_sold"
          label="Units Sold"
        />
      </div>

      <div className="siq-chart-grid">
        <Panel title="Top 5 Products by Demand">
          <DataTable
            columns={[
              { key: "name", label: "Product" },
              {
                key: "demand",
                label: "Total Demand",
                render: (value) => fmt(value),
              },
            ]}
            rows={analytics.top_products || []}
          />
        </Panel>

        <Panel title="Bottom 5 Products by Demand">
          <DataTable
            columns={[
              { key: "name", label: "Product" },
              {
                key: "demand",
                label: "Total Demand",
                render: (value) => fmt(value),
              },
            ]}
            rows={analytics.bottom_products || []}
          />
        </Panel>
      </div>

      <Panel
        title="Filtered Inventory Report"
        subtitle="Product-level inventory and demand summary"
      >
        <DataTable
          columns={[
            { key: "product_id", label: "Product" },
            { key: "category", label: "Category" },
            {
              key: "average_inventory",
              label: "Average Inventory",
              render: (value) => fmt(value),
            },
            {
              key: "total_demand",
              label: "Total Demand",
              render: (value) => fmt(value),
            },
          ]}
          rows={inventory}
        />
      </Panel>
    </>
  );
}

function InventoryPage({ inventory }) {
  return (
    <>
      <InventoryChart inventory={inventory} />
      <Panel title="Inventory Management">
        <DataTable
          columns={[
            { key: "product_id", label: "Product" },
            { key: "category", label: "Category" },
            {
              key: "average_inventory",
              label: "Average Inventory",
              render: (v) => fmt(v),
            },
            {
              key: "total_demand",
              label: "Total Demand",
              render: (v) => fmt(v),
            },
          ]}
          rows={inventory}
        />
      </Panel>
    </>
  );
}

function DemandPage({ demand }) {
  return (
    <Panel title="Demand Forecast & Analysis">
      {demand.length ? (
        <ResponsiveContainer width="100%" height={380}>
          <AreaChart data={demand}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip content={<ChartTooltip />} />
            <Area
              dataKey="demand"
              name="Demand"
              stroke="#C47D48"
              fill="#C47D48"
              fillOpacity={0.18}
            />
          </AreaChart>
        </ResponsiveContainer>
      ) : <EmptyChart />}
    </Panel>
  );
}

function SalesPage({ sales }) {
  return (
    <Panel title="Sales Analytics">
      {sales.length ? (
        <ResponsiveContainer width="100%" height={380}>
          <LineChart data={sales}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip content={<ChartTooltip />} />
            <Line
              dataKey="units_sold"
              name="Units Sold"
              stroke="#6D8799"
              strokeWidth={2}
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      ) : <EmptyChart />}
    </Panel>
  );
}

function ReplenishmentPage({ inventory }) {
  return (
    <Panel
      title="Replenishment Lab"
      subtitle="Inventory and demand indicators for replenishment review"
    >
      <DataTable
        columns={[
          { key: "product_id", label: "Product" },
          { key: "category", label: "Category" },
          {
            key: "average_inventory",
            label: "Average Inventory",
            render: (v) => fmt(v),
          },
          {
            key: "total_demand",
            label: "Total Demand",
            render: (v) => fmt(v),
          },
        ]}
        rows={inventory}
      />
      <p className="siq-note">
        These are historical inventory indicators, not AI-generated reorder quantities.
      </p>
    </Panel>
  );
}

function ModelInsightsPage() {
  const models = [
    { name: "Naive", mae: "1266.95", rmse: "1862.37", wape: "12.63%" },
    { name: "SARIMAX", mae: "1471.45", rmse: "2162.75", wape: "14.67%" },
    { name: "Prophet", mae: "3083.77", rmse: "3581.31", wape: "30.75%" },
  ];

  return (
    <Panel
      title="Model Insights"
      subtitle="Previously recorded forecasting model evaluation results"
    >
      <div className="siq-model-grid">
        {models.map((model) => (
          <div className="siq-model-card" key={model.name}>
            <h3>{model.name}</h3>
            <div>MAE <strong>{model.mae}</strong></div>
            <div>RMSE <strong>{model.rmse}</strong></div>
            <div>WAPE <strong>{model.wape}</strong></div>
          </div>
        ))}
      </div>
      <p className="siq-note">
        The Naive baseline has the lowest recorded error among these three
        models. These are evaluation results, not live forecast outputs.
      </p>
    </Panel>
  );
}

export default function App() {
  const [page, setPage] = useState("control");
  const [datasetId, setDatasetId] = useState(() => {
    try {
      return window.sessionStorage.getItem("supplyiq.datasetId");
    } catch {
      return null;
    }
  });
  const [datasetMeta, setDatasetMeta] = useState(null);
  const [datasetError, setDatasetError] = useState("");

  const [options, setOptions] = useState({
    product: [],
    category: [],
    store: [],
    region: [],
  });

  const [draft, setDraft] = useState(INITIAL_FILTERS);
  const [applied, setApplied] = useState(INITIAL_FILTERS);

  const [overview, setOverview] = useState({});
  const [demand, setDemand] = useState([]);
  const [sales, setSales] = useState([]);
  const [inventory, setInventory] = useState([]);
  const [analytics, setAnalytics] = useState({});

  const [loading, setLoading] = useState(true);
  const [dashboardLoaded, setDashboardLoaded] = useState(false);
  const [error, setError] = useState("");
  const [filterError, setFilterError] = useState("");

  useEffect(() => {
    let active = true;

    if (!datasetId) {
      return () => {
        active = false;
      };
    }

    getDataset(datasetId)
      .then(({ data }) => {
        if (active) {
          setDatasetMeta(data);
          setDatasetError("");
        }
      })
      .catch((err) => {
        if (!active) return;
        if (err.response?.status === 404) {
          setDatasetId(null);
          try {
            window.sessionStorage.removeItem("supplyiq.datasetId");
          } catch {
            setDatasetError(
              "The uploaded dataset session has expired; using the historical dataset."
            );
          }
          setDatasetError(
            "The uploaded dataset session has expired; using the historical dataset."
          );
          setDatasetMeta(null);
        } else {
          setDatasetError(
            err.response?.data?.detail ||
            "Unable to load the selected dataset."
          );
        }
      });

    return () => {
      active = false;
    };
  }, [datasetId]);

  useEffect(() => {
    let active = true;

    getFilters(datasetId)
      .then(({ data }) => {
        if (!active) return;

        setFilterError("");
        setOptions({
          product: data.products || [],
          category: data.categories || [],
          store: data.stores || [],
          region: data.regions || [],
        });
      })
      .catch((err) => {
        if (active) {
          setFilterError(
            err.response?.data?.detail ||
            "Unable to load filter options. Check the backend."
          );
        }
      });

    return () => {
      active = false;
    };
  }, [datasetId]);

  useEffect(() => {
    let active = true;

    async function loadDashboard() {
      setLoading(true);
      setError("");

      try {
        const results = await Promise.allSettled([
          getOverview(applied, datasetId),
          getDemand(applied, datasetId),
          getSales(applied, datasetId),
          getInventory(applied, datasetId),
          getAnalytics(applied, datasetId),
        ]);

        if (!active) return;

        const setters = [
          setOverview,
          setDemand,
          setSales,
          setInventory,
          setAnalytics,
        ];
        const labels = [
          "Overview",
          "Demand",
          "Sales",
          "Inventory",
          "Analytics",
        ];
        const failures = [];
        let uploadedDatasetExpired = false;

        results.forEach((result, index) => {
          if (result.status === "fulfilled") {
            setters[index](result.value.data || (
              index === 0 || index === 4 ? {} : []
            ));
          } else {
            setters[index](index === 0 || index === 4 ? {} : []);
            const detail = result.reason?.response?.data?.detail;
            if (
              datasetId &&
              result.reason?.response?.status === 404 &&
              String(detail).includes("Uploaded dataset not found")
            ) {
              uploadedDatasetExpired = true;
            }
            failures.push(
              `${labels[index]}: ${
                typeof detail === "string"
                  ? detail
                  : result.reason?.message || "Request failed."
              }`
            );
          }
        });

        if (uploadedDatasetExpired) {
          setDatasetId(null);
          setDatasetMeta(null);
          setDatasetError(
            "The uploaded dataset session has expired; using the historical dataset."
          );
          try {
            window.sessionStorage.removeItem("supplyiq.datasetId");
          } catch {
            setDatasetError(
              "The uploaded dataset session expired, and its selection could not be cleared from this browser session."
            );
          }
        }

        setError(failures.join(" "));
        setDashboardLoaded(true);
      } catch (err) {
        if (active) {
          setError(
            err.response?.data?.detail ||
            "Unable to load dashboard data. Check that the backend is running."
          );
          setDashboardLoaded(true);
        }
      } finally {
        if (active) setLoading(false);
      }
    }

    loadDashboard();

    return () => {
      active = false;
    };
  }, [applied, datasetId]);

  const applyFilters = () => {
    setApplied({ ...draft });
  };

  const resetFilters = () => {
    setDraft(INITIAL_FILTERS);
    setApplied(INITIAL_FILTERS);
  };

  const changeDataset = (nextId, metadata = null) => {
    const selectedId = nextId || null;
    setDatasetId(selectedId);
    setDatasetMeta(metadata);
    setDraft(INITIAL_FILTERS);
    setApplied(INITIAL_FILTERS);
    setDatasetError("");
    try {
      if (selectedId) {
        window.sessionStorage.setItem("supplyiq.datasetId", selectedId);
      } else {
        window.sessionStorage.removeItem("supplyiq.datasetId");
      }
    } catch {
      setDatasetError(
        "Dataset selection is active, but could not be saved for this browser session."
      );
    }
  };

  const title =
    NAV_ITEMS.find(([id]) => id === page)?.[1] || "Control Tower";

  let content;

  if (page === "control") {
  content = (
    <ControlTower
      overview={overview}
      demand={demand}
      sales={sales}
      inventory={inventory}
      analytics={analytics}
    />
  );
} else if (page === "inventory") {
  content = <InventoryPage inventory={inventory} />;
} else if (page === "demand") {
  content = <DemandPage demand={demand} />;
} else if (page === "sales") {
  content = <SalesPage sales={sales} />;
} else if (page === "replenishment") {
  content = <ReplenishmentPage inventory={inventory} />;
} else if (page === "models") {
  content = <ModelInsightsPage />;
} else if (page === "ai") {
  content = (
    <AIIntelligence
      filters={applied}
      datasetId={datasetId}
      datasetMeta={datasetMeta}
      onDatasetChange={changeDataset}
      onDatasetUploaded={changeDataset}
    />
  );
}
  return (
    <div className="siq-app">
      <aside className="siq-sidebar">
        <div className="siq-brand">
          <div className="siq-brand-icon">S</div>
          <div>
            <h2>SupplyIQ</h2>
            <span>Supply Chain Intelligence</span>
          </div>
        </div>

        <div className="siq-nav-heading">WORKSPACE</div>

        <nav className="siq-nav">
          {NAV_ITEMS.map(([id, label]) => (
            <button
              key={id}
              className={page === id ? "active" : ""}
              onClick={() => setPage(id)}
            >
              {label}
            </button>
          ))}
        </nav>

        <div className="siq-backend-status">
          <span />
          Backend connection
        </div>
      </aside>

      <main className="siq-main">
        <header className="siq-header">
          <div>
            <span className="siq-eyebrow">SUPPLY CHAIN DASHBOARD</span>
            <h1>{title}</h1>
          </div>
          <span className="siq-dataset">
            {datasetMeta?.name || "Historical Dataset · 2022–2024"}
          </span>
        </header>

        <div className="siq-content">
          <FiltersPanel
            draft={draft}
            setDraft={setDraft}
            options={options}
            onApply={applyFilters}
            onReset={resetFilters}
            loading={loading}
          />

          {(datasetError || filterError || error) && (
            <div className="siq-error">
              {[datasetError, filterError, error].filter(Boolean).join(" ")}
            </div>
          )}

          {loading && !dashboardLoaded ? (
            <div className="siq-loading">Loading dashboard data...</div>
          ) : (
            <div className="siq-results">{content}</div>
          )}
        </div>
      </main>

      <style>{`
        .siq-app {
        --navy:#17283F;
        --copper:#C47D48;
        --ivory:#F8F6F1;
        min-height:100vh;
        display:flex;

  background-color:var(--ivory);
  background-image:
    linear-gradient(rgba(248,246,241,0.72), rgba(248,246,241,0.72)),
    url("${heroImage}");

  background-size:cover;
  background-position:center;
  background-repeat:no-repeat;
  background-attachment:fixed;

  color:#24364a;
  font-family:Inter,Arial,sans-serif;
}
        .siq-sidebar {
          width:245px;
          flex-shrink:0;
          min-height:100vh;
          padding:26px 16px;
          background:var(--navy);
          color:white;
          display:flex;
          flex-direction:column;
        }
        .siq-brand {display:flex;gap:12px;align-items:center;padding:0 8px 38px}
        .siq-brand-icon {
          width:40px;height:40px;border-radius:10px;
          display:grid;place-items:center;background:var(--copper);
          font-size:22px;font-weight:800;
        }
        .siq-brand h2 {margin:0;font-size:20px}
        .siq-brand span {color:#c0cbd5;font-size:11px}
        .siq-nav-heading {font-size:10px;letter-spacing:1.5px;color:#9cabb9;padding:0 10px 12px}
        .siq-nav {display:grid;gap:7px}
        .siq-nav button {
          text-align:left;border:0;background:transparent;color:#d5dce3;
          border-radius:8px;padding:13px 12px;cursor:pointer;font-size:13px
        }
        .siq-nav button:hover,.siq-nav button.active {background:#31465d;color:white}
        .siq-nav button.active {border-left:3px solid var(--copper)}
        .siq-backend-status {margin-top:auto;padding:20px 8px 0;color:#c0cbd5;font-size:11px;display:flex;gap:9px;align-items:center}
        .siq-backend-status span {width:8px;height:8px;background:#65b88a;border-radius:50%}
        .siq-main {flex:1;min-width:0}
        .siq-header {
          padding:25px 34px 20px;background:white;border-bottom:1px solid #e9e4dc;
          display:flex;justify-content:space-between;align-items:center;gap:15px
        }
        .siq-eyebrow {color:var(--copper);font-size:10px;font-weight:800;letter-spacing:1.5px}
        .siq-header h1 {margin:6px 0 0;color:var(--navy);font-size:25px}
        .siq-dataset {font-size:12px;color:#788493}
        .siq-content {padding:25px 34px 45px;max-width:1700px;margin:auto}
        .siq-filter-panel,.siq-panel {
          background:white;border:1px solid #e9e4dc;border-radius:12px;
          padding:21px;margin-bottom:22px;box-shadow:0 3px 14px #17283f08
        }
        .siq-panel-heading {display:flex;justify-content:space-between;align-items:center;gap:12px;margin-bottom:17px}
        .siq-panel-heading h2 {margin:0;color:var(--navy);font-size:16px}
        .siq-panel-heading p {margin:5px 0 0;color:#84909b;font-size:12px}
        .siq-filter-hint {color:#8a929a;font-size:11px}
        .siq-filter-grid {display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:15px}
        .siq-filter {position:relative;min-width:0}
        .siq-filter-label {display:block;font-size:12px;font-weight:700;margin-bottom:7px;color:#425267}
        .siq-dropdown-button {
          width:100%;display:flex;justify-content:space-between;align-items:center;
          padding:11px 12px;border:1px solid #d9dfe4;border-radius:7px;
          background:white;color:#34465a;font-size:12px;text-align:left;cursor:pointer
        }
        .siq-dropdown-button:hover,.siq-dropdown-button.is-open {border-color:var(--copper)}
        .siq-chevron {font-size:18px;color:#8b9299}
        .siq-dropdown-menu {
          position:absolute;z-index:20;top:68px;left:0;width:100%;min-width:220px;
          background:white;border:1px solid #ddd;border-radius:9px;
          box-shadow:0 12px 28px #17283f20;padding:10px
        }
        .siq-dropdown-top {display:flex;justify-content:space-between;padding:6px 5px 10px;font-size:12px}
        .siq-dropdown-top span {color:#84909b}
        .siq-check-option {display:flex;align-items:center;gap:9px;padding:8px 6px;font-size:12px;cursor:pointer;border-radius:5px}
        .siq-check-option:hover {background:#f5f2ed}
        .siq-check-option input {width:15px;height:15px;accent-color:var(--copper);cursor:pointer}
        .siq-select-all {border-bottom:1px solid #eee;border-radius:0;font-weight:700}
        .siq-option-list {max-height:190px;overflow-y:auto;padding-top:5px}
        .siq-dropdown-footer {border-top:1px solid #eee;margin-top:7px;padding-top:8px;display:flex;justify-content:space-between;gap:5px}
        .siq-dropdown-footer button {border:0;background:transparent;color:#52677a;font-size:11px;cursor:pointer;padding:5px}
        .siq-dropdown-footer button:last-child {color:var(--copper);font-weight:700}
        .siq-filter-actions {display:flex;gap:10px;margin-top:19px}
        .siq-apply-button,.siq-reset-button {border-radius:6px;padding:10px 19px;font-size:12px;font-weight:700;cursor:pointer}
        .siq-apply-button {border:1px solid var(--navy);background:var(--navy);color:white}
        .siq-apply-button:disabled {opacity:.6;cursor:wait}
        .siq-reset-button {border:1px solid #d8dfe5;background:white;color:#536477}
        .siq-metrics {display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:15px;margin-bottom:22px}
        .siq-metric-card {background:white;border:1px solid #e9e4dc;border-radius:10px;padding:19px;display:flex;flex-direction:column;gap:9px}
        .siq-metric-label {color:#718091;font-size:12px}
        .siq-metric-card strong {color:var(--navy);font-size:25px}
        .siq-metric-card small {color:#929ba4;font-size:10px}
        .siq-chart-grid {display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}
        .siq-chart-grid .siq-panel {min-width:0}
        .siq-empty,.siq-loading {min-height:180px;display:grid;place-items:center;color:#8b949d;font-size:13px}
        .siq-table-wrap {width:100%;overflow-x:auto}
        .siq-table {width:100%;border-collapse:collapse;font-size:12px}
        .siq-table th {text-align:left;background:#f5f2ed;color:#526174;padding:12px;white-space:nowrap}
        .siq-table td {padding:12px;border-bottom:1px solid #eee9e2;color:#46566a}
        .siq-table tr:hover td {background:#fbfaf8}
        .siq-tooltip {background:white;border:1px solid #ddd;border-radius:7px;padding:10px;font-size:12px;box-shadow:0 4px 12px #0001}
        .siq-model-grid {display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:15px}
        .siq-model-card {padding:18px;border:1px solid #e8e3db;border-radius:9px;display:grid;gap:12px;font-size:12px}
        .siq-model-card h3 {margin:0;color:var(--navy);font-size:16px}
        .siq-model-card div {display:flex;justify-content:space-between;color:#718091}
        .siq-model-card strong {color:#263b50}
        .siq-note {color:#7e8993;font-size:11px;line-height:1.6;margin-top:16px}
        .siq-error {padding:13px;background:#fff0ed;color:#9d4038;border-radius:8px;margin-bottom:18px;font-size:13px}
        @media(max-width:1000px) {
          .siq-sidebar {width:195px}
          .siq-filter-grid {grid-template-columns:repeat(2,minmax(0,1fr))}
          .siq-metrics {grid-template-columns:repeat(2,minmax(0,1fr))}
        }
        @media(max-width:700px) {
          .siq-app {display:block}
          .siq-sidebar {width:auto;min-height:auto;padding:15px}
          .siq-brand {padding-bottom:15px}
          .siq-nav {display:flex;overflow-x:auto}
          .siq-nav button {white-space:nowrap}
          .siq-backend-status,.siq-nav-heading {display:none}
          .siq-header {padding:20px}
          .siq-content {padding:16px}
          .siq-chart-grid,.siq-model-grid {grid-template-columns:1fr}
          .siq-filter-grid {grid-template-columns:1fr 1fr}
          .siq-dataset {display:none}
        }
        @media(max-width:420px) {
          .siq-filter-grid {grid-template-columns:1fr}
          .siq-metrics {grid-template-columns:1fr 1fr}
          .siq-metric-card strong {font-size:19px}
        }
      `}</style>
    </div>
  );
}
