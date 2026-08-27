import { useMemo } from "react";
import {
  FiAlertTriangle,
  FiLock,
  FiRefreshCw,
  FiShield,
  FiSlash,
} from "react-icons/fi";
import KPICard from "../components/KPICard";
import ThreatTable from "../components/ThreatTable";
import LoadingSpinner from "../components/LoadingSpinner";
import EmptyState from "../components/EmptyState";
import LiveThreatFeed from "../components/LiveThreatFeed";
import ActionBadge from "../components/ActionBadge";
import RiskBadge from "../components/RiskBadge";
import RiskGauge from "../components/RiskGauge";
import { ActionChart, RiskChart } from "../components/Charts";
import { useHistory } from "../hooks/useHistory";
import { formatDateTime } from "../utils/formatters";

export default function Overview() {
  const { history, total, loading, error, mongoDown, refresh } = useHistory({
    limit: 100,
    skip: 0,
  });

  const stats = useMemo(() => {
    const blocked = history.filter((h) => h.decision?.action === "BLOCK_IP").length;
    const isolated = history.filter((h) => h.decision?.action === "ISOLATE_HOST").length;
    const critical = history.filter((h) => h.risk?.risk_level === "CRITICAL").length;
    const highRisk = history.filter((h) => h.risk?.risk_level === "HIGH").length;
    const attacksDetected = history.filter(
      (h) => (h.prediction?.attack || "BENIGN") !== "BENIGN"
    ).length;
    const latestHighRisk = history.find((h) =>
      ["HIGH", "CRITICAL"].includes(h.risk?.risk_level)
    );

    return {
      blocked,
      isolated,
      critical,
      highRisk,
      attacksDetected,
      latestHighRisk,
    };
  }, [history]);

  return (
    <div>
      <div className="page-header">
        <div>
          <h2>SOC Overview</h2>
          <p>Key detections, risk posture, and recent response actions.</p>
        </div>
        <div className="page-actions">
          <button type="button" className="btn btn-secondary" onClick={refresh}>
            <FiRefreshCw /> Refresh
          </button>
        </div>
      </div>

      {mongoDown && (
        <div className="alert alert-warning">
          MongoDB is unavailable. History widgets may be empty until the database is online.
        </div>
      )}
      {error && !mongoDown && <div className="alert alert-error">{error}</div>}

      <div className="grid grid-4" style={{ marginBottom: "1rem" }}>
        <KPICard
          icon={<FiShield />}
          label="Analyses"
          value={total}
          description="Stored pipeline runs"
          accent="#3B82F6"
        />
        <KPICard
          icon={<FiAlertTriangle />}
          label="Attacks Detected"
          value={stats.attacksDetected}
          description="Non-BENIGN classifications"
          accent="#EF4444"
        />
        <KPICard
          icon={<FiSlash />}
          label="Blocked IPs"
          value={stats.blocked}
          description="BLOCK_IP decisions"
          accent="#F97316"
        />
        <KPICard
          icon={<FiLock />}
          label="Isolated Hosts"
          value={stats.isolated}
          description="ISOLATE_HOST decisions"
          accent="#8B5CF6"
        />
      </div>

      {loading ? (
        <LoadingSpinner label="Loading dashboard…" />
      ) : history.length === 0 ? (
        <EmptyState
          title="No analyses available."
          message="Run Live Analyze → Demo Attack to populate the SOC dashboard."
        />
      ) : (
        <>
          <div className="overview-split">
            <div className="card overview-split-card">
              <h3 className="card-title">Live Threat Feed</h3>
              <LiveThreatFeed rows={history} maxItems={6} />
            </div>
            <div className="card overview-split-card">
              <h3 className="card-title">Current Risk Posture</h3>
              {stats.latestHighRisk ? (
                <div className="risk-posture">
                  <RiskGauge
                    score={stats.latestHighRisk.risk?.risk_score}
                    level={stats.latestHighRisk.risk?.risk_level}
                    size="lg"
                  />
                  <div className="risk-posture-facts">
                    <div className="stat-row">
                      <span>IP</span>
                      <strong className="mono">{stats.latestHighRisk.ip_address || "—"}</strong>
                    </div>
                    <div className="stat-row">
                      <span>Attack</span>
                      <strong>{stats.latestHighRisk.prediction?.attack || "—"}</strong>
                    </div>
                    <div className="stat-row">
                      <span>Level</span>
                      <RiskBadge level={stats.latestHighRisk.risk?.risk_level} />
                    </div>
                    <div className="stat-row">
                      <span>Action</span>
                      <ActionBadge action={stats.latestHighRisk.decision?.action} />
                    </div>
                    <div className="stat-row">
                      <span>Seen</span>
                      <strong>{formatDateTime(stats.latestHighRisk.timestamp)}</strong>
                    </div>
                  </div>
                </div>
              ) : (
                <p className="heatmap-empty">
                  No HIGH/CRITICAL events yet. High risk: {stats.highRisk} · Critical:{" "}
                  {stats.critical}
                </p>
              )}
            </div>
          </div>

          <div className="grid grid-2" style={{ marginBottom: "1rem" }}>
            <div className="card">
              <h3 className="card-title">Risk Distribution</h3>
              <RiskChart history={history} />
            </div>
            <div className="card">
              <h3 className="card-title">Response Actions</h3>
              <ActionChart history={history} />
            </div>
          </div>

          <div className="card">
            <h3 className="card-title">Recent Analyses</h3>
            <ThreatTable rows={history.slice(0, 10)} />
          </div>
        </>
      )}
    </div>
  );
}
