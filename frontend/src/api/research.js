import client from "./client";

export async function fetchExperiments() {
  const { data } = await client.get("/experiments");
  return data;
}

export async function fetchSimulation() {
  const { data } = await client.get("/simulation");
  return data;
}

export async function submitAnalysisFeedback(id, payload) {
  const { data } = await client.post(`/history/${id}/feedback`, payload);
  return data;
}

export async function fetchIncidents({ limit = 50, skip = 0 } = {}) {
  const { data } = await client.get("/incidents", { params: { limit, skip } });
  return data;
}

export async function fetchIncident(id) {
  const { data } = await client.get(`/incidents/${id}`);
  return data;
}

export async function fetchLiveEvents() {
  const { data } = await client.get("/stream/latest");
  return data;
}

export async function fetchHealth() {
  const { data } = await client.get("/health");
  return data;
}
