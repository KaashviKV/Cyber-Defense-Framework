import client from "./client";

export async function analyzeTraffic({ ip_address, features }) {
  const { data } = await client.post("/analyze", {
    ip_address,
    features,
  });
  return data;
}
