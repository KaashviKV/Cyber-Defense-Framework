import { useCallback, useEffect, useState } from "react";
import { checkHealth } from "../api/health";

export function useHealth(pollMs = 30000) {
  const [online, setOnline] = useState(null);
  const [service, setService] = useState("");
  const [checking, setChecking] = useState(true);

  const refresh = useCallback(async () => {
    setChecking(true);
    try {
      const data = await checkHealth();
      setOnline(data?.status === "ok");
      setService(data?.service || "API");
    } catch {
      setOnline(false);
      setService("");
    } finally {
      setChecking(false);
    }
  }, []);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, pollMs);
    return () => clearInterval(id);
  }, [pollMs, refresh]);

  return { online, service, checking, refresh };
}
