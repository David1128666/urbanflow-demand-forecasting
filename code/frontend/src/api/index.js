import axios from "axios";

const api = axios.create({
  baseURL: "/",
  timeout: 5000,
  headers: {
    "Content-Type": "application/json",
  },
});

export async function getHealth() {
  const response = await api.get("/health");
  return response.data;
}

function unwrap(response) {
  const payload = response.data;
  if (payload.code !== 200) {
    throw new Error(payload.message || "Request failed");
  }
  return payload.data;
}

export async function getDashboardSummary() {
  return unwrap(await api.get("/api/v1/dashboard/summary"));
}

export async function getStations(params = {}) {
  return unwrap(await api.get("/api/v1/stations", { params }));
}

export async function getDemandHistory(params) {
  return unwrap(await api.get("/api/v1/demand/history", { params }));
}

export async function getLatestForecasts(params = {}) {
  return unwrap(await api.get("/api/v1/forecasts/latest", { params }));
}

export async function getModelMetrics(params = {}) {
  return unwrap(await api.get("/api/v1/models/metrics", { params }));
}

export async function getLatestInventory(params = {}) {
  return unwrap(await api.get("/api/v1/inventory/latest", { params }));
}

export async function getDispatchSummary() {
  return unwrap(await api.get("/api/v1/dispatch/summary"));
}

export async function getDispatchRecommendations(params = {}) {
  return unwrap(await api.get("/api/v1/dispatch/recommendations", { params }));
}

export default api;
