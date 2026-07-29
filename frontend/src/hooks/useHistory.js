import { useCallback, useEffect, useState } from "react";
import { fetchHistory } from "../api/history";
import { getApiErrorMessage } from "../api/client";

export function useHistory({ limit = 100, skip = 0, auto = true } = {}) {
  const [history, setHistory] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(auto);
  const [error, setError] = useState(null);
  const [mongoDown, setMongoDown] = useState(false);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    setMongoDown(false);
    try {
      const data = await fetchHistory({ limit, skip });
      setHistory(Array.isArray(data.history) ? data.history : []);
      setTotal(data.total ?? 0);
    } catch (err) {
      const status = err.response?.status;
      const message = getApiErrorMessage(err, "Failed to load history.");
      setHistory([]);
      setTotal(0);
      setError(message);
      setMongoDown(status === 503 || /mongodb/i.test(message));
    } finally {
      setLoading(false);
    }
  }, [limit, skip]);

  useEffect(() => {
    if (auto) refresh();
  }, [auto, refresh]);

  return {
    history,
    total,
    loading,
    error,
    mongoDown,
    refresh,
  };
}
