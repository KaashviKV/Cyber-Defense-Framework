import client from "./client";

export async function checkHealth() {
  const { data } = await client.get("/health");
  return data;
}
