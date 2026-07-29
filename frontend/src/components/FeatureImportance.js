import { useEffect, useState } from "react";
import { fetchFeatureImportance } from "../api/model";
import LoadingSpinner from "./LoadingSpinner";

const FALLBACK_FEATURES = [
  { feature: "Flow Duration", importance: 12.4 },
  { feature: "Packet Length Mean", importance: 9.8 },
  { feature: "Fwd Packet Length Mean", importance: 8.6 },
  { feature: "Idle Mean", importance: 7.2 },
  { feature: "Active Mean", importance: 6.5 },
];

export default function FeatureImportance({ topN = 5 }) {
  const [features, setFeatures] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;

    async function load() {
      setLoading(true);
      setError("");
      try {
        const data = await fetchFeatureImportance();
        if (!active) return;
        if (data.status === "success" && Array.isArray(data.top_features)) {
          setFeatures(data.top_features.slice(0, topN));
        } else {
          setFeatures(FALLBACK_FEATURES.slice(0, topN));
          setError(data.message || "Using fallback feature importance.");
        }
      } catch {
        if (active) {
          setFeatures(FALLBACK_FEATURES.slice(0, topN));
          setError("Could not load feature importance from API.");
        }
      } finally {
        if (active) setLoading(false);
      }
    }

    load();
    return () => {
      active = false;
    };
  }, [topN]);

  if (loading) return <LoadingSpinner label="Loading feature importance…" small />;

  const max = Math.max(...features.map((item) => item.importance), 1);

  return (
    <div className="feature-importance">
      {error && <div className="alert alert-info" style={{ marginBottom: "0.75rem" }}>{error}</div>}
      {features.map((item, index) => (
        <div key={item.feature} className="feature-row">
          <div className="feature-row-head">
            <span>#{index + 1}</span>
            <strong>{item.feature}</strong>
            <span>{item.importance}%</span>
          </div>
          <div className="feature-bar">
            <div className="feature-bar-fill" style={{ width: `${(item.importance / max) * 100}%` }} />
          </div>
        </div>
      ))}
    </div>
  );
}
