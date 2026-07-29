import client from "./client";

export async function fetchModelInfo() {
  const { data } = await client.get("/model-info");
  return data;
}

export async function fetchModelPerformance() {
  const { data } = await client.get("/model-performance");
  return data;
}

export async function fetchFeatureImportance() {
  const { data } = await client.get("/feature-importance");
  return data;
}

export async function fetchMetrics() {
  const { data } = await client.get("/metrics");
  return data;
}
