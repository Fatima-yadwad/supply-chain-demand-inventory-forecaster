
import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:8000",
  timeout: 30000,
});

export const filterParams = (filters = {}, datasetId = null) => {
  const queryValue = (selection) => {
    if (selection === undefined || selection === null) {
      return "All";
    }

    const values = Array.isArray(selection) ? selection : [selection];
    if (values.length === 0) {
      return "__NONE__";
    }

    const normalized = values
      .map((value) => String(value).trim())
      .filter(Boolean);

    if (normalized.length === 0) {
      return "__NONE__";
    }

    return normalized.includes("All") ? "All" : normalized.join(",");
  };

  const params = {
    product: queryValue(filters.product),
    category: queryValue(filters.category),
    store: queryValue(filters.store),
    region: queryValue(filters.region),
  };

  if (datasetId) {
    params.dataset_id = datasetId;
  }

  return params;
};

const filterConfig = (filters, datasetId) => ({
  params: filterParams(filters, datasetId),
});

export const getOverview = (filters, datasetId) =>
  api.get("/api/overview", filterConfig(filters, datasetId));

export const getDemand = (filters, datasetId) =>
  api.get("/api/demand", filterConfig(filters, datasetId));

export const getSales = (filters, datasetId) =>
  api.get("/api/sales", filterConfig(filters, datasetId));

export const getInventory = (filters, datasetId) =>
  api.get("/api/inventory", filterConfig(filters, datasetId));

export const getAnalytics = (filters, datasetId) =>
  api.get("/api/analytics", filterConfig(filters, datasetId));

export const getFilters = (datasetId) =>
  api.get("/api/filters", {
    params: datasetId ? { dataset_id: datasetId } : {},
  });

export const getDataset = (datasetId) =>
  api.get(`/api/datasets/${encodeURIComponent(datasetId)}`);

export const uploadDataset = (file) => {
  const form = new FormData();
  form.append("file", file);
  return api.post("/api/datasets/upload", form);
};

export const getAIReport = (period, filters, datasetId) =>
  api.get(`/api/ai/reports/${period}`, {
    params: filterParams(filters, datasetId),
  });

export const getHealth = () => api.get("/api/health");

export default api;
