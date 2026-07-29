import client from "./client";

export async function fetchHistory({ limit = 50, skip = 0 } = {}) {
  const { data } = await client.get("/history", {
    params: { limit, skip },
  });
  return data;
}

export async function fetchHistoryItem(id) {
  const { data } = await client.get(`/history/${id}`);
  return data;
}
