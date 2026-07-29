import { useEffect, useState } from "react";
import { fetchModelInfo, fetchModelPerformance, fetchMetrics } from "../api/model";
import LoadingSpinner from "../components/LoadingSpinner";
import { ATTACK_CLASSES, ACTIONS, FEATURE_COUNT } from "../utils/constants";
import { formatNumber, formatPercent } from "../utils/formatters";

export default function ProjectStats() {
  const [loading, setLoading] = useState(true);
  const [modelInfo, setModelInfo] = useState(null);
  const [performance, setPerformance] = useState(null);
  const [metrics, setMetrics] = useState(null);

  useEffect(() => {
    let active = true;
    async function load() {
      setLoading(true);
      try {
        const [info, perf, met] = await Promise.allSettled([
          fetchModelInfo(),
          fetchModelPerformance(),
          fetchMetrics(),
        ]);
        if (!active) return;
        if (info.status === "fulfilled") setModelInfo(info.value);
        if (perf.status === "fulfilled") setPerformance(perf.value);
        if (met.status === "fulfilled") setMetrics(met.value);
      } finally {
        if (active) setLoading(false);
      }
    }
    load();
    return () => {
      active = false;
    };
  }, []);

  if (loading) return <LoadingSpinner label="Loading project statistics…" />;

  const accuracy = performance?.metrics?.accuracy ?? performance?.accuracy;
  const accuracyDisplay =
    accuracy == null
      ? "—"
      : formatPercent(Number(accuracy) <= 1 ? Number(accuracy) * 100 : Number(accuracy));

  return (
    <div>
      <div className="page-header">
        <div>
          <h2>Project Statistics</h2>
          <p>Reference metrics for examiners and technical demonstrations.</p>
        </div>
      </div>

      <div className="grid grid-3">
        <div className="card stat-card">
          <span>Random Forest Accuracy</span>
          <strong>{accuracyDisplay}</strong>
        </div>
        <div className="card stat-card">
          <span>Attack Classes</span>
          <strong>{ATTACK_CLASSES.length}</strong>
        </div>
        <div className="card stat-card">
          <span>Input Features</span>
          <strong>{FEATURE_COUNT}</strong>
        </div>
        <div className="card stat-card">
          <span>RL Actions</span>
          <strong>{ACTIONS.length}</strong>
        </div>
        <div className="card stat-card">
          <span>CTI Sources</span>
          <strong>2 (VirusTotal, AbuseIPDB)</strong>
        </div>
        <div className="card stat-card">
          <span>Stack</span>
          <strong>MongoDB · Flask · React</strong>
        </div>
      </div>

      <div className="grid grid-2" style={{ marginTop: "1rem" }}>
        <div className="card">
          <h3 className="card-title">Model Info</h3>
          <pre className="json-viewer" style={{ maxHeight: 280 }}>
            {JSON.stringify(modelInfo || { message: "Unavailable" }, null, 2)}
          </pre>
        </div>
        <div className="card">
          <h3 className="card-title">Aggregated Metrics</h3>
          <pre className="json-viewer" style={{ maxHeight: 280 }}>
            {JSON.stringify(metrics || { message: "Unavailable" }, null, 2)}
          </pre>
        </div>
      </div>

      {performance?.metrics && (
        <div className="card" style={{ marginTop: "1rem" }}>
          <h3 className="card-title">Model Performance</h3>
          <div className="grid grid-4">
            {Object.entries(performance.metrics).map(([key, value]) => (
              <div key={key} className="stat-card flat">
                <span>{key}</span>
                <strong>{formatNumber(Number(value) * (Number(value) <= 1 ? 100 : 1), 2)}%</strong>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
